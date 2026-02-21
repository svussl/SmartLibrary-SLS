from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# ==========================================
# 1. جدول الكتب (Library Books)
# ==========================================

class Book(models.Model):
    CATEGORY_CHOICES = [
        ('Programming', 'برمجة وتطوير (Programming)'),
        ('CyberSecurity', 'أمن سيبراني (Cyber Security)'),
        ('AI', 'ذكاء اصطناعي (AI & Data Science)'),
        ('Networking', 'شبكات واتصالات (Networking)'),
        ('Medical', 'طب بشري (Human Medicine)'),
        ('Pharmacy', 'صيدلة (Pharmacy)'),
        ('Dentistry', 'طب أسنان (Dentistry)'),
        ('Nursing', 'تمريض (Nursing)'),
        ('Engineering', 'هندسة عامة (General Engineering)'),
        ('CivilEng', 'هندسة مدنية (Civil Engineering)'),
        ('Arch', 'هندسة معمارية (Architecture)'),
        ('Electrical', 'هندسة كهربائية (Electrical Eng)'),
        ('Law', 'قانون وحقوق (Law)'),
        ('Economics', 'اقتصاد وإدارة أعمال (Economics & Business)'),
        ('Psychology', 'علم نفس (Psychology)'),
        ('Sociology', 'علم اجتماع (Sociology)'),
        ('History', 'تاريخ (History)'),
        ('Geography', 'جغرافيا (Geography)'),
        ('Literature', 'أدب ولغات (Literature & Languages)'),
        ('Religion', 'شريعة ودراسات إسلامية (Islamic Studies)'),
        ('Math', 'رياضيات (Mathematics)'),
        ('Physics', 'فيزياء (Physics)'),
        ('Chemistry', 'كيمياء (Chemistry)'),
        ('Biology', 'أحياء (Biology)'),
        ('Arts', 'فنون وتصميم (Arts & Design)'),
        ('General', 'ثقافة عامة (General Culture)'),
    ]

    title = models.CharField(max_length=200, verbose_name="عنوان الكتاب")
    author = models.CharField(max_length=100, verbose_name="المؤلف")
    isbn = models.CharField(max_length=13, blank=True, null=True, verbose_name="رقم الإيداع (ISBN)")
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='General', verbose_name="التصنيف")
    description = models.TextField(blank=True, verbose_name="وصف الكتاب")
    cover_image_url = models.URLField(blank=True, null=True, verbose_name="رابط الغلاف")
    
    # حقل عدد الصفحات لحساب مدة القراءة
    page_count = models.IntegerField(default=100, verbose_name="عدد الصفحات")
    
    total_copies = models.IntegerField(default=1, verbose_name="العدد الكلي")
    available_copies = models.IntegerField(default=1, verbose_name="النسخ المتاحة")
    tags = models.CharField(max_length=200, blank=True, verbose_name="وسوم")
    
    # === حقل الذكاء الاصطناعي ===
    embedding = models.JSONField(blank=True, null=True, verbose_name="البصمة الرقمية (AI Vector)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def reading_time(self):
        """
        حساب متوسط مدة القراءة.
        بافتراض أن الشخص يقرأ صفحة واحدة كل دقيقتين تقريباً.
        """
        if self.page_count:
            minutes = self.page_count * 2
            if minutes < 60:
                return f"{minutes} دقيقة"
            hours = minutes // 60
            remaining_mins = minutes % 60
            if remaining_mins > 0:
                return f"{hours} ساعة و {remaining_mins} دقيقة"
            return f"{hours} ساعة"
        return "غير محدد"

    def __str__(self):
        return f"{self.title} | {self.author}"

# ==========================================
# 2. ملف الطالب (Student Profile)
# ==========================================
class StudentProfile(models.Model):
    MAJOR_CHOICES = [
        ('General', 'سنة تحضيرية / عام'),
        ('CS', 'علم الحاسوب (Computer Science)'),
        ('SE', 'هندسة برمجيات (Software Engineering)'),
        ('AI', 'ذكاء اصطناعي (AI)'),
        ('CyberSec', 'أمن سيبراني (Cyber Security)'),
        ('Med', 'طب بشري'),
        ('Dent', 'طب أسنان'),
        ('Pharm', 'صيدلة'),
        ('Arch', 'هندسة معمارية'),
        ('Civil', 'هندسة مدنية'),
        ('Business', 'إدارة أعمال'),
        ('Law', 'حقوق'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True, verbose_name="الرقم الجامعي")
    
    major = models.CharField(
        max_length=50, 
        choices=MAJOR_CHOICES, 
        default='General',
        verbose_name="التخصص الدراسي"
    )

    interest_fingerprint = models.TextField(blank=True, null=True, verbose_name="بصمة الاهتمامات")

    def __str__(self):
        full_name = f"{self.user.first_name} {self.user.last_name}"
        if not full_name.strip():
            full_name = self.user.username
        return f"{full_name} ({self.student_id})"


# ==========================================
# 3. جدول العمليات والإعارة (Transactions)
# ==========================================
class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار (طلب إلكتروني)'),
        ('active', 'جاري (تم التسليم للطالب)'),
        ('returned', 'تم الإرجاع للمكتبة'),
        ('rejected', 'مرفوض'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="الكتاب")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, verbose_name="الطالب")
    
    request_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    borrow_date = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الاستلام الفعلي")
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الاستحقاق")
    return_date = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الإرجاع")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الطلب")
    user_rating = models.IntegerField(null=True, blank=True, verbose_name="التقييم (1-5)")

    def save(self, *args, **kwargs):
        if self.status == 'active':
            if not self.borrow_date:
                self.borrow_date = timezone.now()
            if not self.due_date:
                self.due_date = timezone.now() + timedelta(days=14)
            
            if self.pk:
                old_instance = Transaction.objects.get(pk=self.pk)
                if old_instance.status != 'active' and self.book.available_copies > 0:
                    self.book.available_copies -= 1
                    self.book.save()
            else:
                if self.book.available_copies > 0:
                    self.book.available_copies -= 1
                    self.book.save()
            
        if self.status == 'returned' and not self.return_date:
            self.return_date = timezone.now()
            self.book.available_copies += 1
            self.book.save()
            
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.status == 'active' and self.due_date and timezone.now() > self.due_date:
            return True
        return False

    def __str__(self):
        return f"{self.book.title} - {self.student.student_id}"

    class Meta:
        verbose_name = "عملية إعارة"
        verbose_name_plural = "عمليات الإعارة"
        ordering = ['-request_date']


# ==========================================
# 4. سجل البحث (Gap Analysis Logs)
# ==========================================
class SearchLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    query_text = models.CharField(max_length=255, verbose_name="نص البحث")
    timestamp = models.DateTimeField(auto_now_add=True)
    result_count = models.IntegerField(default=0, verbose_name="عدد النتائج")
    clicked_result = models.BooleanField(default=False)

    class Meta:
        verbose_name = "سجل بحث"
        verbose_name_plural = "سجلات البحث (Gap Analysis)"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.query_text} ({self.result_count})"