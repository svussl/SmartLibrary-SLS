#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# جمع الملفات الساكنة (CSS/JS)
python manage.py collectstatic --no-input

# تطبيق تعديلات قاعدة البيانات
python manage.py migrate