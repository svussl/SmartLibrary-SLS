# ==========================================
# ملف admin.py
# ==========================================
from django.contrib import admin
from django.contrib import messages
from .models import Book, StudentProfile, Transaction, SearchLog, Notification, PhysicalVisit
from .ai_engine import SmartLibraryAI
import requests

# ==========================================
# إعدادات العرض العامة لمركز الإدارة
# ==========================================
admin.site.site_header = "إدارة المكتبة الذكية (SLS)"
admin.site.site_title = "نظام المكتبة المتقدم"
admin.site.index_title = "لوحة تحكم المشرف العام"

# ==========================================
# 0. الإجراءات المخصصة (Custom Actions)
# ==========================================
@admin.action(description='⚡ تحديث البصمة الدلالية للذكاء الاصطناعي (Embeddings)')
def update_embeddings(modeladmin, request, queryset):
    """
    إجراء وظيفي مخصص لتوليد أو تحديث البصمة الرقمية للكتب يدوياً في حال لم تتم العملية تلقائياً.
    يتم استدعاء نموذج معالجة اللغات الطبيعية (NLP) لحساب المتجهات.
    """
    ai = SmartLibraryAI()
    count = 0
    for book in queryset:
        ai.update_book_embedding(book)
        count += 1
    modeladmin.message_user(request, f"تم بنجاح تحديث وتوليد البصمة الدلالية لعدد {count} كتاب.")

# ==========================================
# 1. إدارة محتوى الكتب (BookAdmin) مع الأتمتة
# ==========================================
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'book_type', 'language', 'total_copies', 'available_copies')
    # حقول البحث الموسعة لضمان عمل واجهة الإكمال التلقائي (Autocomplete) بفعالية
    search_fields = ('title', 'author', 'isbn', 'publisher') 
    list_filter = ('category', 'book_type', 'language', 'created_at')
    readonly_fields = ('created_at', 'embedding')

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('title', 'author', 'isbn', 'category', 'book_type', 'language')
        }),
        ('بيانات النشر', {
            'fields': ('publisher', 'publication_year'),
            'description': 'تفاصيل دار النشر وتاريخ الإصدار لغايات التوثيق الأكاديمي.'
        }),
        ('التفاصيل والمحتوى', {
            'fields': ('description', 'tags', 'cover_image_url', 'page_count')
        }),
        ('إدارة المخزون والتوافر', {
            'fields': ('total_copies', 'available_copies')
        }),
        ('محرك الذكاء الاصطناعي', {
            'fields': ('embedding', 'created_at'), 
            'classes': ('collapse',)
        }),
    )
    actions = [update_embeddings]

    def fetch_book_data(self, query):
        """دالة مساعدة لمعالجة طلبات الاتصال بواجهة برمجة تطبيقات Google Books"""
        try:
            api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "items" in data and len(data["items"]) > 0:
                    return data["items"][0]["volumeInfo"]
        except Exception as e:
            return None
        return None

    def save_model(self, request, obj, form, change):
        """تجاوز وظيفة الحفظ الافتراضية لأتمتة استخراج البيانات المفقودة تلقائياً من مصادر خارجية"""
        # التحقق من وجود نواقص في الحقول الأساسية قبل استدعاء الـ API لتجنب استهلاك الموارد عبثاً
        if not obj.description or not obj.publisher or not obj.publication_year:
            book_info = None
            source = ""

            # المحاولة الأولى: عبر الرقم المعياري الدولي للكتاب (ISBN)
            if obj.isbn:
                clean_isbn = obj.isbn.replace("-", "").replace(" ", "")
                book_info = self.fetch_book_data(f"isbn:{clean_isbn}")
                source = "رقم الإيداع (ISBN)"

            # المحاولة الثانية: عبر العنوان (في حال فشل البحث بالرقم المعياري)
            if (not book_info or not book_info.get("description")) and obj.title:
                alt_info = self.fetch_book_data(f"intitle:{obj.title}")
                if alt_info and alt_info.get("description"):
                    book_info = alt_info
                    source = "عنوان الكتاب"

            # تطبيق البيانات المستخرجة على النموذج الوظيفي
            if book_info:
                if not obj.description and book_info.get("description"):
                    obj.description = book_info.get("description")
                    messages.success(request, f"✅ تمت أتمتة جلب الوصف التفصيلي باستخدام {source}.")
                
                # جلب وتعيين بيانات الناشر وسنة النشر إن توفرت
                if not obj.publisher and book_info.get("publisher"):
                    obj.publisher = book_info.get("publisher")
                    
                if not obj.publication_year and book_info.get("publishedDate"):
                    pub_date = book_info.get("publishedDate")
                    if len(pub_date) >= 4:
                        obj.publication_year = int(pub_date[:4])
                        
                if not obj.language and book_info.get("language"):
                    obj.language = book_info.get("language").upper()

                if not obj.cover_image_url and "imageLinks" in book_info:
                    obj.cover_image_url = book_info["imageLinks"].get("thumbnail", "")
                
                categories = book_info.get("categories", [])
                if categories and not obj.tags:
                    obj.tags = ", ".join(categories)
                
                if not obj.author and "authors" in book_info:
                    obj.author = ", ".join(book_info["authors"])
        else:
            if obj.isbn and not change:
                messages.warning(request, f"⚠️ لم يتم العثور على بيانات إضافية مؤتمتة لهذا المرجع.")

        super().save_model(request, obj, form, change)
        
        # التحديث الآلي لنموذج التضمين (Embedding) الخاص بالذكاء الاصطناعي
        if not obj.embedding:
            try:
                ai = SmartLibraryAI()
                ai.update_book_embedding(obj)
            except Exception as e:
                pass

