"""CV Matching — PDF რეზიუმეს შედარება ვაკანსიის აღწერასთან."""
import re
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_text_from_pdf(pdf_file) -> str:
    """ამოიღებს ტექსტს PDF ფაილიდან."""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"PDF წაკითხვის შეცდომა: {e}")
        return ""

def clean_text(text: str) -> str:
    """ასუფთავებს ტექსტს (პატარა ასოები, ზედმეტი სიმბოლოები)."""
    text = text.lower()
    text = re.sub(r'[^\w\sა-ჰ]', ' ', text) # ტოვებს მხოლოდ ასო-ციფრებს
    return re.sub(r'\s+', ' ', text).strip()

def calculate_match_score(cv_text: str, job_text: str) -> int:
    """ითვლის Match %-ს CV-სა და ვაკანსიას შორის (TF-IDF + Cosine Similarity)."""
    if not cv_text or not job_text:
        return 0
    
    # ვასუფთავებთ ტექსტებს
    clean_cv = clean_text(cv_text)
    clean_job = clean_text(job_text)
    
    # თუ ვაკანსიის ტექსტი ძალიან მოკლეა (მხოლოდ სათაური), 
    # TF-IDF შეიძლება ცუდად იმუშაოს, ამიტომ პატარა ჩასწორება
    if len(clean_job.split()) < 5:
        clean_job = clean_job * 3 # ხელოვნურად ვამრავლებთ რომ წონა მიიღოს

    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([clean_cv, clean_job])
        # cosine_similarity აბრუნებს 0-დან 1-მდე მნიშვნელობას
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return int(similarity * 100)
    except ValueError:
        # თუ ტექსტი ცარიელია ან მხოლოდ stop-words-ია
        return 0