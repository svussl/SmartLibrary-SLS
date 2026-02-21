from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, F
from django.utils import timezone
from .models import Book, SearchLog, Transaction, StudentProfile
from .ai_engine import SmartLibraryAI
from .forms import UserRegistrationForm, StudentLoginForm
from django.db import transaction
from collections import Counter

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
# 2. الوظائف الرئيسية والبحث الذكي
# ==========================================

@login_required
def home(request):
    """الصفحة الرئيسية: تعرض توصيات ذكية"""
    books = []
    ai_engine = SmartLibraryAI()
    
    if hasattr(request.user, 'studentprofile'):
        profile = request.user.studentprofile
        last_loan = Transaction.objects.filter(student=profile).order_by('-request_date').first()
        
        if last_loan:
            books = ai_engine.get_recommendations(last_loan.book.id, top_k=8)
        
        if not books:
            major_text = profile.get_major_display()
            if major_text != 'General':
                books = ai_engine.recommend_by_profile(major_text, top_k=8)

    if not books:
        books = Book.objects.all().order_by('-id')[:8]

    return render(request, 'library/home.html', {'books': books})

@login_required
def search_view(request):
    query = request.GET.get('q', '')
    sort_option = request.GET.get('sort', 'relevance')
    
    books = []
    
    if query:
        ai_engine = SmartLibraryAI()
        # جلب الكتب المرتبة دلالياً من المحرك
        results = ai_engine.semantic_search(query, top_k=20)
        
        # تحضير النتائج وإضافة match_score للعرض
        for i, book in enumerate(results):
            # إذا لم يزودنا المحرك بـ score، ننشئ واحداً افتراضياً للترتيب
            if not hasattr(book, 'match_score'):
                book.match_score = max(100 - (i * 4), 50)
            books.append(book)

        # تطبيق خيارات الترتيب الإضافية
        if sort_option == 'newest':
            books.sort(key=lambda x: x.id, reverse=True)
        elif sort_option == 'popular':
            books.sort(key=lambda x: x.transaction_set.count(), reverse=True)

        # تسجيل البحث للتحليلات (فقط عند البحث الفعلي وليس عند تغيير الترتيب فقط)
        if 'sort' not in request.GET:
            SearchLog.objects.create(
                user=request.user, 
                query_text=query, 
                result_count=len(books)
            )

    context = {
        'books': books, 
        'query': query,
        'current_sort': sort_option,
    }
    return render(request, 'library/search.html', context)

@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    ai_engine = SmartLibraryAI()
    similar_books = ai_engine.get_recommendations(book.id, top_k=4)
    
    active_transaction = Transaction.objects.filter(
        student__user=request.user,
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
# 3. إدارة العمليات والملف الشخصي
# ==========================================

@login_required
def profile_view(request):
    try:
        student = request.user.studentprofile
    except StudentProfile.DoesNotExist:
        messages.error(request, "ملف الطالب غير موجود.")
        return redirect('library:home')

    transactions = Transaction.objects.filter(student=student).order_by('-request_date')
    
    borrowed_tags = transactions.values_list('book__tags', flat=True)
    all_tags = []
    for tags_string in borrowed_tags:
        if tags_string:
            all_tags.extend([t.strip() for t in tags_string.split(',') if t.strip()])
    
    interest_cloud = [tag for tag, count in Counter(all_tags).most_common(10)]

    return render(request, 'library/profile.html', {
        'student': student,
        'transactions': transactions,
        'interest_cloud': interest_cloud,
    })

@login_required
@transaction.atomic
def borrow_request(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    student = get_object_or_404(StudentProfile, user=request.user)

    if book.available_copies < 1:
        messages.error(request, "عذراً، لا توجد نسخ متاحة.")
        return redirect('library:book_detail', book_id=book.id)

    if Transaction.objects.filter(student=student, book=book, status__in=['pending', 'active']).exists():
        messages.warning(request, "لديك طلب مسبق لهذا الكتاب.")
        return redirect('library:book_detail', book_id=book.id)

    Transaction.objects.create(student=student, book=book, status='pending')
    messages.success(request, "تم إرسال طلب الاستعارة!")
    return redirect('library:profile')

@login_required
@user_passes_test(is_admin)
def analytics_dashboard(request):
    total_books = Book.objects.count()
    active_loans_count = Transaction.objects.filter(status='active').count()
    most_borrowed = Book.objects.annotate(bc=Count('transaction')).order_by('-bc')[:5]
    gap_analysis = SearchLog.objects.filter(result_count=0).values('query_text').annotate(sc=Count('query_text')).order_by('-sc')[:5]
    avg_pages = Book.objects.aggregate(Avg('page_count'))['page_count__avg'] or 0

    total_minutes = (avg_pages / 200) * 60
    
    if total_minutes >= 60:
        hours = int(total_minutes // 60)
        mins = int(total_minutes % 60)
        avg_reading_time = f"{hours} ساعة و {mins} دقيقة"
    else:
        avg_reading_time = f"{int(total_minutes)} دقيقة"

    return render(request, 'library/analytics.html', {
        'total_books': total_books,
        'active_loans_count': active_loans_count,
        'most_borrowed': most_borrowed,
        'gap_analysis': gap_analysis,
        'avg_reading_time': avg_reading_time,
    })

@login_required
@user_passes_test(is_admin)
def manage_transaction(request, transaction_id, action):
    trans = get_object_or_404(Transaction, id=transaction_id)
    if action == 'approve' and trans.book.available_copies > 0:
        trans.status = 'active'
        trans.book.available_copies -= 1
        trans.book.save()
        trans.borrow_date = timezone.now()
        trans.due_date = trans.borrow_date + timezone.timedelta(days=14)
        trans.save()
        messages.success(request, "تمت الموافقة.")
    elif action == 'reject':
        trans.status = 'rejected'
        trans.save()
        messages.info(request, "تم الرفض.")
    elif action == 'return':
        trans.status = 'returned'
        trans.return_date = timezone.now()
        trans.book.available_copies += 1
        trans.book.save()
        trans.save()
        messages.success(request, "تم الإرجاع.")
    return redirect('library:analytics')