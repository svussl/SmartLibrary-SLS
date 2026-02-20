import numpy as np
from sentence_transformers import SentenceTransformer, util
from .models import Book
import random

class SmartLibraryAI:
    """
    نسخة الأداء العالي (High Performance).
    تستخدم النموذج متعدد اللغات (paraphrase-multilingual-MiniLM-L12-v2).
    تدعم العربية والإنجليزية أصالةً دون الحاجة لترجمة وسيطة.
    """
    
    _instance = None
    _model = None

    def __new__(cls):
        # تطبيق نمط Singleton
        if cls._instance is None:
            cls._instance = super(SmartLibraryAI, cls).__new__(cls)
            print("⏳ Loading AI Model (Multilingual Pro)...")
            try:
                # تحميل النموذج القوي (حجمه 470 ميغابايت تقريباً)
                cls._model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                print("✅ AI Model Loaded Successfully (Supports Arabic & English).")
            except Exception as e:
                print(f"❌ Error loading AI model: {e}")
                cls._model = None
        return cls._instance

    def generate_embedding(self, text):
        """توليد متجه رقمي للنص (عربي أو إنجليزي)"""
        if not self._model:
            return []
        # المودل يفهم اللغة تلقائياً
        embedding = self._model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def update_book_embedding(self, book):
        """تحديث بصمة كتاب واحد"""
        # ندمج النصوص العربية والإنجليزية
        full_text = f"{book.title}. {book.category}. {book.description}. {book.tags}"
        book.embedding = self.generate_embedding(full_text)
        book.save()
        print(f"✅ Updated multilingual embedding for: {book.title}")

    def semantic_search(self, query, top_k=5):
        """البحث الدلالي"""
        if not self._model:
            return Book.objects.filter(title__icontains=query)

        print(f"\n🔍 Searching for: {query}")
        query_embedding = self._model.encode(query, convert_to_tensor=True)
        
        books = Book.objects.exclude(embedding__isnull=True)
        if not books.exists():
            return []

        book_embeddings = [b.embedding for b in books]
        book_ids = [b.id for b in books]

        corpus_embeddings = np.array(book_embeddings).astype('float32')
        cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]

        top_results = []
        for idx, score in enumerate(cos_scores):
            if score > 0.35: 
                top_results.append((score.item(), book_ids[idx]))
                print(f"   -> Found Match: Book ID {book_ids[idx]} (Score: {score:.2f})")

        top_results = sorted(top_results, key=lambda x: x[0], reverse=True)[:top_k]

        final_books = []
        for score, bid in top_results:
            book = Book.objects.get(id=bid)
            book.match_score = round(score * 100, 1) 
            final_books.append(book)

        return final_books

    def get_recommendations(self, book_id, top_k=4):
        """جلب كتب مشابهة (Content-Based)"""
        try:
            target_book = Book.objects.get(id=book_id)
            if not target_book.embedding:
                self.update_book_embedding(target_book)
            
            if not target_book.embedding: return []

            target_embedding = np.array(target_book.embedding).astype('float32')
            books = Book.objects.exclude(id=book_id).exclude(embedding__isnull=True)
            if not books.exists(): return []

            book_embeddings = [b.embedding for b in books]
            book_ids = [b.id for b in books]

            corpus_embeddings = np.array(book_embeddings).astype('float32')
            cos_scores = util.cos_sim(target_embedding, corpus_embeddings)[0]

            top_results = []
            for idx, score in enumerate(cos_scores):
                if score > 0.50: 
                    top_results.append((score.item(), book_ids[idx]))

            top_results = sorted(top_results, key=lambda x: x[0], reverse=True)[:top_k]

            recommended_books = []
            for score, bid in top_results:
                recommended_books.append(Book.objects.get(id=bid))
            return recommended_books

        except Book.DoesNotExist:
            return []

    def recommend_by_profile(self, profile_text, top_k=8):
        """اقتراح كتب بناءً على تخصص الطالب"""
        enhanced_query = f"كتب ومراجع علمية في تخصص {profile_text}"
        return self.semantic_search(enhanced_query, top_k=top_k)