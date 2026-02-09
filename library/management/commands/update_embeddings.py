from django.core.management.base import BaseCommand
from library.models import Book
from library.ai_engine import SmartLibraryAI

class Command(BaseCommand):
    help = 'توليد البصمات الدلالية (Embeddings) لجميع الكتب الموجودة'

    def handle(self, *args, **kwargs):
        self.stdout.write("جاري تهيئة محرك الذكاء الاصطناعي...")
        ai = SmartLibraryAI()
        
        books = Book.objects.all()
        count = books.count()
        
        self.stdout.write(f"تم العثور على {count} كتاب. جاري المعالجة...")
        
        processed = 0
        for book in books:
            ai.update_book_embedding(book)
            processed += 1
            if processed % 10 == 0:
                self.stdout.write(f"تمت معالجة {processed}/{count}")
                
        self.stdout.write(self.style.SUCCESS('تم تحديث جميع الكتب بنجاح! النظام جاهز للبحث الدلالي.'))