# ==========================================
# 2. إدارة ملفات الطلاب (StudentProfileAdmin)
# ==========================================
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'student_id', 'major', 'get_email')
    search_fields = ('student_id', 'user__first_name', 'user__last_name', 'user__username', 'user__email')
    list_filter = ('major',)
    
    def get_email(self, obj): return obj.user.email
    get_email.short_description = 'البريد الإلكتروني'

    def get_full_name(self, obj): return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = "الاسم الكامل"

# ==========================================
# 3. إدارة العمليات والإعارات (TransactionAdmin)
# ==========================================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'status', 'borrow_date', 'due_date', 'is_overdue')
    list_filter = ('status', 'request_date')
    search_fields = ('book__title', 'student__student_id', 'student__user__username')
    
    autocomplete_fields = ['student', 'book']
    readonly_fields = ('borrow_date', 'due_date', 'return_date', 'request_date')

    fieldsets = (
        ('تفاصيل الارتباط والإعارة', {
            'fields': ('student', 'book', 'status'),
            'description': 'إدارة حالة الكتاب، التبديل إلى "جاري" سيفعل التواريخ تلقائياً وينبه الطالب.'
        }),
        ('السجل الزمني الآلي', {
            'fields': ('request_date', 'borrow_date', 'due_date', 'return_date')
        }),
    )
    actions = ['approve_requests', 'mark_returned', 'reject_requests']

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial['status'] = 'active'
        return initial

    @admin.action(description='✅ الموافقة وتفعيل الإعارة (مع التنبيه)')
    def approve_requests(self, request, queryset):
        count = 0
        for t in queryset.filter(status='pending'):
            t.status = 'active'
            t.save()  # استدعاء الدالة save لتحديث التواريخ وخصم النسخ ضمن models.py
            
            # توليد تنبيه آلي للطالب
            Notification.objects.create(
                student=t.student,
                message=f"تمت الموافقة الإدارية على طلب إعارة كتاب '{t.book.title}'. تفضل باستلامه."
            )
            count += 1
        self.message_user(request, f"تمت الموافقة وتفعيل {count} طلب إعارة بنجاح.")

    @admin.action(description='↩️ تسجيل إرجاع الكتب إلى الرفوف')
    def mark_returned(self, request, queryset):
        count = 0
        for t in queryset.filter(status='active'):
            t.status = 'returned'
            t.save()
            count += 1
        self.message_user(request, f"تم تسجيل إرجاع وإغلاق {count} دورة إعارة.")

    @admin.action(description='❌ رفض طلبات الاستعارة')
    def reject_requests(self, request, queryset):
        count = 0
        for t in queryset.filter(status='pending'):
            t.status = 'rejected'
            t.save()
            
            # توليد تنبيه آلي للرفض
            Notification.objects.create(
                student=t.student,
                message=f"عذراً، تعذر تلبية طلبك لاستعارة كتاب '{t.book.title}' في الوقت الحالي."
            )
            count += 1
        self.message_user(request, f"تم رفض {count} طلب إعارة وتنبيه الطلاب المعنيين.")

# ==========================================
# 4. سجلات تحليل الفجوة (Gap Analysis)
# ==========================================
@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'user', 'result_count', 'timestamp')
    search_fields = ('query_text',)
    list_filter = ('timestamp',)

# ==========================================
# 5. إدارة نظام التنبيهات (NotificationAdmin)
# ==========================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('student', 'message_snippet', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('student__student_id', 'student__user__username', 'message')
    autocomplete_fields = ['student']

    def message_snippet(self, obj):
        return obj.message[:60] + '...' if len(obj.message) > 60 else obj.message
    message_snippet.short_description = "محتوى التنبيه"

# ==========================================
# 6. سجلات التواجد المادي (PhysicalVisitAdmin)
# ==========================================
@admin.register(PhysicalVisit)
class PhysicalVisitAdmin(admin.ModelAdmin):
    list_display = ('student', 'activity', 'check_in', 'check_out', 'stay_duration')
    list_filter = ('activity', 'check_in')
    search_fields = ('student__student_id', 'student__user__username', 'student__user__first_name')
    autocomplete_fields = ['student']
    readonly_fields = ('stay_duration',)