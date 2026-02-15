import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from library.models import Book, StudentProfile, Transaction

class Command(BaseCommand):
    help = 'مسح قاعدة البيانات وملؤها ببيانات اختبارية (15 مستخدم، 100 كتاب، وتخصصات متنوعة)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('⚠️ جاري مسح قاعدة البيانات بالكامل...'))

        # 1. حذف البيانات القديمة
        Transaction.objects.all().delete()
        StudentProfile.objects.all().delete()
        Book.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('✅ تم حذف البيانات القديمة.'))

        # 2. إنشاء حساب المدير (Superuser)
        self.stdout.write('👤 جاري إنشاء حساب المدير (admin)...')
        User.objects.create_superuser('admin', 'admin@library.com', 'admin')
        self.stdout.write(self.style.SUCCESS('✅ تم إنشاء المدير: admin / admin'))

        # 3. بيانات للتوليد
        first_names = ['أحمد', 'محمد', 'سارة', 'فاطمة', 'علي', 'عمر', 'نور', 'خالد', 'منى', 'يوسف', 'ليلى', 'حسن', 'مريم', 'إبراهيم', 'زينب']
        last_names = ['دالاتي', 'سلمان', 'الأسد', 'الحمصي', 'الشامي', 'العلي', 'يوسف', 'طاهر', 'نجار', 'حداد', 'خطيب', 'محمود', 'سعيد', 'عبدالله', 'عثمان']
        
        majors_pool = [c[0] for c in StudentProfile.MAJOR_CHOICES] 

        # 4. إنشاء 15 طالب
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

        # 5. إنشاء الكتب (قائمة موسعة لتصل إلى 100 كتاب تقريباً)
        self.stdout.write('📚 جاري إنشاء 100 كتاب لتغطية كافة التصنيفات...')
        
        books_data = [
            # --- Programming & CS ---
            {"title": "Clean Code", "author": "Robert C. Martin", "cat": "Programming", "desc": "دليل لبرمجة نظيفة واحترافية."},
            {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen", "cat": "Programming", "desc": "المرجع الشامل في الخوارزميات."},
            {"title": "The Pragmatic Programmer", "author": "Andrew Hunt", "cat": "Programming", "desc": "رحلة من مبرمج عادي إلى مبرمج محترف."},
            {"title": "Design Patterns", "author": "Erich Gamma", "cat": "Programming", "desc": "أنماط التصميم القابلة لإعادة الاستخدام."},
            {"title": "You Don't Know JS", "author": "Kyle Simpson", "cat": "Programming", "desc": "تعمق في خبايا لغة جافاسكربت."},
            {"title": "Python Crash Course", "author": "Eric Matthes", "cat": "Programming", "desc": "مقدمة عملية وسريعة لتعلم بايثون."},
            {"title": "Head First Java", "author": "Kathy Sierra", "cat": "Programming", "desc": "تعلم الجافا بطريقة تفاعلية."},
            {"title": "Refactoring", "author": "Martin Fowler", "cat": "Programming", "desc": "تحسين تصميم الكود الحالي."},
            
            # --- AI & Data Science ---
            {"title": "Artificial Intelligence: A Modern Approach", "author": "Stuart Russell", "cat": "AI", "desc": "الكتاب الأساسي في دراسة الذكاء الاصطناعي."},
            {"title": "Deep Learning", "author": "Ian Goodfellow", "cat": "AI", "desc": "شرح عميق للشبكات العصبية."},
            {"title": "Hands-On Machine Learning", "author": "Aurélien Géron", "cat": "AI", "desc": "تعلم الآلة باستخدام Scikit-Learn و TensorFlow."},
            {"title": "Pattern Recognition and Machine Learning", "author": "Christopher Bishop", "cat": "AI", "desc": "أساسيات التعرف على الأنماط."},
            {"title": "Data Science for Business", "author": "Foster Provost", "cat": "AI", "desc": "ما يجب أن تعرفه عن علم البيانات."},
            {"title": "The Hundred-Page Machine Learning Book", "author": "Andriy Burkov", "cat": "AI", "desc": "ملخص شامل لتعلم الآلة."},
            {"title": "Superintelligence", "author": "Nick Bostrom", "cat": "AI", "desc": "المسارات، المخاطر، والاستراتيجيات."},
            {"title": "Life 3.0", "author": "Max Tegmark", "cat": "AI", "desc": "كيف سيغير الذكاء الاصطناعي حياتنا."},

            # --- CyberSecurity & Networking ---
            {"title": "Hacking: The Art of Exploitation", "author": "Jon Erickson", "cat": "CyberSecurity", "desc": "فن الاختراق وأمن المعلومات."},
            {"title": "The Web Application Hacker's Handbook", "author": "Dafydd Stuttard", "cat": "CyberSecurity", "desc": "اكتشاف واستغلال ثغرات الويب."},
            {"title": "Metasploit: The Penetration Tester's Guide", "author": "David Kennedy", "cat": "CyberSecurity", "desc": "دليل اختبار الاختراق."},
            {"title": "Computer Networking: A Top-Down Approach", "author": "Kurose & Ross", "cat": "Networking", "desc": "أساسيات الشبكات والبروتوكولات."},
            {"title": "TCP/IP Illustrated", "author": "W. Richard Stevens", "cat": "Networking", "desc": "شرح بروتوكولات الشبكة بالتفصيل."},
            {"title": "Network Security Essentials", "author": "William Stallings", "cat": "Networking", "desc": "تطبيقات ومعايير أمن الشبكات."},
            {"title": "Social Engineering: The Science of Human Hacking", "author": "Christopher Hadnagy", "cat": "CyberSecurity", "desc": "فن الهندسة الاجتماعية."},
            {"title": "Practical Malware Analysis", "author": "Michael Sikorski", "cat": "CyberSecurity", "desc": "دليل عملي لتحليل البرمجيات الخبيثة."},

            # --- Medical & Pharmacy ---
            {"title": "Gray's Anatomy", "author": "Henry Gray", "cat": "Medical", "desc": "المرجع الأشهر في التشريح البشري."},
            {"title": "Harrison's Principles of Internal Medicine", "author": "J. Larry Jameson", "cat": "Medical", "desc": "مبادئ الطب الباطني."},
            {"title": "Guyton and Hall Textbook of Medical Physiology", "author": "John E. Hall", "cat": "Medical", "desc": "فسيولوجيا طبية شاملة."},
            {"title": "Pharmacology", "author": "Karen Whalen", "cat": "Pharmacy", "desc": "علم الأدوية وتطبيقاته."},
            {"title": "Basic and Clinical Pharmacology", "author": "Bertram Katzung", "cat": "Pharmacy", "desc": "الأساسيات في علم الأدوية السريري."},
            {"title": "Pharmaceutical Calculations", "author": "Howard C. Ansel", "cat": "Pharmacy", "desc": "الحسابات الصيدلانية."},
            {"title": "Robbins Basic Pathology", "author": "Vinay Kumar", "cat": "Medical", "desc": "أساسيات علم الأمراض."},
            {"title": "Netter's Atlas of Human Anatomy", "author": "Frank H. Netter", "cat": "Medical", "desc": "أطلس تشريح الإنسان."},

            # --- Dentistry & Nursing ---
            {"title": "Dental Materials", "author": "John Powers", "cat": "Dentistry", "desc": "خصائص وتطبيقات مواد طب الأسنان."},
            {"title": "Oral and Maxillofacial Surgery", "author": "Lars Andersson", "cat": "Dentistry", "desc": "جراحة الفم والوجه والفكين."},
            {"title": "Ten Cate's Oral Histology", "author": "Antonio Nanci", "cat": "Dentistry", "desc": "علم الأنسجة الفموية."},
            {"title": "Fundamentals of Nursing", "author": "Patricia A. Potter", "cat": "Nursing", "desc": "أساسيات التمريض والممارسة."},
            {"title": "Medical-Surgical Nursing", "author": "Sharon L. Lewis", "cat": "Nursing", "desc": "تمريض باطني جراحي."},
            {"title": "Nursing Diagnosis Handbook", "author": "Betty J. Ackley", "cat": "Nursing", "desc": "دليل التشخيص التمريضي."},

            # --- Engineering (Civil, Arch, Electrical) ---
            {"title": "Shigley's Mechanical Engineering Design", "author": "Richard Budynas", "cat": "Engineering", "desc": "تصميم هندسي ميكانيكي."},
            {"title": "Engineering Mechanics: Statics", "author": "Russell Hibbeler", "cat": "Engineering", "desc": "ميكانيكا هندسية: سكون."},
            {"title": "Civil Engineering Materials", "author": "Somayaji", "cat": "CivilEng", "desc": "مواد الهندسة المدنية والإنشاءات."},
            {"title": "Structural Analysis", "author": "Russell Hibbeler", "cat": "CivilEng", "desc": "تحليل إنشائي."},
            {"title": "Modern Architecture", "author": "Kenneth Frampton", "cat": "Arch", "desc": "تاريخ العمارة الحديثة."},
            {"title": "The Architecture of Happiness", "author": "Alain de Botton", "cat": "Arch", "desc": "كيف تؤثر المباني على مشاعرنا."},
            {"title": "Electric Machinery Fundamentals", "author": "Stephen J. Chapman", "cat": "Electrical", "desc": "أساسيات الآلات الكهربائية."},
            {"title": "Microelectronic Circuits", "author": "Adel S. Sedra", "cat": "Electrical", "desc": "الدوائر الإلكترونية الدقيقة."},
            {"title": "Power System Analysis", "author": "John Grainger", "cat": "Electrical", "desc": "تحليل أنظمة القوى الكهربائية."},

            # --- Law & Economics ---
            {"title": "The Law of Contract", "author": "G.H. Treitel", "cat": "Law", "desc": "قانون العقود والالتزامات."},
            {"title": "Criminal Law", "author": "Jonathan Herring", "cat": "Law", "desc": "القانون الجنائي: النص والقضايا."},
            {"title": "International Law", "author": "Malcolm Shaw", "cat": "Law", "desc": "القانون الدولي العام."},
            {"title": "Understanding Jurisprudence", "author": "Raymond Wacks", "cat": "Law", "desc": "فهم الفقه القانوني."},
            {"title": "Economics", "author": "Paul Samuelson", "cat": "Economics", "desc": "مبادئ الاقتصاد الجزئي والكلي."},
            {"title": "Capital in the Twenty-First Century", "author": "Thomas Piketty", "cat": "Economics", "desc": "رأس المال في القرن الحادي والعشرين."},
            {"title": "The Wealth of Nations", "author": "Adam Smith", "cat": "Economics", "desc": "ثروة الأمم."},
            {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman", "cat": "Economics", "desc": "التفكير السريع والبطيء (اقتصاد سلوكي)."},

            # --- Psychology & Sociology ---
            {"title": "Introduction to Psychology", "author": "James Kalat", "cat": "Psychology", "desc": "مقدمة في علم النفس والسلوك."},
            {"title": "The Man Who Mistook His Wife for a Hat", "author": "Oliver Sacks", "cat": "Psychology", "desc": "قصص إكلينيكية في علم النفس العصبي."},
            {"title": "Influence: The Psychology of Persuasion", "author": "Robert Cialdini", "cat": "Psychology", "desc": "سيكولوجية الإقناع."},
            {"title": "Man's Search for Meaning", "author": "Viktor Frankl", "cat": "Psychology", "desc": "الإنسان والبحث عن المعنى."},
            {"title": "Sociology: A Down-to-Earth Approach", "author": "James Henslin", "cat": "Sociology", "desc": "علم الاجتماع وتطبيقاته الحياتية."},
            {"title": "The Presentation of Self in Everyday Life", "author": "Erving Goffman", "cat": "Sociology", "desc": "تقديم الذات في الحياة اليومية."},
            {"title": "Suicide", "author": "Émile Durkheim", "cat": "Sociology", "desc": "دراسة اجتماعية حول الانتحار."},
            {"title": "Liquid Modernity", "author": "Zygmunt Bauman", "cat": "Sociology", "desc": "الحداثة السائلة."},

            # --- History, Geography, Religion ---
            {"title": "A Brief History of Time", "author": "Stephen Hawking", "cat": "Physics", "desc": "تاريخ موجز للزمن."},
            {"title": "Sapiens: A Brief History of Humankind", "author": "Yuval Noah Harari", "cat": "History", "desc": "تاريخ موجز للبشرية."},
            {"title": "Guns, Germs, and Steel", "author": "Jared Diamond", "cat": "History", "desc": "مصير المجتمعات البشرية."},
            {"title": "The Silk Roads", "author": "Peter Frankopan", "cat": "History", "desc": "تاريخ جديد للعالم."},
            {"title": "Prisoners of Geography", "author": "Tim Marshall", "cat": "Geography", "desc": "كيف تشكل الخرائط السياسة العالمية."},
            {"title": "Physical Geography", "author": "James Peterson", "cat": "Geography", "desc": "الجغرافيا الطبيعية."},
            {"title": "The History of God", "author": "Karen Armstrong", "cat": "Religion", "desc": "تاريخ الألوهية في الديانات الثلاث."},
            {"title": "The World's Religions", "author": "Huston Smith", "cat": "Religion", "desc": "أديان العالم."},
            {"title": "Rethinking Islam", "author": "Mohammed Arkoun", "cat": "Religion", "desc": "نحو قراءة جديدة للإسلام."},

            # --- Science (Math, Physics, Chemistry, Biology) ---
            {"title": "Calculus", "author": "James Stewart", "cat": "Math", "desc": "أساسيات التفاضل والتكامل."},
            {"title": "Linear Algebra Done Right", "author": "Sheldon Axler", "cat": "Math", "desc": "الجبر الخطي."},
            {"title": "The Feynman Lectures on Physics", "author": "Richard Feynman", "cat": "Physics", "desc": "محاضرات فاينمان في الفيزياء."},
            {"title": "Cosmos", "author": "Carl Sagan", "cat": "Physics", "desc": "الكون."},
            {"title": "General Chemistry", "author": "Linus Pauling", "cat": "Chemistry", "desc": "الكيمياء العامة."},
            {"title": "Organic Chemistry", "author": "Paula Bruice", "cat": "Chemistry", "desc": "الكيمياء العضوية."},
            {"title": "Biology", "author": "Neil Campbell", "cat": "Biology", "desc": "علم الأحياء الشامل."},
            {"title": "The Selfish Gene", "author": "Richard Dawkins", "cat": "Biology", "desc": "الجين الأناني."},
            {"title": "Molecular Biology of the Cell", "author": "Bruce Alberts", "cat": "Biology", "desc": "البيولوجيا الجزيئية للخلية."},
            {"title": "What is Life?", "author": "Erwin Schrödinger", "cat": "Physics", "desc": "الجانب الفيزيائي للخلية الحية."},

            # --- Arts & Literature ---
            {"title": "The Story of Art", "author": "E.H. Gombrich", "cat": "Arts", "desc": "قصة الفنون عبر العصور."},
            {"title": "Ways of Seeing", "author": "John Berger", "cat": "Arts", "desc": "طرق الرؤية والنقد الفني."},
            {"title": "Interaction of Color", "author": "Josef Albers", "cat": "Arts", "desc": "تفاعل الألوان."},
            {"title": "The Prophet", "author": "Kahlil Gibran", "cat": "Literature", "desc": "رواية النبي لجبران خليل جبران."},
            {"title": "1984", "author": "George Orwell", "cat": "Literature", "desc": "رواية 1984."},
            {"title": "To Kill a Mockingbird", "author": "Harper Lee", "cat": "Literature", "desc": "لا تقتل عصفوراً ساخراً."},
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "cat": "Literature", "desc": "غاتسبي العظيم."},
            {"title": "Crime and Punishment", "author": "Fyodor Dostoevsky", "cat": "Literature", "desc": "الجريمة والعقاب."},
            {"title": "One Hundred Years of Solitude", "author": "Gabriel García Márquez", "cat": "Literature", "desc": "مائة عام من العزلة."},
            {"title": "In Search of Lost Time", "author": "Marcel Proust", "cat": "Literature", "desc": "البحث عن الزمن المفقود."},

            # --- General & Arabic ---
            {"title": "مقدمة ابن خلدون", "author": "ابن خلدون", "cat": "History", "desc": "مقدمة في التاريخ وعلم الاجتماع."},
            {"title": "ألف ليلة وليلة", "author": "مجهول", "cat": "Literature", "desc": "حكايات تراثية."},
            {"title": "عبقرية الصديق", "author": "عباس محمود العقاد", "cat": "History", "desc": "دراسة لشخصية أبي بكر الصديق."},
            {"title": "البداية والنهاية", "author": "ابن كثير", "cat": "History", "desc": "تاريخ البشرية منذ الخلق."},
            {"title": "كليلة ودمنة", "author": "عبد الله بن المقفع", "cat": "Literature", "desc": "قصص وحكم على ألسنة الحيوانات."},
            {"title": "قوة العادات", "author": "Charles Duhigg", "cat": "General", "desc": "لماذا نعمل ما نعمل في الحياة والعمل."},
            {"title": "العادات السبع للناس الأكثر فعالية", "author": "Stephen Covey", "cat": "General", "desc": "دروس في التغيير الشخصي."},
            {"title": "فن الحرب", "author": "Sun Tzu", "cat": "General", "desc": "استراتيجيات عسكرية وإدارية."},
        ]

        # إنشاء الكتب مع توليد ISBN عشوائي
        created_books = []
        for i, b in enumerate(books_data):
            fake_isbn = f"978{random.randint(1000000000, 9999999999)}"
            book = Book.objects.create(
                title=b['title'],
                author=b['author'],
                category=b['cat'],
                isbn=fake_isbn,
                description=b['desc'],
                total_copies=random.randint(3, 8),
                available_copies=random.randint(1, 5), 
                tags=f"{b['cat']}, Education, Academic"
            )
            created_books.append(book)

        self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء {len(created_books)} كتاب تغطي تصنيفات متنوعة.'))

        # 6. إنشاء سجل إعارات (60 عملية متنوعة)
        self.stdout.write('🔄 جاري إنشاء عمليات إعارة عشوائية مكثفة...')
        
        statuses = ['active', 'returned', 'pending', 'returned', 'active', 'rejected', 'overdue']
        
        for _ in range(60): 
            student = random.choice(students)
            book = random.choice(created_books)
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
            
            # محاكاة حالة overdue
            if status == 'overdue':
                status = 'active' # في القاعدة تبقى active لكن التاريخ قديم
                # نجبر التاريخ ليكون قديماً جداً
                request_date = timezone.now() - timezone.timedelta(days=40)
                borrow_date = request_date + timezone.timedelta(days=1)
                due_date = borrow_date + timezone.timedelta(days=14) # Due date was 25 days ago

            Transaction.objects.create(
                book=book,
                student=student,
                status=status,
                request_date=request_date,
                borrow_date=borrow_date,
                return_date=return_date,
                due_date=due_date
            )

        self.stdout.write(self.style.SUCCESS('✅ تم إنشاء سجلات الإعارة.'))
        self.stdout.write(self.style.SUCCESS('🎉🎉 تم تحديث قاعدة البيانات بـ 90+ كتاب و15 طالب!'))
        self.stdout.write(self.style.WARNING(f'🔑 Admin: admin / admin'))
        self.stdout.write(self.style.WARNING(f'🔑 Student Example: {students[0].student_id} / password123'))
