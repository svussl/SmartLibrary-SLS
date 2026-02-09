from django.contrib import admin
from .models import Book, StudentProfile, Transaction, SearchLog
from .ai_engine import SmartLibraryAI

# ==========================================
# 0. تعريف إجراءات مخصصة (Custom Actions)
# ==========================================

@admin.action(description='⚡ تحديث بصمة الذكاء الاصطناعي (Embeddings)')
def update_embeddings(modeladmin, request, queryset):
    """
    يقوم هذا الإجراء بتوليد البصمة الرقمية للكتب المختارة
    باستخدام محرك الذكاء الاصطناعي.
    """
    ai = SmartLibraryAI()
    count = 0
    for book in queryset:
        ai.update_book_embedding(book)
        count += 1
    modeladmin.message_user(request, f"تم تحديث البصمة الدلالية بنجاح لـ {count} كتاب.")

# ==========================================
# 1. تخصيص واجهة إدارة الكتب
# ==========================================

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'total_copies', 'available_copies', 'created_at')
    search_fields = ('title', 'author', 'isbn', 'tags')
    list_filter = ('category', 'created_at')
    readonly_fields = ('created_at', 'embedding') # عرض البصمة للقراءة فقط

    # تقسيم الحقول بشكل منظم
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('title', 'author', 'isbn', 'category')
        }),
        ('التفاصيل والمحتوى', {
            'fields': ('description', 'tags', 'cover_image_url')
        }),
        ('المخزون', {
            'fields': ('total_copies', 'available_copies')
        }),
        ('الذكاء الاصطناعي', {
            'fields': ('embedding', 'created_at'),
            'classes': ('collapse',), # إخفاء هذا القسم افتراضياً لعدم الإزعاج
        }),
    )

    # +++++++ السطر المهم الذي كان ناقصاً +++++++
    actions = [update_embeddings] 
    # +++++++++++++++++++++++++++++++++++++++++++

# ==========================================
# 2. تخصيص واجهة الطلاب
# ==========================================
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'major', 'get_email')
    search_fields = ('user__username', 'student_id', 'user__email')
    list_filter = ('major',)

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'البريد الإلكتروني'

# ==========================================
# 3. تخصيص واجهة الإعارات (Transactions)
# ==========================================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'status', 'request_date', 'due_date', 'is_overdue')
    list_filter = ('status', 'request_date')
    search_fields = ('book__title', 'student__user__username')
    
    # إضافة إجراءات سريعة للموافقة أو الإرجاع من القائمة
    actions = ['approve_requests', 'mark_returned', 'reject_requests']

    @admin.action(description='✅ الموافقة على الطلبات المختارة')
    def approve_requests(self, request, queryset):
        updated_count = 0
        for trans in queryset:
            if trans.status == 'pending':
                trans.status = 'active'
                trans.save() # سيقوم المودل بضبط التواريخ تلقائياً
                updated_count += 1
        self.message_user(request, f"تمت الموافقة على {updated_count} طلب بنجاح.")

    @admin.action(description='↩️ تسجيل إرجاع الكتب المحددة')
    def mark_returned(self, request, queryset):
        updated_count = 0
        for trans in queryset:
            if trans.status == 'active':
                trans.status = 'returned'
                trans.save()
                updated_count += 1
        self.message_user(request, f"تم تسجيل إرجاع {updated_count} كتاب.")

    @admin.action(description='❌ رفض الطلبات المحددة')
    def reject_requests(self, request, queryset):
        rows_updated = queryset.update(status='rejected')
        self.message_user(request, f"تم رفض {rows_updated} طلب.")

# ==========================================
# 4. سجلات البحث (Gap Analysis)
# ==========================================
@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'user', 'result_count', 'timestamp')
    list_filter = ('timestamp', 'result_count')
    search_fields = ('query_text',)