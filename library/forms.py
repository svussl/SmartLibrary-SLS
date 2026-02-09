from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="كلمة المرور")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="تأكيد كلمة المرور")
    
    # حقول الطالب الإضافية
    student_id = forms.CharField(max_length=20, label="الرقم الجامعي")
    
    # هنا نستخدم القائمة المنسدلة المعرفة في الموديل
    major = forms.ChoiceField(choices=StudentProfile.MAJOR_CHOICES, label="التخصص الدراسي")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        pass1 = cleaned_data.get("password")
        pass2 = cleaned_data.get("confirm_password")
        if pass1 != pass2:
            raise forms.ValidationError("كلمات المرور غير متطابقة")
        return cleaned_data