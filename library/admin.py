from django.contrib import admin
from django.contrib import messages
from .models import Book, StudentProfile, Transaction, SearchLog
from .ai_engine import SmartLibraryAI
import requests

# ==========================================
# إعدادات العرض العامة
# ==========================================
admin.site.site_header = "إدارة المكتبة الذكية (SLS)"
admin.site.site_title = "نظام المكتبة"
admin.site.index_title = "لوحة تحكم المشرف"

# ==========================================
# 0. Custom Actions (إجراءات مخصصة)
# ==========================================
@admin.action(description='⚡ تحديث بصمة الذكاء الاصطناعي (Embeddings)')
def update_embeddings(modeladmin, request, queryset):
    """
    توليد البصمة الرقمية للكتب يدوياً في حال لم تتم تلقائياً
    """
    ai = SmartLibraryAI()
    count = 0
    for book in queryset:
        ai.update_book_embedding(book)
        count += 1
    modeladmin.message_user(request, f"تم تحديث البصمة الدلالية لـ {count} كتاب.")

# ==========================================
# 1. إدارة الكتب (BookAdmin) مع الجلب التلقائي
# ==========================================
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'total_copies', 'available_copies')
    # حقول البحث هذه ضرورية لكي يعمل الـ Autocomplete في صفحة الإعارة
    search_fields = ('title', 'author', 'isbn') 
    list_filter = ('category', 'created_at')
    readonly_fields = ('created_at', 'embedding')

    fieldsets = (
        ('المعلومات الأساسية', {'fields': ('title', 'author', 'isbn', 'category')}),
        ('التفاصيل والمحتوى', {'fields': ('description', 'tags', 'cover_image_url')}),
        ('المخزون', {'fields': ('total_copies', 'available_copies')}),
        ('الذكاء الاصطناعي', {'fields': ('embedding', 'created_at'), 'classes': ('collapse',)}),
    )
    actions = [update_embeddings]

    def fetch_book_data(self, query):
        """دالة مساعدة للاتصال بـ Google Books API"""
        try:
            api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "items" in data and len(data["items"]) > 0:
                    return data["items"][0]["volumeInfo"]
        except:
            return None
        return None

    def save_model(self, request, obj, form, change):
        """تجاوز الحفظ لجلب البيانات تلقائياً إذا كان الوصف فارغاً"""
        if not obj.description:
            book_info = None
            source = ""

            # المحاولة 1: ISBN
            if obj.isbn:
                clean_isbn = obj.isbn.replace("-", "").replace(" ", "")
                book_info = self.fetch_book_data(f"isbn:{clean_isbn}")
                source = "ISBN"

            # المحاولة 2: العنوان (إذا فشل ISBN)
            if (not book_info or not book_info.get("description")) and obj.title:
                alt_info = self.fetch_book_data(f"intitle:{obj.title}")
                if alt_info and alt_info.get("description"):
                    book_info = alt_info
                    source = "العنوان (Title)"

            # تطبيق البيانات
            if book_info:
                if book_info.get("description"):
                    obj.description = book_info.get("description")
                    messages.success(request, f"✅ تم جلب الوصف بنجاح باستخدام {source}!")
                else:
                    messages.warning(request, f"⚠️ تم العثور على الكتاب لكن لا يوجد وصف متاح.")

                if not obj.cover_image_url and "imageLinks" in book_info:
                    obj.cover_image_url = book_info["imageLinks"].get("thumbnail", "")
                
                categories = book_info.get("categories", [])
                if categories and not obj.tags:
                    obj.tags = ", ".join(categories)
                
                if not obj.author and "authors" in book_info:
                    obj.author = ", ".join(book_info["authors"])
            else:
                if obj.isbn:
                    messages.warning(request, f"⚠️ لم يتم العثور على بيانات للكتاب.")

        super().save_model(request, obj, form, change)
        
        # تحديث الذكاء الاصطناعي
        if not obj.embedding:
            try:
                ai = SmartLibraryAI()
                ai.update_book_embedding(obj)
            except:
                pass

# ==========================================
# 2. إدارة الطلاب (StudentProfileAdmin)
# ==========================================
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'student_id', 'major', 'get_email')
    # حقول البحث هنا ضرورية لكي يعمل الـ Autocomplete في صفحة الإعارة
    search_fields = ('student_id', 'user__first_name', 'user__last_name', 'user__username', 'user__email')
    list_filter = ('major',)
    
    def get_email(self, obj): return obj.user.email
    get_email.short_description = 'البريد الإلكتروني'

    def get_full_name(self, obj): return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = "الاسم الكامل"

# ==========================================
# 3. إدارة الإعارات (TransactionAdmin)
# ==========================================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'status', 'borrow_date', 'due_date', 'is_overdue')
    list_filter = ('status', 'request_date')
    search_fields = ('book__title', 'student__student_id', 'student__user__username')
    
    # تفعيل البحث والإكمال التلقائي (يعتمد على search_fields في الكلاسات السابقة)
    autocomplete_fields = ['student', 'book']
    
    readonly_fields = ('borrow_date', 'due_date', 'return_date', 'request_date')

    fieldsets = (
        ('تفاصيل الإعارة', {
            'fields': ('student', 'book', 'status'),
            'description': 'عند اختيار الحالة "جاري (Active)" سيتم تعيين التواريخ تلقائياً.'
        }),
        ('التواريخ (تلقائية)', {
            'fields': ('request_date', 'borrow_date', 'due_date', 'return_date')
        }),
    )
    actions = ['approve_requests', 'mark_returned', 'reject_requests']

    def get_changeform_initial_data(self, request):
        # جعل الحالة الافتراضية "Active" لتسهيل الإعارة الفورية
        initial = super().get_changeform_initial_data(request)
        initial['status'] = 'active'
        return initial

    @admin.action(description='✅ الموافقة وتفعيل الإعارة')
    def approve_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='active')
        # نمر عليهم للحفظ لضمان حساب التواريخ وخصم المخزون
        for t in queryset.filter(status='active', borrow_date__isnull=True): 
            t.save()
        self.message_user(request, f"تمت الموافقة وتفعيل {updated} طلب.")

    @admin.action(description='↩️ تسجيل إرجاع الكتب')
    def mark_returned(self, request, queryset):
        count = 0
        for t in queryset.filter(status='active'):
            t.status = 'returned'
            t.save()
            count += 1
        self.message_user(request, f"تم تسجيل إرجاع {count} كتب بنجاح.")

    @admin.action(description='❌ رفض الطلبات')
    def reject_requests(self, request, queryset):
        rows = queryset.update(status='rejected')
        self.message_user(request, f"تم رفض {rows} طلب.")

# ==========================================
# 4. سجلات البحث (Analytics)
# ==========================================
@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'user', 'result_count', 'timestamp')
    search_fields = ('query_text',)