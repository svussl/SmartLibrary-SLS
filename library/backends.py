from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import StudentProfile

class StudentIDBackend(ModelBackend):
    """
    مخصص للسماح للطلاب بتسجيل الدخول باستخدام الرقم الجامعي.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 1. محاولة البحث عن المستخدم عن طريق الرقم الجامعي
        try:
            # نبحث في جدول الطلاب عن هذا الرقم
            profile = StudentProfile.objects.get(student_id=username)
            user = profile.user
            
            # إذا وجدنا الطالب، نتحقق من كلمة المرور
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except StudentProfile.DoesNotExist:
            # إذا لم نجد طالباً بهذا الرقم، لا نفعل شيئاً ونترك النظام يجرب الطرق الأخرى
            pass
            
        return None