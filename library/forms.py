from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import StudentProfile

# 1. نموذج التسجيل (كما هو تماماً)
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="كلمة المرور")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="تأكيد كلمة المرور")
    student_id = forms.CharField(max_length=20, label="الرقم الجامعي")
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

# 2. نموذج تسجيل الدخول المخصص (جديد)
class StudentLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="الرقم الجامعي / اسم المستخدم",
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'أدخل الرقم الجامعي هنا'
        })
    )
    password = forms.CharField(
        label="كلمة المرور",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'كلمة المرور'
        })
    )