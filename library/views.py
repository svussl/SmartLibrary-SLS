from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Q
from django.utils import timezone
from .models import Book, SearchLog, Transaction, StudentProfile
from .ai_engine import SmartLibraryAI
from .forms import UserRegistrationForm, StudentLoginForm
from django.db import transaction

# ==========================================
# دالة مساعدة لفحص الصلاحيات (Admin Check)
# ==========================================
def is_admin(user):
    return user.is_superuser

# ==========================================
# 1. نظام المصادقة (Authentication)
# ==========================================

def register(request):
    if request.user.is_authenticated:
        return redirect('library:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            StudentProfile.objects.create(
                user=user,
                student_id=form.cleaned_data['student_id'],
                major=form.cleaned_data['major']
            )
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"مرحباً بك {user.first_name}! تم إنشاء حسابك بنجاح.")
            return redirect('library:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'library/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('library:home')

    if request.method == 'POST':
        # استخدام StudentLoginForm بدلاً من الفورم الافتراضي
        form = StudentLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"أهلاً بعودتك، {user.first_name}!")
            return redirect('library:home')
        else:
            messages.error(request, "الرقم الجامعي أو كلمة المرور غير صحيحة.")
    else:
        form = StudentLoginForm()
    
    return render(request, 'library/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "تم تسجيل الخروج بنجاح.")
    return redirect('library:login')

# ==========================================
# 2. الوظائف الرئيسية (Core Features)
# ==========================================

@login_required
def home(request):
    """الصفحة الرئيسية: تعرض توصيات ذكية بناءً على التخصص أو التاريخ"""
    books = []
    
    if hasattr(request.user, 'studentprofile'):
        profile = request.user.studentprofile
        ai_engine = SmartLibraryAI()

        last_loan = Transaction.objects.filter(student=profile).last()
        
        if last_loan:
            books = ai_engine.get_recommendations(last_loan.book.id, top_k=8)
        
        if not books:
            major_text = profile.get_major_display()
            if major_text != 'General':
                books = ai_engine.recommend_by_profile(major_text, top_k=8)

    if not books:
        books = Book.objects.all().order_by('-created_at')[:8]

    return render(request, 'library/home.html', {'books': books})

@login_required
def search_view(request):
    """
    واجهة البحث الدلالي مع دعم خيارات الترتيب (Sorting) والفلترة (Filtering)
    """
    query = request.GET.get('q', '')
    sort_option = request.GET.get('sort', 'relevance')
    
    # استقبال خيارات الفلترة (القائمة المختارة)
    # إذا لم يختر المستخدم شيئاً (أول زيارة)، نفترض أنه يريد الكتب المطبوعة
    selected_types = request.GET.getlist('book_type')
    if not request.GET and not selected_types:
        selected_types = ['printed'] # الافتراضي

    books = []
    
    if query:
        ai_engine = SmartLibraryAI()
        # 1. البحث الدلالي باستخدام AI
        books = ai_engine.semantic_search(query)
        
        # 2. تطبيق فلتر نوع المصدر (Source Type Filter)
        # ملاحظة: بما أن قاعدة البيانات الحالية لا تحوي حقل is_ebook
        # سنعتبر أن جميع الكتب الحالية هي "كتب مطبوعة" (Printed)
        filtered_books = []
        if books:
            for book in books:
                # منطق الفلترة:
                # إذا اختار المستخدم "printed" -> نعرض الكتب (لأنها كلها مطبوعة حالياً)
                # إذا اختار المستخدم "ebook" فقط -> لن نعرض شيئاً (لأنه لا يوجد حقل ebook)
                # يمكنك مستقبلاً إضافة حقل book.is_ebook في المودل وتعديل الشرط هنا
                
                is_printed_book = True # فرضية حالية
                is_ebook_book = False  # فرضية حالية

                if 'printed' in selected_types and is_printed_book:
                    filtered_books.append(book)
                elif 'ebook' in selected_types and is_ebook_book:
                    filtered_books.append(book)
            
            books = filtered_books

        # 3. منطق الترتيب (Sorting Logic)
        if books:
            if sort_option == 'newest':
                books.sort(key=lambda x: x.created_at, reverse=True)
            elif sort_option == 'popular':
                books.sort(key=lambda x: x.transaction_set.count(), reverse=True)

        # 4. تسجيل عملية البحث (نتأكد أنها عملية بحث وليست مجرد تغيير فلتر)
        user = request.user if request.user.is_authenticated else None
        if 'sort' not in request.GET and 'book_type' not in request.GET:
            SearchLog.objects.create(user=user, query_text=query, result_count=len(books))

    context = {
        'books': books, 
        'query': query,
        'current_sort': sort_option,
        'selected_types': selected_types, # لإعادة تحديد المربعات في الواجهة
    }
    return render(request, 'library/search.html', context)


@login_required
def book_detail(request, book_id):
    """صفحة تفاصيل الكتاب مع التوصيات المشابهة"""
    book = get_object_or_404(Book, id=book_id)
    
    ai_engine = SmartLibraryAI()
    similar_titles = ai_engine.get_recommendations(book.id)
    similar_books = similar_titles 
    
    active_transaction = None
    if hasattr(request.user, 'studentprofile'):
        active_transaction = Transaction.objects.filter(
            student=request.user.studentprofile,
            book=book,
            status__in=['pending', 'active']
        ).first()

    context = {
        'book': book,
        'similar_books': similar_books,
        'active_transaction': active_transaction
    }
    return render(request, 'library/detail.html', context)

# ==========================================
# 3. إدارة العمليات (Transactions)
# ==========================================

@login_required
@transaction.atomic
def borrow_request(request, book_id):
    """معالجة طلب استعارة كتاب"""
    book = get_object_or_404(Book, id=book_id)
    student = get_object_or_404(StudentProfile, user=request.user)

    if book.available_copies < 1:
        messages.error(request, "عذراً، لا توجد نسخ متاحة حالياً.")
        return redirect('library:book_detail', book_id=book.id)

    existing_loan = Transaction.objects.filter(
        student=student, 
        book=book, 
        status__in=['pending', 'active']
    ).exists()

    if existing_loan:
        messages.warning(request, "لديك طلب مسبق لهذا الكتاب قيد المعالجة أو لديك الكتاب بالفعل.")
        return redirect('library:book_detail', book_id=book.id)

    Transaction.objects.create(
        student=student,
        book=book,
        status='pending',
        request_date=timezone.now()
    )
    
    messages.success(request, "تم إرسال طلب الاستعارة بنجاح!")
    return redirect('library:profile')

@login_required
def profile_view(request):
    try:
        student = request.user.studentprofile
    except StudentProfile.DoesNotExist:
        messages.error(request, "ملف الطالب غير موجود.")
        return redirect('library:home')

    transactions = Transaction.objects.filter(student=student).order_by('-request_date')
    
    return render(request, 'library/profile.html', {
        'student': student,
        'transactions': transactions
    })

# ==========================================
# 4. لوحة الإدارة والتحليلات (Admin Only)
# ==========================================

@login_required
@user_passes_test(is_admin)
def analytics_dashboard(request):
    total_books = Book.objects.count()
    active_loans_count = Transaction.objects.filter(status='active').count()
    
    most_borrowed = Book.objects.annotate(
        borrow_count=Count('transaction')
    ).filter(borrow_count__gt=0).order_by('-borrow_count')[:5]

    avg_reading_data = Transaction.objects.filter(status='returned').aggregate(
        avg_diff=Avg(F('return_date') - F('borrow_date'))
    )
    
    avg_borrow_days = 0
    if avg_reading_data['avg_diff']:
        avg_borrow_days = avg_reading_data['avg_diff'].days

    gap_analysis = SearchLog.objects.filter(result_count=0).values('query_text').annotate(
        search_count=Count('query_text')
    ).order_by('-search_count')[:5]

    context = {
        'total_books': total_books,
        'active_loans_count': active_loans_count,
        'most_borrowed': most_borrowed,
        'avg_borrow_days': avg_borrow_days,
        'gap_analysis': gap_analysis,
    }
    
    return render(request, 'library/analytics.html', context)

@login_required
@user_passes_test(is_admin)
def manage_transaction(request, transaction_id, action):
    trans = get_object_or_404(Transaction, id=transaction_id)
    if action == 'approve':
        if trans.book.available_copies > 0:
            trans.status = 'active'
            trans.book.available_copies -= 1
            trans.book.save()
            trans.borrow_date = timezone.now()
            trans.save()
            messages.success(request, f"تمت الموافقة على طلب الطالب.")
        else:
            messages.error(request, "لا توجد نسخ كافية.")
    elif action == 'reject':
        trans.status = 'rejected'
        trans.save()
        messages.info(request, "تم رفض الطلب.")
    elif action == 'return':
        trans.status = 'returned'
        trans.return_date = timezone.now()
        trans.book.available_copies += 1
        trans.book.save()
        trans.save()
        messages.success(request, "تم تسجيل إرجاع الكتاب بنجاح.")

    return redirect('library:analytics')