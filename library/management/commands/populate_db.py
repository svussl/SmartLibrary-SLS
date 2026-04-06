import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from library.models import Book, StudentProfile, Transaction, PhysicalVisit, Notification

class Command(BaseCommand):
    help = 'مسح قاعدة البيانات وملؤها بـ 15 طالب، 400 كتاب، 100 إعارة، 200 زيارة واقعية، وتنبيهات'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('⚠️ جاري مسح قاعدة البيانات بالكامل...'))

        # ==========================
        # 1. حذف البيانات القديمة (تمت إضافة الجداول الجديدة)
        # ==========================
        PhysicalVisit.objects.all().delete()
        Notification.objects.all().delete()
        Transaction.objects.all().delete()
        StudentProfile.objects.all().delete()
        Book.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('✅ تم حذف البيانات القديمة.'))

        # ==========================
        # 2. إنشاء حساب المدير (Superuser)
        # ==========================
        self.stdout.write('👤 جاري إنشاء حساب المدير (admin)...')
        User.objects.create_superuser('admin', 'admin@library.com', 'admin')
        self.stdout.write(self.style.SUCCESS('✅ تم إنشاء المدير: admin / admin'))

        # ==========================
        # 3. إنشاء 15 حساب طالب
        # ==========================
        first_names = ['أحمد', 'محمد', 'سارة', 'فاطمة', 'علي', 'عمر', 'نور', 'خالد', 'منى', 'يوسف', 'ليلى', 'حسن', 'مريم', 'إبراهيم', 'زينب']
        last_names = ['دالاتي', 'سلمان', 'الأسعد', 'الحمصي', 'الشامي', 'العلي', 'يوسف', 'طاهر', 'نجار', 'حداد', 'خطيب', 'محمود', 'سعيد', 'عبدالله', 'عثمان']
        
        majors_pool = [c[0] for c in StudentProfile.MAJOR_CHOICES] 

        self.stdout.write('🎓 جاري إنشاء 15 حساب طالب...')
        students = []
        for i in range(15):
            f_name = first_names[i]
            l_name = last_names[i]
            username = f"student_{i+1}"
            email = f"student{i+1}@svu.edu.sy"
            
            user = User.objects.create_user(username=username, email=email, password='password123', first_name=f_name, last_name=l_name)
            major = majors_pool[i % len(majors_pool)]
            student_id = str(2024000 + i + 1)

            profile = StudentProfile.objects.create(
                user=user,
                student_id=student_id,
                major=major
            )
            students.append(profile)
        
        self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {len(students)} طالب بنجاح.'))

        # ==========================
        # 4. تجميع وإنشاء 400 كتاب (مع الحقول الجديدة)
        # ==========================
        self.stdout.write('📚 جاري إنشاء 400 كتاب تغطي كافة التخصصات (مع الناشر والسنة)...')
        
        base_books_data = [
            {"title": "Clean Code", "cat": "Programming"}, {"title": "Deep Learning", "cat": "AI"},
            {"title": "Computer Networking", "cat": "Networking"}, {"title": "Hacking Art", "cat": "CyberSecurity"},
            {"title": "Gray's Anatomy", "cat": "Medical"}, {"title": "Pharmacology Basics", "cat": "Pharmacy"},
            {"title": "Dental Materials", "cat": "Dentistry"}, {"title": "Fundamentals of Nursing", "cat": "Nursing"},
            {"title": "Structural Analysis", "cat": "CivilEng"}, {"title": "Modern Architecture", "cat": "Arch"},
            {"title": "Electric Machinery", "cat": "Electrical"}, {"title": "Engineering Mechanics", "cat": "Engineering"},
            {"title": "Criminal Law", "cat": "Law"}, {"title": "Microeconomics", "cat": "Economics"},
            {"title": "Introduction to Psychology", "cat": "Psychology"}, {"title": "Sapiens", "cat": "History"},
            {"title": "Calculus", "cat": "Math"}, {"title": "General Chemistry", "cat": "Chemistry"}
        ]

        categories = [
            "Programming", "AI", "CyberSecurity", "Networking", "Medical", "Pharmacy", 
            "Dentistry", "Nursing", "Engineering", "CivilEng", "Arch", "Electrical", 
            "Law", "Economics", "Psychology", "Sociology", "History", "Geography", 
            "Religion", "Math", "Physics", "Chemistry", "Biology", "Arts", "Literature", "General"
        ]

        templates = [
            "Advanced {cat} Studies - Vol {vol}", "Principles of {cat} Edition {vol}",
            "The Complete Guide to {cat}", "Modern {cat} Practices",
            "Introduction to Applied {cat}", "{cat} for Beginners", "Research Methods in {cat}"
        ]

        # قوائم الخيارات للحقول الجديدة
        publishers = ['دار النشر الجامعية', 'O\'Reilly', 'Springer', 'Pearson', 'McGraw-Hill', 'دار المعرفة', 'مكتبة العبيكان']
        languages = ['العربية', 'English']
        book_types = ['printed', 'ebook']

        created_books = []
        
        # إنشاء الكتب الأساسية
        for b in base_books_data:
            fake_isbn = f"978{random.randint(1000000000, 9999999999)}"
            book = Book.objects.create(
                title=b['title'],
                author="Expert Author",
                category=b['cat'],
                isbn=fake_isbn,
                description=f"كتاب متخصص في مجال {b['cat']}",
                total_copies=random.randint(3, 8),
                available_copies=random.randint(1, 5),
                tags=f"{b['cat']}, Academic",
                # إضافات جديدة
                publisher=random.choice(publishers),
                publication_year=random.randint(2000, 2026),
                language=random.choice(languages),
                book_type=random.choice(book_types)
            )
            created_books.append(book)

        # توليد الباقي
        books_needed = 400 - len(created_books)
        for i in range(books_needed):
            cat = random.choice(categories)
            title = random.choice(templates).format(cat=cat, vol=random.randint(1, 10))
            fake_isbn = f"978{random.randint(1000000000, 9999999999)}"
            
            book = Book.objects.create(
                title=title,
                author=f"Author {random.randint(100, 999)}",
                category=cat,
                isbn=fake_isbn,
                description=f"كتاب أكاديمي شامل يغطي جوانب {cat}.",
                total_copies=random.randint(2, 6),
                available_copies=random.randint(1, 4),
                tags=f"{cat}, Reference",
                # إضافات جديدة
                publisher=random.choice(publishers),
                publication_year=random.randint(1995, 2026),
                language=random.choice(languages),
                book_type=random.choice(book_types)
            )
            created_books.append(book)

        self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {len(created_books)} كتاب بنجاح.'))

        # ==========================
        # 5. إنشاء الإعارات والتنبيهات
        # ==========================
        self.stdout.write('🔄 جاري إنشاء 100 إعارة وتنبيهات مرافقة...')
        
        MAJOR_GROUPS = {
            'IT': ["Programming", "AI", "CyberSecurity", "Networking"],
            'Medicine': ["Medical", "Pharmacy", "Dentistry", "Nursing"],
            'Engineering': ["Engineering", "CivilEng", "Arch", "Electrical"],
            'Science': ["Math", "Physics", "Chemistry", "Biology"],
            'Humanities': ["Law", "Economics", "Psychology", "Sociology", "History", "Geography", "Religion", "Arts", "Literature", "General"]
        }

        student_focus = {}
        group_keys = list(MAJOR_GROUPS.keys())
        for i, student in enumerate(students):
            student_focus[student.id] = MAJOR_GROUPS[group_keys[i % len(group_keys)]]

        statuses = ['active', 'returned', 'pending', 'returned', 'active', 'rejected']
        
        for _ in range(100): 
            student = random.choice(students)
            student_core_cats = student_focus[student.id]
            
            candidate_books = [b for b in created_books if b.category in student_core_cats] if random.random() < 0.80 else [b for b in created_books if b.category not in student_core_cats]
            candidate_books = candidate_books or created_books
            book = random.choice(candidate_books)
            status = random.choice(statuses)
            
            days_ago = random.randint(1, 90)
            request_date = timezone.now() - timedelta(days=days_ago)
            borrow_date = request_date + timedelta(days=1) if status in ['active', 'returned'] else None
            due_date = borrow_date + timedelta(days=14) if borrow_date else None
            return_date = borrow_date + timedelta(days=random.randint(3, 12)) if status == 'returned' else None

            Transaction.objects.create(
                book=book, student=student, status=status, request_date=request_date,
                borrow_date=borrow_date, return_date=return_date, due_date=due_date
            )

        # إنشاء تنبيه ترحيبي لكل طالب
        for student in students:
            Notification.objects.create(
                student=student,
                message=f"مرحباً بك {student.user.first_name} في النظام الجديد للمكتبة الذكية. نرجو لك تجربة ممتعة!",
                is_read=random.choice([True, False])
            )

        # ==========================
        # 6. إنشاء سجلات المكتبة الواقعية (Physical Visits)
        # ==========================
        self.stdout.write('🏢 جاري إنشاء 200 سجل استخدام للمكتبة الواقعية...')
        activities = ['internet', 'reading', 'studying']
        
        for _ in range(200):
            student = random.choice(students)
            # 15% من الزيارات نتركها نشطة (بدون Check-out) لكي تظهر في المتواجدين حالياً
            is_active_now = random.random() < 0.15 
            
            if is_active_now:
                check_in = timezone.now() - timedelta(minutes=random.randint(10, 150))
                check_out = None
            else:
                days_ago = random.randint(1, 30)
                # توليد أوقات ذروة منطقية (بين الساعة 8 صباحاً و 4 عصراً)
                hour_of_day = random.randint(8, 16) 
                check_in = timezone.now() - timedelta(days=days_ago)
                check_in = check_in.replace(hour=hour_of_day, minute=random.randint(0, 59))
                # مدة البقاء بين 30 دقيقة و 4 ساعات
                check_out = check_in + timedelta(minutes=random.randint(30, 240))

            PhysicalVisit.objects.create(
                student=student,
                activity=random.choice(activities),
                check_in=check_in,
                check_out=check_out
            )

        self.stdout.write(self.style.SUCCESS('✅ تم إنشاء زيارات المكتبة والتنبيهات.'))
        self.stdout.write(self.style.SUCCESS(f'🎉🎉 تمت التهيئة بالكامل! يمكنك الآن تشغيل السيرفر والاطلاع على التحليلات.'))