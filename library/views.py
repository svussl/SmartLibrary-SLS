import json
from django.db.models.functions import ExtractHour
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, F, Q
from django.utils import timezone
from .models import Book, SearchLog, Transaction, StudentProfile, Notification, PhysicalVisit
from .ai_engine import SmartLibraryAI
from .forms import UserRegistrationForm, StudentLoginForm
from django.db import transaction as db_transaction
from collections import Counter

# استيراد دالة توسيع الاستعلام التي أنشأناها
from .search_utils import expand_search_query 

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
    search_type = request.GET.get('search_type', 'advanced')
    sort_option = request.GET.get('sort', 'relevance')
    
    # التقاط الفلاتر الجديدة
    book_type = request.GET.get('book_type', '')
    language = request.GET.get('language', '')
    
    books = []
    
    if query:
        if search_type == 'normal':
            results = Book.objects.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(isbn__icontains=query)
            ).distinct()
            
            if book_type:
                results = results.filter(book_type=book_type)
            if language:
                results = results.filter(language=language)
                
            books = list(results)
            
            for book in books:
                book.match_score = None 
                
        else:
            enhanced_query = expand_search_query(query)
            ai_engine = SmartLibraryAI()
            
            results = ai_engine.semantic_search(enhanced_query, top_k=40)
            
            if book_type:
                results = [b for b in results if b.book_type == book_type]
            if language:
                results = [b for b in results if b.language == language]
                
            for i, book in enumerate(results[:20]):
                if not hasattr(book, 'match_score'):
                    book.match_score = max(100 - (i * 4), 50)
                books.append(book)

        if sort_option == 'newest':
            books.sort(key=lambda x: x.id, reverse=True)
        elif sort_option == 'popular':
            books.sort(key=lambda x: x.transaction_set.count(), reverse=True)

        if 'sort' not in request.GET and 'book_type' not in request.GET:
            SearchLog.objects.create(
                user=request.user, 
                query_text=query, 
                result_count=len(books)
            )

    context = {
        'books': books, 
        'query': query, 
        'current_sort': sort_option,
        'search_type': search_type,
        'current_book_type': book_type,
        'current_language': language,
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
    
    notifications = list(Notification.objects.filter(student=student).order_by('-created_at')[:10])
    Notification.objects.filter(student=student, is_read=False).update(is_read=True)
    
    borrowed_tags = transactions.values_list('book__tags', flat=True)
    all_tags = []
    for tags_string in borrowed_tags:
        if tags_string:
            all_tags.extend([t.strip() for t in tags_string.split(',') if t.strip()])
    
    interest_cloud = [tag for tag, count in Counter(all_tags).most_common(10)]

    return render(request, 'library/profile.html', {
        'student': student,
        'transactions': transactions,
        'notifications': notifications,
        'interest_cloud': interest_cloud,
    })

@login_required
@db_transaction.atomic
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

    physical_stats = PhysicalVisit.objects.values('activity').annotate(count=Count('id'))
    active_visits = PhysicalVisit.objects.filter(check_out__isnull=True).order_by('-check_in')
    peak_hours = PhysicalVisit.objects.annotate(hour=ExtractHour('check_in')).values('hour').annotate(count=Count('id')).order_by('-count')[:5]
    top_majors = PhysicalVisit.objects.values('student__major').annotate(count=Count('id')).order_by('-count')[:5]
    all_students = StudentProfile.objects.select_related('user').all()

    total_minutes = (avg_pages / 200) * 60
    if total_minutes >= 60:
        hours = int(total_minutes // 60)
        mins = int(total_minutes % 60)
        avg_reading_time = f"{hours} ساعة و {mins} دقيقة"
    else:
        avg_reading_time = f"{int(total_minutes)} دقيقة"

    major_dict = dict(StudentProfile.MAJOR_CHOICES)
    for major in top_majors:
        major['major_display'] = major_dict.get(major['student__major'], major['student__major'])

    # ==========================================
    # تحضير بيانات المخططات البيانية (Charts Data)
    # ==========================================
    
    # 1. مخطط النشاط والتخصص
    chart1_labels = list(major_dict.values())
    c1_internet, c1_reading, c1_studying = [0]*len(chart1_labels), [0]*len(chart1_labels), [0]*len(chart1_labels)
    visits_ma = PhysicalVisit.objects.values('student__major', 'activity').annotate(count=Count('id'))
    for v in visits_ma:
        try:
            idx = list(major_dict.keys()).index(v['student__major'])
            if v['activity'] == 'internet': c1_internet[idx] = v['count']
            elif v['activity'] == 'reading': c1_reading[idx] = v['count']
            elif v['activity'] == 'studying': c1_studying[idx] = v['count']
        except ValueError:
            pass
            
    chart1_data = json.dumps({
        'labels': chart1_labels, 'internet': c1_internet, 'reading': c1_reading, 'studying': c1_studying
    })

    # 2. مخطط النشاط والزمن (الساعة 8 صباحاً حتى 6 مساءً)
    chart2_labels = [f"{h}:00" for h in range(8, 19)]
    c2_internet, c2_reading, c2_studying = [0]*11, [0]*11, [0]*11
    visits_time = PhysicalVisit.objects.annotate(hour=ExtractHour('check_in')).values('hour', 'activity').annotate(count=Count('id'))
    for v in visits_time:
        h = v['hour']
        if h is not None and 8 <= h <= 18:
            idx = h - 8
            if v['activity'] == 'internet': c2_internet[idx] = v['count']
            elif v['activity'] == 'reading': c2_reading[idx] = v['count']
            elif v['activity'] == 'studying': c2_studying[idx] = v['count']
            
    chart2_data = json.dumps({
        'labels': chart2_labels, 'internet': c2_internet, 'reading': c2_reading, 'studying': c2_studying
    })

    # 3. مخطط التصنيفات الأكثر استعارة
    cat_dict = dict(Book.CATEGORY_CHOICES)
    top_cats = Transaction.objects.values('book__category').annotate(count=Count('id')).order_by('-count')[:6]
    c3_labels = [cat_dict.get(c['book__category'], c['book__category']) for c in top_cats]
    c3_data = [c['count'] for c in top_cats]
    
    chart3_data = json.dumps({'labels': c3_labels, 'data': c3_data})

    return render(request, 'library/analytics.html', {
        'total_books': total_books,
        'active_loans_count': active_loans_count,
        'most_borrowed': most_borrowed,
        'gap_analysis': gap_analysis,
        'physical_stats': physical_stats,
        'active_visits': active_visits,
        'peak_hours': peak_hours,
        'top_majors': top_majors,
        'avg_reading_time': avg_reading_time,
        'all_students': all_students,
        'chart1_data': chart1_data,
        'chart2_data': chart2_data,
        'chart3_data': chart3_data,
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
        
        Notification.objects.create(
            student=trans.student,
            message=f"تمت الموافقة على طلب إعارة كتاب '{trans.book.title}'. يمكنك استلامه الآن من المكتبة."
        )
        messages.success(request, "تمت الموافقة وتم تنبيه الطالب.")
        
    elif action == 'reject':
        trans.status = 'rejected'
        trans.save()
        
        Notification.objects.create(
            student=trans.student,
            message=f"عذراً، تم رفض طلب إعارة كتاب '{trans.book.title}'."
        )
        messages.info(request, "تم الرفض وتم تنبيه الطالب.")
        
    elif action == 'return':
        trans.status = 'returned'
        trans.return_date = timezone.now()
        trans.book.available_copies += 1
        trans.book.save()
        trans.save()
        messages.success(request, "تم الإرجاع بنجاح.")
        
    return redirect('library:analytics')


# ==========================================
# 4. إدارة المكتبة الواقعية (Physical Library)
# ==========================================

@login_required
@user_passes_test(is_admin)
def physical_check_in(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        activity = request.POST.get('activity')
        
        try:
            student = StudentProfile.objects.get(student_id=student_id)
            PhysicalVisit.objects.create(
                student=student, 
                activity=activity
            )
            messages.success(request, f"تم تسجيل دخول الطالب {student.user.get_full_name()} للقيام بـ ({activity}).")
        except StudentProfile.DoesNotExist:
            messages.error(request, "لم يتم العثور على طالب بهذا الرقم الجامعي.")
            
    return redirect('library:analytics')

@login_required
@user_passes_test(is_admin)
def physical_check_out(request, visit_id):
    visit = get_object_or_404(PhysicalVisit, id=visit_id)
    visit.check_out = timezone.now()
    visit.save()
    messages.success(request, "تم تسجيل خروج الطالب من المكتبة بنجاح.")
    return redirect('library:analytics')