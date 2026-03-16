import streamlit as st
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import io
import json
import re
import docx
from datetime import date

# Load environment variables for local development
load_dotenv()

# --- Translations ---
TRANSLATIONS = {
    "en": {
        "page_title": "AI Resume Optimizer",
        "hero_title": "🚀 AI Resume Optimizer",
        "hero_subtitle": "Get a comprehensive, AI-powered evaluation of your resume with actionable rewrite suggestions.",
        "support_project": "Support This Project",
        "buy_coffee": "☕ Buy Me a Coffee",
        "how_it_works": "How it works:",
        "how_step_1": "1. Upload your resume (PDF, DOCX, or TXT)",
        "how_step_2": "2. Optionally paste a job description",
        "how_step_3": "3. Get scored feedback + rewrite suggestions",
        "your_resume": "📄 Your Resume",
        "upload_label": "Upload your resume (PDF, DOCX, or TXT)",
        "job_description": "🎯 Job Description",
        "job_placeholder": "Pasting the job description allows for a much more accurate analysis...",
        "analyze_button": "✨ Analyze and Evaluate",
        "warning_upload": "⚠️ Please upload your resume first.",
        "spinner_text": "Our AI is performing a deep-dive analysis... This may take a moment.",
        "error_extract": "Could not extract text from the file. It might be empty, corrupted, or an image-based PDF.",
        "error_parse": "Could not parse the analysis scores. Displaying raw feedback.",
        "error_parse_detail": "Error parsing the AI's response. Displaying the full response instead. Details:",
        "error_unexpected": "An unexpected error occurred:",
        "scorecard_header": "📊 Your Evaluation Scorecard",
        "feedback_header": "📝 Detailed Feedback",
        "rewrite_header": "✏️ AI Rewrite Suggestions",
        "score_clarity": "Clarity & Formatting",
        "score_impact": "Impact & Achievements",
        "score_ats": "ATS Friendliness",
        "score_fit": "Job Fit Score",
        "score_freshness": "Freshness & Dates",
        "tab_improvement": "💡 Areas for Improvement",
        "tab_strengths": "✅ Key Strengths",
        "tab_ats": "🤖 ATS & Keyword Optimization",
        "tab_freshness": "📅 Freshness & Date Check",
        "tab_hidden_skills": "🔍 Hidden Skills",
        "no_improvement": "No specific improvement areas identified.",
        "no_strengths": "No specific strengths identified.",
        "no_ats": "No specific ATS tips identified.",
        "no_freshness": "No specific date/freshness issues identified.",
        "no_hidden_skills": "No hidden skills identified.",
        "hidden_skills_header": "🔍 Hidden Skills You Should Highlight",
        "original_label": "❌ Original",
        "rewritten_label": "✅ Rewritten",
        "job_match_header": "🎯 Best Matching Job Roles",
        "footer_text": "Built with Streamlit & Gemini 2.5 Flash",
        "language_label": "🌐 Language",
        "api_key_error": "🔴 Google API Key not found. Please set it in your Streamlit secrets.",
    },
    "de": {
        "page_title": "KI-Lebenslauf-Optimierer",
        "hero_title": "🚀 KI-Lebenslauf-Optimierer",
        "hero_subtitle": "Erhalten Sie eine umfassende, KI-gestützte Bewertung Ihres Lebenslaufs mit umsetzbaren Verbesserungsvorschlägen.",
        "support_project": "Projekt unterstützen",
        "buy_coffee": "☕ Kauf mir einen Kaffee",
        "how_it_works": "So funktioniert es:",
        "how_step_1": "1. Laden Sie Ihren Lebenslauf hoch (PDF, DOCX oder TXT)",
        "how_step_2": "2. Fügen Sie optional eine Stellenbeschreibung ein",
        "how_step_3": "3. Erhalten Sie bewertetes Feedback + Umschreibvorschläge",
        "your_resume": "📄 Ihr Lebenslauf",
        "upload_label": "Laden Sie Ihren Lebenslauf hoch (PDF, DOCX oder TXT)",
        "job_description": "🎯 Stellenbeschreibung",
        "job_placeholder": "Das Einfügen der Stellenbeschreibung ermöglicht eine genauere Analyse...",
        "analyze_button": "✨ Analysieren und Bewerten",
        "warning_upload": "⚠️ Bitte laden Sie zuerst Ihren Lebenslauf hoch.",
        "spinner_text": "Unsere KI führt eine eingehende Analyse durch... Dies kann einen Moment dauern.",
        "error_extract": "Text konnte nicht aus der Datei extrahiert werden. Sie könnte leer, beschädigt oder ein bildbasiertes PDF sein.",
        "error_parse": "Die Analysebewertungen konnten nicht analysiert werden. Rohes Feedback wird angezeigt.",
        "error_parse_detail": "Fehler beim Parsen der KI-Antwort. Stattdessen wird die vollständige Antwort angezeigt. Details:",
        "error_unexpected": "Ein unerwarteter Fehler ist aufgetreten:",
        "scorecard_header": "📊 Ihre Bewertungskarte",
        "feedback_header": "📝 Detailliertes Feedback",
        "rewrite_header": "✏️ KI-Umschreibvorschläge",
        "score_clarity": "Klarheit & Formatierung",
        "score_impact": "Wirkung & Erfolge",
        "score_ats": "ATS-Freundlichkeit",
        "score_fit": "Stellenpassung",
        "score_freshness": "Aktualität & Daten",
        "tab_improvement": "💡 Verbesserungsbereiche",
        "tab_strengths": "✅ Hauptstärken",
        "tab_ats": "🤖 ATS & Keyword-Optimierung",
        "tab_freshness": "📅 Aktualität & Datumscheck",
        "tab_hidden_skills": "🔍 Verborgene Fähigkeiten",
        "no_improvement": "Keine spezifischen Verbesserungsbereiche identifiziert.",
        "no_strengths": "Keine spezifischen Stärken identifiziert.",
        "no_ats": "Keine spezifischen ATS-Tipps identifiziert.",
        "no_freshness": "Keine spezifischen Datums-/Aktualitätsprobleme identifiziert.",
        "no_hidden_skills": "Keine verborgenen Fähigkeiten identifiziert.",
        "hidden_skills_header": "🔍 Verborgene Fähigkeiten, die Sie hervorheben sollten",
        "original_label": "❌ Original",
        "rewritten_label": "✅ Umgeschrieben",
        "job_match_header": "🎯 Am besten passende Berufsrollen",
        "footer_text": "Erstellt mit Streamlit & Gemini 2.5 Flash",
        "language_label": "🌐 Sprache",
        "api_key_error": "🔴 Google API-Schlüssel nicht gefunden. Bitte setzen Sie ihn in Ihren Streamlit-Secrets.",
    },
    "fr": {
        "page_title": "Optimiseur de CV par IA",
        "hero_title": "🚀 Optimiseur de CV par IA",
        "hero_subtitle": "Obtenez une évaluation complète de votre CV par IA avec des suggestions de réécriture concrètes.",
        "support_project": "Soutenir ce projet",
        "buy_coffee": "☕ Offrez-moi un café",
        "how_it_works": "Comment ça marche :",
        "how_step_1": "1. Téléchargez votre CV (PDF, DOCX ou TXT)",
        "how_step_2": "2. Collez éventuellement une description de poste",
        "how_step_3": "3. Obtenez un retour noté + suggestions de réécriture",
        "your_resume": "📄 Votre CV",
        "upload_label": "Téléchargez votre CV (PDF, DOCX ou TXT)",
        "job_description": "🎯 Description du poste",
        "job_placeholder": "Coller la description du poste permet une analyse beaucoup plus précise...",
        "analyze_button": "✨ Analyser et Évaluer",
        "warning_upload": "⚠️ Veuillez d'abord télécharger votre CV.",
        "spinner_text": "Notre IA effectue une analyse approfondie... Cela peut prendre un moment.",
        "error_extract": "Impossible d'extraire le texte du fichier. Il peut être vide, corrompu ou un PDF basé sur des images.",
        "error_parse": "Impossible d'analyser les scores. Affichage du retour brut.",
        "error_parse_detail": "Erreur lors de l'analyse de la réponse de l'IA. Affichage de la réponse complète. Détails :",
        "error_unexpected": "Une erreur inattendue s'est produite :",
        "scorecard_header": "📊 Votre tableau de bord",
        "feedback_header": "📝 Retour détaillé",
        "rewrite_header": "✏️ Suggestions de réécriture IA",
        "score_clarity": "Clarté & Mise en forme",
        "score_impact": "Impact & Réalisations",
        "score_ats": "Compatibilité ATS",
        "score_fit": "Adéquation au poste",
        "score_freshness": "Fraîcheur & Dates",
        "tab_improvement": "💡 Axes d'amélioration",
        "tab_strengths": "✅ Points forts",
        "tab_ats": "🤖 ATS & Optimisation mots-clés",
        "tab_freshness": "📅 Fraîcheur & Vérification des dates",
        "tab_hidden_skills": "🔍 Compétences cachées",
        "no_improvement": "Aucun axe d'amélioration spécifique identifié.",
        "no_strengths": "Aucun point fort spécifique identifié.",
        "no_ats": "Aucun conseil ATS spécifique identifié.",
        "no_freshness": "Aucun problème de date/fraîcheur spécifique identifié.",
        "no_hidden_skills": "Aucune compétence cachée identifiée.",
        "hidden_skills_header": "🔍 Compétences cachées à mettre en valeur",
        "original_label": "❌ Original",
        "rewritten_label": "✅ Réécrit",
        "job_match_header": "🎯 Postes les mieux adaptés",
        "footer_text": "Créé avec Streamlit & Gemini 2.5 Flash",
        "language_label": "🌐 Langue",
        "api_key_error": "🔴 Clé API Google introuvable. Veuillez la configurer dans vos secrets Streamlit.",
    },
    "es": {
        "page_title": "Optimizador de CV con IA",
        "hero_title": "🚀 Optimizador de CV con IA",
        "hero_subtitle": "Obtén una evaluación completa de tu currículum con IA y sugerencias de reescritura accionables.",
        "support_project": "Apoya este proyecto",
        "buy_coffee": "☕ Invítame un café",
        "how_it_works": "Cómo funciona:",
        "how_step_1": "1. Sube tu currículum (PDF, DOCX o TXT)",
        "how_step_2": "2. Opcionalmente pega una descripción del puesto",
        "how_step_3": "3. Obtén retroalimentación con puntuación + sugerencias de reescritura",
        "your_resume": "📄 Tu Currículum",
        "upload_label": "Sube tu currículum (PDF, DOCX o TXT)",
        "job_description": "🎯 Descripción del puesto",
        "job_placeholder": "Pegar la descripción del puesto permite un análisis mucho más preciso...",
        "analyze_button": "✨ Analizar y Evaluar",
        "warning_upload": "⚠️ Por favor, sube tu currículum primero.",
        "spinner_text": "Nuestra IA está realizando un análisis profundo... Esto puede tardar un momento.",
        "error_extract": "No se pudo extraer texto del archivo. Puede estar vacío, corrupto o ser un PDF basado en imágenes.",
        "error_parse": "No se pudieron analizar las puntuaciones. Mostrando retroalimentación sin procesar.",
        "error_parse_detail": "Error al analizar la respuesta de la IA. Mostrando la respuesta completa. Detalles:",
        "error_unexpected": "Se produjo un error inesperado:",
        "scorecard_header": "📊 Tu tarjeta de evaluación",
        "feedback_header": "📝 Retroalimentación detallada",
        "rewrite_header": "✏️ Sugerencias de reescritura IA",
        "score_clarity": "Claridad y formato",
        "score_impact": "Impacto y logros",
        "score_ats": "Compatibilidad ATS",
        "score_fit": "Ajuste al puesto",
        "score_freshness": "Actualidad y fechas",
        "tab_improvement": "💡 Áreas de mejora",
        "tab_strengths": "✅ Fortalezas clave",
        "tab_ats": "🤖 ATS y optimización de palabras clave",
        "tab_freshness": "📅 Actualidad y verificación de fechas",
        "tab_hidden_skills": "🔍 Habilidades ocultas",
        "no_improvement": "No se identificaron áreas de mejora específicas.",
        "no_strengths": "No se identificaron fortalezas específicas.",
        "no_ats": "No se identificaron consejos ATS específicos.",
        "no_freshness": "No se identificaron problemas específicos de fechas/actualidad.",
        "no_hidden_skills": "No se identificaron habilidades ocultas.",
        "hidden_skills_header": "🔍 Habilidades ocultas que deberías destacar",
        "original_label": "❌ Original",
        "rewritten_label": "✅ Reescrito",
        "job_match_header": "🎯 Puestos más compatibles",
        "footer_text": "Creado con Streamlit y Gemini 2.5 Flash",
        "language_label": "🌐 Idioma",
        "api_key_error": "🔴 Clave API de Google no encontrada. Configúrala en tus secretos de Streamlit.",
    },
    "tr": {
        "page_title": "Yapay Zeka CV Optimize Edici",
        "hero_title": "🚀 Yapay Zeka CV Optimize Edici",
        "hero_subtitle": "Yapay zeka destekli kapsamlı bir CV değerlendirmesi ve uygulanabilir yeniden yazım önerileri alın.",
        "support_project": "Bu Projeyi Destekle",
        "buy_coffee": "☕ Bana Bir Kahve Ismarla",
        "how_it_works": "Nasıl çalışır:",
        "how_step_1": "1. CV'nizi yükleyin (PDF, DOCX veya TXT)",
        "how_step_2": "2. İsteğe bağlı olarak iş tanımını yapıştırın",
        "how_step_3": "3. Puanlı geri bildirim + yeniden yazım önerileri alın",
        "your_resume": "📄 CV'niz",
        "upload_label": "CV'nizi yükleyin (PDF, DOCX veya TXT)",
        "job_description": "🎯 İş Tanımı",
        "job_placeholder": "İş tanımını yapıştırmak çok daha doğru bir analiz sağlar...",
        "analyze_button": "✨ Analiz Et ve Değerlendir",
        "warning_upload": "⚠️ Lütfen önce CV'nizi yükleyin.",
        "spinner_text": "Yapay zekamız derinlemesine bir analiz yapıyor... Bu biraz zaman alabilir.",
        "error_extract": "Dosyadan metin çıkarılamadı. Dosya boş, bozuk veya görüntü tabanlı bir PDF olabilir.",
        "error_parse": "Analiz puanları ayrıştırılamadı. Ham geri bildirim gösteriliyor.",
        "error_parse_detail": "Yapay zeka yanıtı ayrıştırılırken hata oluştu. Bunun yerine tam yanıt gösteriliyor. Ayrıntılar:",
        "error_unexpected": "Beklenmeyen bir hata oluştu:",
        "scorecard_header": "📊 Değerlendirme Kartınız",
        "feedback_header": "📝 Detaylı Geri Bildirim",
        "rewrite_header": "✏️ Yapay Zeka Yeniden Yazım Önerileri",
        "score_clarity": "Netlik ve Biçimlendirme",
        "score_impact": "Etki ve Başarılar",
        "score_ats": "ATS Uyumluluğu",
        "score_fit": "İş Uyumu Puanı",
        "score_freshness": "Güncellik ve Tarihler",
        "tab_improvement": "💡 İyileştirme Alanları",
        "tab_strengths": "✅ Temel Güçlü Yönler",
        "tab_ats": "🤖 ATS ve Anahtar Kelime Optimizasyonu",
        "tab_freshness": "📅 Güncellik ve Tarih Kontrolü",
        "tab_hidden_skills": "🔍 Gizli Beceriler",
        "no_improvement": "Belirli bir iyileştirme alanı tespit edilmedi.",
        "no_strengths": "Belirli bir güçlü yön tespit edilmedi.",
        "no_ats": "Belirli bir ATS ipucu tespit edilmedi.",
        "no_freshness": "Belirli bir tarih/güncellik sorunu tespit edilmedi.",
        "no_hidden_skills": "Gizli beceri tespit edilmedi.",
        "hidden_skills_header": "🔍 Öne Çıkarmanız Gereken Gizli Beceriler",
        "original_label": "❌ Orijinal",
        "rewritten_label": "✅ Yeniden Yazılmış",
        "job_match_header": "🎯 En Uygun İş Pozisyonları",
        "footer_text": "Streamlit ve Gemini 2.5 Flash ile yapılmıştır",
        "language_label": "🌐 Dil",
        "api_key_error": "🔴 Google API Anahtarı bulunamadı. Lütfen Streamlit secrets ayarlarınızda tanımlayın.",
    },
}

