from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Q
from django.utils import timezone
from .models import Book, SearchLog, Transaction, StudentProfile
from .ai_engine import SmartLibraryAI
from .forms import UserRegistrationForm


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
            
            login(request, user)
            messages.success(request, f"مرحباً بك {user.first_name}! تم إنشاء حسابك بنجاح.")
            return redirect('library:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'library/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('library:home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"أهلاً بعودتك، {user.first_name}!")
                return redirect('library:home')
            else:
                messages.error(request, "اسم المستخدم أو كلمة المرور غير صحيحة.")
        else:
            messages.error(request, "الرجاء التحقق من البيانات المدخلة.")
    else:
        form = AuthenticationForm()
    
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

        # أ) محاولة جلب توصيات بناءً على آخر استعارة
        last_loan = Transaction.objects.filter(student=profile).last()
        
        if last_loan:
            books = ai_engine.get_recommendations(last_loan.book.id, top_k=8)
        
        # ب) إذا لم يستعر شيئاً، نجلب كتباً بناءً على تخصصه
        if not books:
            major_text = profile.get_major_display()
            if major_text != 'General':
                books = ai_engine.recommend_by_profile(major_text, top_k=8)

    # ج) إذا لم توجد توصيات، نعرض أحدث الكتب
    if not books:
        books = Book.objects.all().order_by('-created_at')[:8]

    return render(request, 'library/home.html', {'books': books})

@login_required
def search_view(request):
    query = request.GET.get('q', '')
    books = []
    
    if query:
        ai_engine = SmartLibraryAI()
        books = ai_engine.semantic_search(query)
        
        # تسجيل العملية
        user = request.user if request.user.is_authenticated else None
        SearchLog.objects.create(user=user, query_text=query, result_count=len(books))

    return render(request, 'library/search.html', {'books': books, 'query': query})


@login_required
def book_detail(request, book_id):
    """صفحة تفاصيل الكتاب مع التوصيات المشابهة"""
    book = get_object_or_404(Book, id=book_id)
    
    ai_engine = SmartLibraryAI()
    similar_titles = ai_engine.get_recommendations(book.id)
    similar_books = similar_titles 
    
    # التحقق من حالة الاستعارة (تم إصلاح الخطأ هنا) ✅
    active_transaction = None
    if hasattr(request.user, 'studentprofile'):
        active_transaction = Transaction.objects.filter(
            student=request.user.studentprofile,
            book=book,
            status__in=['pending', 'active'] # استخدام الحقل الصحيح status بدلاً من is_returned
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
def borrow_request(request, book_id):
    """معالجة طلب استعارة كتاب"""
    book = get_object_or_404(Book, id=book_id)
    student = get_object_or_404(StudentProfile, user=request.user)

    if book.available_copies < 1:
        messages.error(request, "عذراً، لا توجد نسخ متاحة حالياً.")
        return redirect('library:book_detail', book_id=book.id)

    # التحقق من عدم وجود طلب مسبق (تم إصلاح الخطأ هنا أيضاً) ✅
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
    pending_requests = Transaction.objects.filter(status='pending').order_by('request_date')
    active_loans = Transaction.objects.filter(status='active').order_by('due_date')
    
    most_borrowed = Transaction.objects.values('book__title') \
        .annotate(total_borrows=Count('id')) \
        .order_by('-total_borrows')[:5]

    avg_duration_data = Transaction.objects.filter(status='returned') \
        .annotate(duration=ExpressionWrapper(
            F('return_date') - F('borrow_date'), 
            output_field=DurationField()
        )) \
        .values('book__title') \
        .annotate(avg_days=Avg('duration')) \
        .order_by('-avg_days')[:5]

    gap_analysis = SearchLog.objects.filter(result_count=0) \
        .values('query_text') \
        .annotate(attempts=Count('id')) \
        .order_by('-attempts')[:5]

    context = {
        'pending_requests': pending_requests,
        'active_loans': active_loans,
        'most_borrowed': most_borrowed,
        'avg_duration_data': avg_duration_data,
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
        trans.save()
        messages.success(request, "تم تسجيل إرجاع الكتاب بنجاح.")

    return redirect('library:analytics')