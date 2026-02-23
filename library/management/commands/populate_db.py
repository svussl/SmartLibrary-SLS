import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from library.models import Book, StudentProfile, Transaction

class Command(BaseCommand):
    help = 'مسح قاعدة البيانات وملؤها بـ 15 طالب، 400 كتاب، و100 إعارة بقاعدة (80% من التخصص - 20% من تخصصات أخرى)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('⚠️ جاري مسح قاعدة البيانات بالكامل...'))

        # ==========================
        # 1. حذف البيانات القديمة
        # ==========================
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
        # 3. إنشاء 15 حساب طالب (كما هي)
        # ==========================
        first_names = ['أحمد', 'محمد', 'سارة', 'فاطمة', 'علي', 'عمر', 'نور', 'خالد', 'منى', 'يوسف', 'ليلى', 'حسن', 'مريم', 'إبراهيم', 'زينب']
        last_names = ['دالاتي', 'سلمان', 'الأسد', 'الحمصي', 'الشامي', 'العلي', 'يوسف', 'طاهر', 'نجار', 'حداد', 'خطيب', 'محمود', 'سعيد', 'عبدالله', 'عثمان']
        
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
        # 4. تجميع وإنشاء 400 كتاب (أساسي + مولّد آلياً)
        # ==========================
        self.stdout.write('📚 جاري إنشاء 400 كتاب تغطي كافة التخصصات...')
        
        # قائمة مبدئية مصغرة (لتجنب تضخم الكود، سنولد الباقي برمجياً)
        base_books_data = [
            # IT
            {"title": "Clean Code", "cat": "Programming"}, {"title": "Deep Learning", "cat": "AI"},
            {"title": "Computer Networking", "cat": "Networking"}, {"title": "Hacking Art", "cat": "CyberSecurity"},
            # Medical
            {"title": "Gray's Anatomy", "cat": "Medical"}, {"title": "Pharmacology Basics", "cat": "Pharmacy"},
            {"title": "Dental Materials", "cat": "Dentistry"}, {"title": "Fundamentals of Nursing", "cat": "Nursing"},
            # Engineering
            {"title": "Structural Analysis", "cat": "CivilEng"}, {"title": "Modern Architecture", "cat": "Arch"},
            {"title": "Electric Machinery", "cat": "Electrical"}, {"title": "Engineering Mechanics", "cat": "Engineering"},
            # Humanities & Others
            {"title": "Criminal Law", "cat": "Law"}, {"title": "Microeconomics", "cat": "Economics"},
            {"title": "Introduction to Psychology", "cat": "Psychology"}, {"title": "Sapiens", "cat": "History"},
            {"title": "Calculus", "cat": "Math"}, {"title": "General Chemistry", "cat": "Chemistry"}
        ]

        categories = [
            "Programming", "AI", "CyberSecurity", "Networking", 
            "Medical", "Pharmacy", "Dentistry", "Nursing", 
            "Engineering", "CivilEng", "Arch", "Electrical", 
            "Law", "Economics", "Psychology", "Sociology", 
            "History", "Geography", "Religion", "Math", 
            "Physics", "Chemistry", "Biology", "Arts", "Literature", "General"
        ]

        templates = [
            "Advanced {cat} Studies - Vol {vol}",
            "Principles of {cat} Edition {vol}",
            "The Complete Guide to {cat}",
            "Modern {cat} Practices",
            "Introduction to Applied {cat}",
            "{cat} for Beginners",
            "Research Methods in {cat}"
        ]

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
                tags=f"{b['cat']}, Academic"
            )
            created_books.append(book)

        # توليد الباقي حتى نصل لـ 400 كتاب بالضبط
        books_needed = 400 - len(created_books)
        for i in range(books_needed):
            cat = random.choice(categories)
            template = random.choice(templates)
            title = template.format(cat=cat, vol=random.randint(1, 10))
            
            fake_isbn = f"978{random.randint(1000000000, 9999999999)}"
            book = Book.objects.create(
                title=title,
                author=f"Author {random.randint(100, 999)}",
                category=cat,
                isbn=fake_isbn,
                description=f"كتاب أكاديمي شامل يغطي جوانب {cat}.",
                total_copies=random.randint(2, 6),
                available_copies=random.randint(1, 4),
                tags=f"{cat}, Reference"
            )
            created_books.append(book)

        self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {len(created_books)} كتاب بنجاح.'))

        # ==========================
        # 5. تصنيف المجالات لتطبيق قاعدة الـ 80/20
        # ==========================
        # تقسيم التصنيفات إلى "كليات" واسعة
        MAJOR_GROUPS = {
            'IT': ["Programming", "AI", "CyberSecurity", "Networking"],
            'Medicine': ["Medical", "Pharmacy", "Dentistry", "Nursing"],
            'Engineering': ["Engineering", "CivilEng", "Arch", "Electrical"],
            'Science': ["Math", "Physics", "Chemistry", "Biology"],
            'Humanities': ["Law", "Economics", "Psychology", "Sociology", "History", "Geography", "Religion", "Arts", "Literature", "General"]
        }

        # ربط كل طالب بكلية/مجال معين ليكون هو اختصاصه الرئيسي
        student_focus = {}
        group_keys = list(MAJOR_GROUPS.keys())
        for i, student in enumerate(students):
            focus_group = group_keys[i % len(group_keys)] # توزيع الطلاب على الكليات بالتساوي
            student_focus[student.id] = MAJOR_GROUPS[focus_group]

        # ==========================
        # 6. إنشاء 100 إعارة (80% من الاختصاص، 20% من خارجه)
        # ==========================
        self.stdout.write('🔄 جاري إنشاء 100 إعارة وتطبيق قاعدة الـ 80/20...')
        
        statuses = ['active', 'returned', 'pending', 'returned', 'active', 'rejected', 'overdue']
        
        for _ in range(100): 
            student = random.choice(students)
            student_core_cats = student_focus[student.id]
            
            # تطبيق قاعدة الاحتمالات 80/20
            if random.random() < 0.80:
                # 80%: يختار كتاب من اختصاصه
                candidate_books = [b for b in created_books if b.category in student_core_cats]
            else:
                # 20%: يختار كتاب من خارج اختصاصه
                candidate_books = [b for b in created_books if b.category not in student_core_cats]
            
            # في حال لم يجد كتاباً (احتياط برمجياً)، يختار من أي كتاب
            if not candidate_books:
                candidate_books = created_books

            book = random.choice(candidate_books)
            status = random.choice(statuses)
            
            days_ago = random.randint(1, 90)
            request_date = timezone.now() - timezone.timedelta(days=days_ago)
            
            borrow_date = None
            return_date = None
            due_date = None
            
            if status in ['active', 'returned', 'overdue']:
                borrow_date = request_date + timezone.timedelta(days=1)
                due_date = borrow_date + timezone.timedelta(days=14)

            if status == 'returned':
                return_date = borrow_date + timezone.timedelta(days=random.randint(3, 12))
            
            if status == 'overdue':
                status = 'active'
                request_date = timezone.now() - timezone.timedelta(days=40)
                borrow_date = request_date + timezone.timedelta(days=1)
                due_date = borrow_date + timezone.timedelta(days=14) 

            Transaction.objects.create(
                book=book,
                student=student,
                status=status,
                request_date=request_date,
                borrow_date=borrow_date,
                return_date=return_date,
                due_date=due_date
            )

        self.stdout.write(self.style.SUCCESS('✅ تم إنشاء 100 إعارة بنجاح.'))
        self.stdout.write(self.style.SUCCESS(f'🎉🎉 تمت التهيئة: 400 كتاب، 15 طالب، 100 إعارة (بنسبة 80/20 للاختصاص)!'))