LANG_OPTIONS = {
    "English": "en",
    "Deutsch": "de",
    "Français": "fr",
    "Español": "es",
    "Türkçe": "tr",
}


def t(key):
    """Get translated string for current language."""
    lang = st.session_state.get("lang", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


# --- Page Configuration ---
st.set_page_config(page_title="AI Resume Optimizer", page_icon="🚀", layout="wide")

# --- Custom CSS for Modern UI ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    font-family: 'Inter', sans-serif;
}

.hero-section {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    padding: 2.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
.hero-section h1 {
    color: #ffffff;
    font-size: 2.4rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}
.hero-section p {
    color: #b8b8d4;
    font-size: 1.1rem;
    font-weight: 300;
}

.score-card {
    background: linear-gradient(145deg, #1a1a2e, #16213e);
    border-radius: 14px;
    padding: 1.5rem 1rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: transform 0.2s ease;
}
.score-card:hover {
    transform: translateY(-3px);
}
.score-card .score-label {
    color: #9ca3af;
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 0.75rem;
}
.radial-wrap {
    position: relative;
    display: inline-block;
    width: 110px;
    height: 110px;
}
.radial-wrap svg {
    transform: rotate(-90deg);
}
.radial-bg {
    fill: none;
    stroke: rgba(255, 255, 255, 0.08);
    stroke-width: 8;
}
.radial-fill {
    fill: none;
    stroke-width: 8;
    stroke-linecap: round;
    transition: stroke-dashoffset 1s ease-in-out;
}
.radial-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.5rem;
    font-weight: 700;
}

.score-red { color: #ef4444; }
.score-yellow { color: #f59e0b; }
.score-green { color: #22c55e; }
.stroke-red { stroke: #ef4444; }
.stroke-yellow { stroke: #f59e0b; }
.stroke-green { stroke: #22c55e; }

.section-header {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    padding: 1.2rem 1.5rem;
    border-radius: 12px;
    margin: 1.5rem 0 1rem 0;
    border-left: 4px solid #6366f1;
}
.section-header h2 {
    color: #e2e8f0;
    font-size: 1.3rem;
    font-weight: 600;
    margin: 0;
}

[data-testid="stFileUploader"] {
    border: 2px dashed rgba(99, 102, 241, 0.4);
    border-radius: 12px;
    padding: 1rem;
    background: rgba(99, 102, 241, 0.05);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border: none;
    border-radius: 10px;
    padding: 0.75rem 2rem;
    font-weight: 600;
    font-size: 1rem;
    letter-spacing: 0.3px;
    transition: all 0.3s ease;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}

.rewrite-card {
    background: rgba(30, 30, 50, 0.6);
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.06);
}
.rewrite-card .before-label {
    color: #ef4444;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.rewrite-card .after-label {
    color: #22c55e;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.rewrite-card .bullet-text {
    color: #d1d5db;
    font-size: 0.95rem;
    line-height: 1.6;
    margin: 0.3rem 0 0.8rem 0;
}

.bmc-button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #FF813F, #FF5F5F);
    color: white !important;
    text-decoration: none !important;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    transition: all 0.3s ease;
}
.bmc-button:hover {
    box-shadow: 0 4px 12px rgba(255, 129, 63, 0.4);
    transform: translateY(-1px);
}

.job-match-card {
    background: linear-gradient(145deg, #1a1a2e, #16213e);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.job-match-card .job-title {
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
}
.job-match-card .job-reason {
    color: #9ca3af;
    font-size: 0.85rem;
    margin-top: 0.25rem;
}
.job-match-card .job-score-badge {
    font-size: 1.3rem;
    font-weight: 700;
    min-width: 55px;
    text-align: center;
    padding: 0.3rem 0.6rem;
    border-radius: 8px;
    background: rgba(255,255,255,0.05);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 16px;
}
</style>
""", unsafe_allow_html=True)

# --- API Key Configuration ---
try:
    google_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=google_key)
except (KeyError, AttributeError):
    st.error(t("api_key_error"))
    st.stop()

# Initialize the Generative Model
model = genai.GenerativeModel('gemini-2.5-flash')


# --- Helper Functions ---
def extract_text_from_pdf(file_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None


def extract_text_from_docx(file_bytes):
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text)
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return None


def extract_text_from_file(uploaded_file):
    file_bytes = uploaded_file.read()
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    elif uploaded_file.type == "text/plain":
        return file_bytes.decode("utf-8")
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_bytes)
    return ""


def get_score_color(score):
    if score <= 4:
        return "red"
    elif score <= 7:
        return "yellow"
    return "green"


def render_score_card(label, score):
    color = get_score_color(score)
    # SVG radial progress: circle with radius 45, circumference ≈ 282.74
    circumference = 282.74
    offset = circumference - (score / 10) * circumference
    st.markdown(f"""
    <div class="score-card">
        <div class="radial-wrap">
            <svg width="110" height="110" viewBox="0 0 110 110">
                <circle class="radial-bg" cx="55" cy="55" r="45"></circle>
                <circle class="radial-fill stroke-{color}" cx="55" cy="55" r="45"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{offset}"></circle>
            </svg>
            <div class="radial-text score-{color}">{score}/10</div>
        </div>
        <div class="score-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


# --- Sidebar: Language Selector + Info ---
with st.sidebar:
    lang_choice = st.selectbox(
        "🌐 Language",
        list(LANG_OPTIONS.keys()),
        index=0,
    )
    st.session_state["lang"] = LANG_OPTIONS[lang_choice]

    st.markdown("---")
    st.markdown(f"### {t('support_project')}")
    st.markdown(f"""
    <a class="bmc-button" href="https://buymeacoffee.com/aliyilbasi" target="_blank">
        {t('buy_coffee')}
    </a>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"**{t('how_it_works')}**")
    st.markdown(f"""
{t('how_step_1')}
{t('how_step_2')}
{t('how_step_3')}
""")

# --- Hero Section ---
st.markdown(f"""
<div class="hero-section">
    <h1>{t('hero_title')}</h1>
    <p>{t('hero_subtitle')}</p>
</div>
""", unsafe_allow_html=True)

# --- Input Columns ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(t("your_resume"))
    uploaded_file = st.file_uploader(
        t("upload_label"),
        type=["pdf", "txt", "docx"],
        label_visibility="collapsed",
    )

with col2:
    st.subheader(t("job_description"))
    job_desc = st.text_area(
        t("job_description"),
        height=250,
        placeholder=t("job_placeholder"),
        label_visibility="collapsed",
    )

analyze_button = st.button(
    t("analyze_button"), type="primary", use_container_width=True
)


def display_results(scores, feedback_dict):
    """Render the evaluation results from stored data."""
    # --- Score Cards ---
    st.markdown(f"""
    <div class="section-header">
        <h2>{t('scorecard_header')}</h2>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_score_card(t("score_clarity"), scores.get("Clarity_and_Formatting", 0))
    with c2:
        render_score_card(t("score_impact"), scores.get("Impact_and_Achievements", 0))
    with c3:
        render_score_card(t("score_ats"), scores.get("ATS_Friendliness", 0))
    with c4:
        render_score_card(t("score_fit"), scores.get("Job_Fit", 0))
    with c5:
        render_score_card(t("score_freshness"), scores.get("Freshness_and_Dates", 0))

    # --- Job Match Suggestions (only when no job desc) ---
    job_matches = scores.get("job_matches", [])
    if job_matches:
        st.markdown(f"""
        <div class="section-header">
            <h2>{t('job_match_header')}</h2>
        </div>
        """, unsafe_allow_html=True)

        for match in job_matches:
            m_title = match.get("title", "")
            m_score = match.get("score", 0)
            m_reason = match.get("reason", "")
            color = get_score_color(m_score)
            st.markdown(f"""
            <div class="job-match-card">
                <div>
                    <div class="job-title">{m_title}</div>
                    <div class="job-reason">{m_reason}</div>
                </div>
                <div class="job-score-badge score-{color}">{m_score}/10</div>
            </div>
            """, unsafe_allow_html=True)

    # --- Detailed Feedback ---
    st.markdown(f"""
    <div class="section-header">
        <h2>{t('feedback_header')}</h2>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        t("tab_improvement"),
        t("tab_strengths"),
        t("tab_ats"),
        t("tab_freshness"),
        t("tab_hidden_skills"),
    ])

    with tab1:
        st.markdown(feedback_dict.get("💡 Areas for Improvement", t("no_improvement")))
    with tab2:
        st.markdown(feedback_dict.get("✅ Key Strengths", t("no_strengths")))
    with tab3:
        st.markdown(feedback_dict.get("🤖 ATS & Keyword Optimization", t("no_ats")))
    with tab4:
        st.markdown(feedback_dict.get("📅 Freshness & Date Check", t("no_freshness")))
    with tab5:
        st.markdown(feedback_dict.get("🔍 Hidden Skills", t("no_hidden_skills")))

    # --- AI Rewrite Suggestions ---
    rewrites = scores.get("rewrite_suggestions", [])
    if rewrites:
        st.markdown(f"""
        <div class="section-header">
            <h2>{t('rewrite_header')}</h2>
        </div>
        """, unsafe_allow_html=True)

        for item in rewrites:
            original = item.get("original", "")
            rewritten = item.get("rewritten", "")
            st.markdown(f"""
            <div class="rewrite-card">
                <div class="before-label">{t('original_label')}</div>
                <div class="bullet-text">{original}</div>
                <div class="after-label">{t('rewritten_label')}</div>
                <div class="bullet-text">{rewritten}</div>
            </div>
            """, unsafe_allow_html=True)


# --- Main Logic ---
if analyze_button:
    if uploaded_file is None:
        st.warning(t("warning_upload"))
    else:
        with st.spinner(t("spinner_text")):
            try:
                resume_text = extract_text_from_file(uploaded_file)
                if not resume_text or not resume_text.strip():
                    st.error(t("error_extract"))
                else:
                    job_matches_instruction = ""
                    if not job_desc:
                        job_matches_instruction = """
                    - "job_matches": an array of 5 objects, each with:
                      - "title": the job role/position title this resume fits (in the resume's language)
                      - "score": integer 1-10 indicating how well the resume fits this role
                      - "reason": a brief one-sentence explanation of why this role is a good match (in the resume's language)
                    This field is REQUIRED when no job description is provided. Analyze the candidate's skills, experience, and background to suggest the 5 best-fitting job roles, sorted from highest to lowest score."""

                    today = date.today().strftime("%B %d, %Y")

                    prompt = f"""
                    You are an expert career coach and professional resume reviewer for a top tech company.
                    Your task is to provide a comprehensive evaluation of a resume.

                    **CRITICAL: TODAY'S DATE IS {today}.**
                    You MUST use this date as your reference when evaluating all dates in the resume. Any date on or before today is in the past, NOT the future. For example, "Jan 2025 – Present" is a valid current role because January 2025 is in the past. Do NOT flag past dates as future dates.

                    **IMPORTANT DATE EVALUATION RULES:**
                    - Overlapping timelines between education and work are NORMAL and EXPECTED (e.g. working while studying). Do NOT flag these as issues.
                    - "Present" or "Current" end dates are valid and mean the person is still in that role/program.
                    - Only flag dates that are genuinely in the future (after {today}) as concerning.
                    - Focus on: consistency of date format, unexplained gaps longer than 6 months between sequential roles, and whether the resume appears recently updated.

                    **CRITICAL LANGUAGE INSTRUCTION:**
                    Detect the language of the resume content below. You MUST write your ENTIRE response (both the JSON values for "original" and "rewritten", and the qualitative Markdown analysis) in the SAME language as the resume. If the resume is in Turkish, respond in Turkish. If in German, respond in German. If in French, respond in French. If in Spanish, respond in Spanish. If in English, respond in English. Match the resume's language exactly.

                    **Context:**
                    - The candidate's resume is provided below.
                    - The target job description is also provided (if available). If no job description is provided, perform a general analysis.

                    **Instructions for your output:**
                    Your response MUST be structured in two parts:

                    PART 1: A JSON object enclosed in triple backticks (```json ... ```). Do not include any text before this JSON block.
                    The JSON object must have:
                    - "Clarity_and_Formatting": integer 1-10
                    - "Impact_and_Achievements": integer 1-10
                    - "ATS_Friendliness": integer 1-10
                    - "Job_Fit": integer 1-10 (score 5 if no job description provided)
                    - "Freshness_and_Dates": integer 1-10. Evaluate how up-to-date the resume is relative to today's date ({today}). Consider: Are dates present and recent? Are there unexplained gaps longer than 6 months between sequential roles? Does the most recent experience end in a current or recent year? Is the date format consistent throughout (e.g. all "MM/YYYY" or all "Month Year")? Are technologies, tools, and certifications current and not outdated? Remember: overlapping education and work dates are completely normal. Score 1-3 if dates are missing, very old, or inconsistent. Score 4-6 if somewhat outdated or has minor gaps/format issues. Score 7-10 if dates are recent, consistent, and well-formatted.
                    - "rewrite_suggestions": array of 3-5 objects with "original" and "rewritten" keys (in the resume's language){job_matches_instruction}

                    PART 2: Detailed qualitative analysis in Markdown (in the resume's language). Use these exact heading formats:
                    ### ✅ Key Strengths
                    ### 💡 Areas for Improvement
                    ### 🤖 ATS & Keyword Optimization
                    ### 📅 Freshness & Date Check
                    (Evaluate the resume's dates: Is it recently updated? Are there employment gaps? Is the date format consistent? Are listed technologies/certifications still current? Provide specific advice on what to update.)

                    ### 🔍 Hidden Skills
                    (Analyze the candidate's work experience, projects, and education to identify skills they clearly possess but did NOT explicitly list or highlight in their resume. For example: if someone managed a team but didn't list "Leadership" or "Team Management"; if they built APIs but didn't mention "REST" or "API Design"; if they worked with data but didn't list "Data Analysis"; if they worked in international teams but didn't mention "Cross-cultural Communication". List each hidden skill with a brief explanation of where in the resume it is implied and suggest how to add it.)

                    ---
                    **Job Description:**
                    {job_desc if job_desc else "Not provided. Please perform a general analysis."}
                    ---
                    **Resume Content:**
                    {resume_text}
                    ---
                    """

                    response = model.generate_content(prompt)
                    response_text = response.text.strip()

                    try:
                        json_match = re.search(
                            r"```json\n(.*?)\n```", response_text, re.DOTALL
                        )
                        if not json_match:
                            st.error(t("error_parse"))
                            st.markdown(response_text)
                        else:
                            json_str = json_match.group(1)
                            scores = json.loads(json_str)
                            qualitative_feedback = response_text[json_match.end():].strip()

                            # Parse feedback into dict
                            sections = qualitative_feedback.split("###")
                            feedback_dict = {}
                            for section in sections:
                                if section.strip():
                                    parts = section.split("\n", 1)
                                    title = parts[0].strip()
                                    content = parts[1].strip() if len(parts) > 1 else ""
                                    feedback_dict[title] = content

                            # Store results in session state
                            st.session_state["results_scores"] = scores
                            st.session_state["results_feedback"] = feedback_dict

                            display_results(scores, feedback_dict)

                    except (json.JSONDecodeError, IndexError, KeyError) as e:
                        st.error(f"{t('error_parse_detail')} {e}")
                        st.markdown("---")
                        st.markdown(response_text)

            except Exception as e:
                st.error(f"{t('error_unexpected')} {e}")

# --- Re-display stored results on rerun (e.g. language change) ---
elif "results_scores" in st.session_state:
    display_results(st.session_state["results_scores"], st.session_state["results_feedback"])

# --- Footer ---
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 1rem 0;">
    <a class="bmc-button" href="https://buymeacoffee.com/aliyilbasi" target="_blank">
        {t('buy_coffee')}
    </a>
    <p style="color: #6b7280; font-size: 0.8rem; margin-top: 0.75rem;">
        {t('footer_text')}
    </p>
</div>
""", unsafe_allow_html=True)
