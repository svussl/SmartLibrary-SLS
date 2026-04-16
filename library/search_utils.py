# library/search_utils.py

# 1. قاموس المصطلحات التقنية (Mapping Dictionary)
TECH_TERMS_MAPPING = {
    "بايثون": "Python",
    "جافا": "Java",
    "سي شارب": "C#",
    "فلاتر": "Flutter",
    "جانجو": "Django",
    "رياكت": "React",
    "ذكاء اصطناعي": "Artificial Intelligence AI",
    "تعلم الآلة": "Machine Learning ML",
    "قواعد البيانات": "Databases SQL",
    "خوارزميات": "Algorithms",
}

def expand_search_query(user_query):
    """
    تقوم هذه الدالة بفحص نص البحث وإضافة المصطلحات الإنجليزية المرادفة
    لتعزيز المعنى الدلالي قبل تمريره لنموذج التضمين.
    """
    if not user_query:
        return ""

    expanded_query = user_query

    # البحث عن المصطلحات العربية واستبدالها بالنسخة المدمجة (عربي + إنجليزي)
    for ar_term, en_term in TECH_TERMS_MAPPING.items():
        if ar_term in expanded_query:
            # مثال: تحويل "بايثون" إلى "بايثون Python"
            expanded_query = expanded_query.replace(ar_term, f"{ar_term} {en_term}")
    
    # تنظيف المسافات الزائدة
    return " ".join(expanded_query.split())