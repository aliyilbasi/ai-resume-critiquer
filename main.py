import streamlit as st
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import io
import json
import re

# Load environment variables for local development
load_dotenv()

# --- Page Configuration ---
st.set_page_config(page_title="AI Resume Optimizer", page_icon="🚀", layout="wide")

# --- API Key Configuration ---
try:
    # Use st.secrets for deployment
    google_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=google_key)
except (KeyError, AttributeError):
    st.error("🔴 Google API Key not found. Please set it in your Streamlit secrets.")
    st.stop()

# Initialize the Generative Model
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Helper Functions for Text Extraction ---
def extract_text_from_pdf(file_bytes):
    """Extracts text from a PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return None

def extract_text_from_file(uploaded_file):
    """Extracts text from the uploaded file (PDF or TXT)."""
    file_bytes = uploaded_file.read()
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    elif uploaded_file.type == "text/plain":
        return file_bytes.decode("utf-8")
    return ""

# --- UI Elements ---
st.title("🚀 AI Resume Optimizer")
st.markdown(
    "Get a comprehensive evaluation of your resume. For the best results, provide the job description you're targeting."
)

st.divider()

# --- Input Columns ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Your Resume")
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF or TXT)", type=["pdf", "txt"], label_visibility="collapsed"
    )

with col2:
    st.subheader("Job Description")
    job_desc = st.text_area(
        "Paste the job description here",
        height=250,
        placeholder="Pasting the job description allows for a much more accurate analysis...",
        label_visibility="collapsed"
    )

analyze_button = st.button("✨ Analyze and Evaluate", type="primary", use_container_width=True)

# --- Main Logic ---
if analyze_button:
    if uploaded_file is None:
        st.warning("⚠️ Please upload your resume first.")
    else:
        with st.spinner("Our AI is performing a deep-dive analysis... This may take a moment."):
            try:
                resume_text = extract_text_from_file(uploaded_file)
                if not resume_text or not resume_text.strip():
                    st.error("Could not extract text from the file. It might be empty, corrupted, or an image-based PDF.")
                else:
                    # --- The New, Powerful Prompt ---
                    prompt = f"""
                    You are an expert career coach and professional resume reviewer for a top tech company.
                    Your task is to provide a comprehensive evaluation of a resume.

                    **Context:**
                    - The candidate's resume is provided below.
                    - The target job description is also provided (if available). Your primary goal is to assess the resume's suitability for this specific role. If no job description is provided, perform a general analysis for a professional role.

                    **Instructions for your output:**
                    Your response MUST be structured in two parts:
                    
                    PART 1: A JSON object containing your quantitative scores. This JSON object must be enclosed in triple backticks (```json ... ```). Do not include any text before this JSON block.
                    The JSON object must have the following keys with integer values from 1 to 10:
                    - "Clarity_and_Formatting": How readable, clean, and professional the resume is.
                    - "Impact_and_Achievements": How well the resume uses quantifiable results and action verbs to show impact.
                    - "ATS_Friendliness": How well the resume is optimized for Applicant Tracking Systems (e.g., standard format, keywords).
                    - "Job_Fit": How well the resume content (skills, experience) aligns with the provided job description. Score 5 if no job description is provided.

                    PART 2: A detailed qualitative analysis in Markdown format. This part should come AFTER the JSON block. Use the following exact headings:
                    ### ✅ Key Strengths
                    (List 2-3 specific things the resume does well.)
                    
                    ### 💡 Areas for Improvement
                    (Provide a detailed, actionable list of the most important changes. Focus on rephrasing bullet points, adding metrics, and tailoring content.)
                    
                    ### 🤖 ATS & Keyword Optimization
                    (Give advice on how to improve the resume for Applicant Tracking Systems. Suggest specific keywords from the job description that are missing from the resume.)

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
                    
                    # --- Parsing the AI's Response ---
                    try:
                        # Find the JSON part using regex, which is more robust
                        json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
                        if not json_match:
                            # Fallback if JSON is not found in the expected format
                            st.error("Could not parse the analysis scores. Displaying raw feedback.")
                            st.markdown(response_text)
                        else:
                            json_str = json_match.group(1)
                            scores = json.loads(json_str)

                            # The rest of the text is the qualitative feedback
                            qualitative_feedback = response_text[json_match.end():].strip()

                            # --- Displaying the Structured Output ---
                            st.divider()
                            st.header("Your Evaluation Scorecard")

                            # Display Metrics
                            c1, c2, c3, c4 = st.columns(4)
                            with c1:
                                st.metric("Clarity & Formatting", f"{scores.get('Clarity_and_Formatting', 0)}/10")
                            with c2:
                                st.metric("Impact & Achievements", f"{scores.get('Impact_and_Achievements', 0)}/10")
                            with c3:
                                st.metric("ATS Friendliness", f"{scores.get('ATS_Friendliness', 0)}/10")
                            with c4:
                                st.metric("Job Fit Score", f"{scores.get('Job_Fit', 0)}/10", help="How well the resume matches the job description.")
                            
                            st.divider()
                            st.header("Detailed Feedback")
                            
                            # Split feedback into sections based on our defined headers
                            sections = qualitative_feedback.split('###')
                            feedback_dict = {}
                            for section in sections:
                                if section.strip():
                                    parts = section.split('\n', 1)
                                    title = parts[0].strip()
                                    content = parts[1].strip() if len(parts) > 1 else ""
                                    feedback_dict[title] = content
                            
                            tab1, tab2, tab3 = st.tabs(["💡 Areas for Improvement", "✅ Key Strengths", "🤖 ATS & Keyword Optimization"])

                            with tab1:
                                st.markdown(feedback_dict.get('💡 Areas for Improvement', "No specific improvement areas identified."))
                            
                            with tab2:
                                st.markdown(feedback_dict.get('✅ Key Strengths', "No specific strengths identified."))
                                
                            with tab3:
                                st.markdown(feedback_dict.get('🤖 ATS & Keyword Optimization', "No specific ATS tips identified."))
                                
                    except (json.JSONDecodeError, IndexError, KeyError) as e:
                        st.error(f"Error parsing the AI's response. Displaying the full response instead. Details: {e}")
                        st.markdown("---")
                        st.markdown(response_text)

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")