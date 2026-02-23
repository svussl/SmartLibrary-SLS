import os
from pathlib import Path

# المسار الأساسي للمشروع
BASE_DIR = Path(__file__).resolve().parent.parent

# إعدادات الأمان (يجب تغيير مفتاح السر في بيئة الإنتاج)
SECRET_KEY = 'django-insecure-smart-library-system-key-replace-this'

# وضع التصحيح (Debug) - تفعيله أثناء التطوير فقط
DEBUG = True

ALLOWED_HOSTS = []

# التطبيقات المثبتة
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # تطبيق المكتبة الذكي
    'library',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sls_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sls_project.wsgi.application'

# إعدادات قاعدة البيانات (SQLite هي الافتراضية وسهلة للبدء)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# التحقق من كلمة المرور
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# اللغة والوقت
LANGUAGE_CODE = 'ar-sy' # تعيين اللغة للعربية (سوريا)
TIME_ZONE = 'Asia/Damascus' # توقيت دمشق
USE_I18N = True
USE_TZ = True

# إعدادات الملفات الساكنة (CSS, JS, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# إعداد الحقول التلقائية
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# إعدادات الوسائط (لصور أغلفة الكتب مثلاً)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# إعدادات توجيه تسجيل الدخول
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'


AUTHENTICATION_BACKENDS = [
    # 1. الأولوية للبحث عن طريق الرقم الجامعي (للطلاب)
    'library.backends.StudentIDBackend',
    
    # 2. ثم البحث عن طريق اسم المستخدم العادي (للمشرفين Admin)
    'django.contrib.auth.backends.ModelBackend',
]

CSRF_TRUSTED_ORIGINS = [
    'https://localhost:8000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]