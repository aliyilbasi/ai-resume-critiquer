import streamlit as st
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import io
import json
import re
import plotly.graph_objects as go

# --- Page & API Configuration ---
load_dotenv()
st.set_page_config(page_title="AI Resume Optimizer", page_icon="🚀", layout="wide")

try:
    google_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=google_key)
except (KeyError, AttributeError):
    st.error("🔴 Google API Key not found. Please set it in your Streamlit secrets.")
    st.stop()

model = genai.GenerativeModel('gemini-1.5-flash')

# --- VISUAL HELPER FUNCTIONS ---

def display_score_bar(score, title):
    """Displays a score as a styled progress bar in the sidebar."""
    st.sidebar.markdown(f"##### {title}")
    
    # Color coding the progress bar
    if score >= 8:
        color = "#28a745" # Green
    elif score >= 5:
        color = "#ffc107" # Yellow
    else:
        color = "#dc3545" # Red
    
    # Custom HTML/CSS for a better-looking progress bar
    st.sidebar.markdown(
        f"""
        <div style="background-color: #eee; border-radius: 5px; height: 25px; width: 100%;">
            <div style="background-color: {color}; width: {score * 10}%; height: 100%; border-radius: 5px; text-align: center; color: white; font-weight: bold; line-height: 25px;">
                {score}/10
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.write("") # Add some space

def create_skill_gap_chart(resume_skills, job_skills):
    """Creates a Plotly bar chart showing matched and missing skills."""
    resume_set = set(s.lower().strip() for s in resume_skills)
    job_set = set(s.lower().strip() for s in job_skills)
    
    matched_skills = list(resume_set.intersection(job_set))
    missing_skills = list(job_set.difference(resume_set))
    
    if not matched_skills and not missing_skills:
        st.info("No specific skills were extracted for comparison. This can happen with very short job descriptions.")
        return None

    # Data for the chart
    y_labels = matched_skills + missing_skills
    x_values = [1] * len(matched_skills) + [-1] * len(missing_skills)
    colors = ['#28a745'] * len(matched_skills) + ['#dc3545'] * len(missing_skills)
    texts = ["Present"] * len(matched_skills) + ["Missing"] * len(missing_skills)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=y_labels,
        x=x_values,
        orientation='h',
        marker_color=colors,
        text=texts,
        hoverinfo='y',
        textposition="none"
    ))

    fig.update_layout(
        title='<b>Resume vs. Job Description Skill Gap</b>',
        xaxis=dict(
            tickvals=[-1, 1],
            ticktext=['<b>MISSING FROM RESUME</b>', '<b>PRESENT IN RESUME</b>'],
            title_text=""
        ),
        yaxis=dict(autorange="reversed"), # Puts matched skills on top
        height=200 + len(y_labels) * 25, # Dynamic height
        margin=dict(l=150) # Add left margin for long skill names
    )
    return fig


# --- TEXT EXTRACTION (Unchanged) ---
def extract_text_from_pdf(file_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return "".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def extract_text_from_file(uploaded_file):
    file_bytes = uploaded_file.read()
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    return file_bytes.decode("utf-8")

# --- UI ELEMENTS ---
st.title("🚀 AI Resume Dashboard")
st.markdown("Upload your resume and a job description to get a visual, in-depth analysis of your fit.")
st.divider()

# --- Input Columns ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Your Resume")
    uploaded_file = st.file_uploader("Upload (PDF or TXT)", type=["pdf", "txt"], label_visibility="collapsed")
with col2:
    st.subheader("Job Description")
    job_desc = st.text_area("Paste here", height=250, placeholder="For the best results, provide the job description...", label_visibility="collapsed")

analyze_button = st.button("✨ Generate My Dashboard", type="primary", use_container_width=True)

# --- MAIN LOGIC ---
if analyze_button:
    if uploaded_file is None:
        st.warning("⚠️ Please upload your resume first.")
    else:
        with st.spinner("Our AI is building your dashboard... This may take a moment."):
            try:
                resume_text = extract_text_from_file(uploaded_file)
                if not resume_text or not resume_text.strip():
                    st.error("Could not extract text from the file. It might be empty or an image-based PDF.")
                else:
                    # --- THE NEW, VISUAL-FOCUSED PROMPT ---
                    prompt = f"""
                    You are an expert career coach AI. Your task is to provide a comprehensive evaluation of a resume against a job description.

                    Your response MUST be a single JSON object enclosed in triple backticks. Do not include any text before or after the JSON block.
                    The JSON object must have three top-level keys: "scores", "skill_analysis", and "qualitative_feedback".

                    1. "scores": An object with integer scores (1-10) for these keys:
                       - "Clarity_and_Formatting"
                       - "Impact_and_Achievements"
                       - "ATS_Friendliness"
                       - "Job_Fit" (Score 5 if no job description)

                    2. "skill_analysis": An object with two keys:
                       - "resume_keywords": A list of the top 10-15 most important technical skills, tools, and soft skills found in the resume.
                       - "job_description_keywords": A list of the top 10-15 most important required skills, tools, and qualifications from the job description. If no job description, return an empty list.

                    3. "qualitative_feedback": An object with string values for these keys:
                       - "strengths": A markdown-formatted string listing 2-3 key strengths of the resume.
                       - "improvements": A detailed, markdown-formatted string with the most important areas for improvement.
                       - "ats_optimization": A markdown-formatted string with advice on ATS optimization and missing keywords.

                    ---
                    **Job Description:**
                    {job_desc if job_desc else "Not provided."}
                    ---
                    **Resume Content:**
                    {resume_text}
                    ---
                    """

                    response = model.generate_content(prompt)
                    response_text = response.text.strip()
                    
                    # --- Parsing the AI's Response ---
                    json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
                    if not json_match:
                        st.error("Error: Could not parse the AI's response. The format was unexpected.")
                        st.code(response_text) # Show the raw response for debugging
                    else:
                        json_str = json_match.group(1)
                        data = json.loads(json_str)
                        
                        scores = data.get("scores", {})
                        skills = data.get("skill_analysis", {})
                        feedback = data.get("qualitative_feedback", {})

                        # --- Displaying the Dashboard ---
                        st.sidebar.header("📊 Evaluation Scorecard")
                        for title, score in scores.items():
                            # Reformat title from "Clarity_and_Formatting" to "Clarity and Formatting"
                            formatted_title = title.replace('_', ' ').title()
                            display_score_bar(score, formatted_title)
                        
                        st.header("Visual Analysis")

                        # Display Skill Gap Chart only if job description is provided
                        if job_desc and skills.get("job_description_keywords"):
                            fig = create_skill_gap_chart(skills.get("resume_keywords", []), skills.get("job_description_keywords", []))
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Provide a job description to generate a Skill Gap Analysis chart.")
                        
                        st.divider()
                        st.header("Detailed Feedback")
                        
                        tab1, tab2, tab_ats = st.tabs(["💡 Areas for Improvement", "✅ Key Strengths", "🤖 ATS Optimization"])

                        with tab1:
                            st.markdown(feedback.get('improvements', "No specific improvement areas identified."))
                        with tab2:
                            st.markdown(feedback.get('strengths', "No specific strengths identified."))
                        with tab_ats:
                            st.markdown(feedback.get('ats_optimization', "No specific ATS tips identified."))
                                
            except json.JSONDecodeError as e:
                st.error(f"Error decoding the AI's JSON response: {e}")
                st.code(response_text) # Show the raw response for debugging
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")