import streamlit as st
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import io
import json
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Load environment variables for local development
load_dotenv()

# --- Page Configuration ---
st.set_page_config(page_title="AI Resume Optimizer", page_icon="🚀", layout="wide")

# --- API Key Configuration ---
try:
    google_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=google_key)
except (KeyError, AttributeError):
    st.error("🔴 Google API Key not found. Please set it in your Streamlit secrets.")
    st.stop()

# Initialize the Generative Model
model = genai.GenerativeModel('gemini-1.5-flash')

# --- VISUALIZATION HELPER FUNCTIONS ---

def create_score_gauge(score, title):
    """Creates a Plotly gauge for a given score."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 20}},
        gauge = {
            'axis': {'range': [0, 10], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#2E8B57"}, # SeaGreen
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 4], 'color': '#FF7F7F'},  # Light Coral
                {'range': [4, 7], 'color': '#FFD700'},  # Gold
                {'range': [7, 10], 'color': '#90EE90'}  # Light Green
            ],
        }))
    fig.update_layout(height=250)
    return fig

def create_word_cloud(text, title):
    """Creates and displays a word cloud."""
    if not text or not text.strip():
        st.write(f"{title}: Not enough text to generate a word cloud.")
        return
    
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.set_axis_off()
    st.pyplot(fig)

def create_donut_chart(data, title):
    """Creates a Plotly donut chart for section analysis."""
    if not data:
        st.write("No section analysis data available.")
        return
    labels = list(data.keys())
    values = list(data.values())
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4,
                                 hoverinfo="label+percent", textinfo="label")])
    fig.update_layout(
        title_text=title,
        showlegend=False,
        height=400,
        margin=dict(t=50, b=0, l=0, r=0)
    )
    return fig


# --- TEXT EXTRACTION FUNCTIONS (Unchanged) ---
def extract_text_from_pdf(file_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = "".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return None

def extract_text_from_file(uploaded_file):
    file_bytes = uploaded_file.read()
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    return file_bytes.decode("utf-8")

# --- UI ELEMENTS ---
st.title("🚀 AI Resume Optimizer with Visual Analytics")
st.markdown("Get a comprehensive evaluation of your resume, now with visual insights!")
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Upload Your Resume")
    uploaded_file = st.file_uploader("Upload (PDF or TXT)", type=["pdf", "txt"], label_visibility="collapsed")
with col2:
    st.subheader("2. Paste the Job Description")
    job_desc = st.text_area("Paste here", height=250, placeholder="For the best results, provide the job description...", label_visibility="collapsed")

analyze_button = st.button("✨ Analyze and Visualize", type="primary", use_container_width=True)

# --- MAIN LOGIC ---
if analyze_button:
    if uploaded_file is None:
        st.warning("⚠️ Please upload your resume first.")
    else:
        with st.spinner("Our AI is performing a deep-dive analysis... This may take a moment."):
            try:
                resume_text = extract_text_from_file(uploaded_file)
                if not resume_text or not resume_text.strip():
                    st.error("Could not extract text from the file. It might be empty or image-based.")
                else:
                    # --- THE UPDATED, MORE POWERFUL PROMPT ---
                    prompt = f"""
                    You are an expert career coach and professional resume reviewer.
                    Your task is to provide a comprehensive evaluation of a resume, with data for visualizations.

                    **Context:**
                    - The candidate's resume is provided.
                    - The target job description is provided (if available).

                    **Instructions for your output:**
                    Your response MUST be structured in two parts:
                    
                    PART 1: A JSON object enclosed in triple backticks (```json ... ```).
                    This JSON object MUST have two top-level keys: "scores" and "section_analysis".
                    1. The "scores" key must contain an object with these four integer scores (1-10): "Clarity_and_Formatting", "Impact_and_Achievements", "ATS_Friendliness", "Job_Fit". Score "Job_Fit" as 5 if no job description is provided.
                    2. The "section_analysis" key must contain an object where you estimate the percentage of the resume's text content dedicated to these sections: "Experience", "Skills", "Education", "Projects", "Summary". Omit any section not present. The percentages must add up to 100.

                    Example JSON:
                    ```json
                    {{
                        "scores": {{
                            "Clarity_and_Formatting": 8,
                            "Impact_and_Achievements": 6,
                            "ATS_Friendliness": 7,
                            "Job_Fit": 9
                        }},
                        "section_analysis": {{
                            "Experience": 60,
                            "Skills": 15,
                            "Education": 15,
                            "Projects": 10
                        }}
                    }}
                    ```

                    PART 2: A detailed qualitative analysis in Markdown format, coming AFTER the JSON block. Use these exact headings:
                    ### ✅ Key Strengths
                    ### 💡 Areas for Improvement
                    ### 🤖 ATS & Keyword Optimization

                    ---
                    **Job Description:**
                    {job_desc if job_desc else "Not provided. Perform a general analysis."}
                    ---
                    **Resume Content:**
                    {resume_text}
                    ---
                    """

                    response = model.generate_content(prompt)
                    response_text = response.text.strip()
                    
                    # --- PARSING AND DISPLAYING RESULTS ---
                    json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
                    if not json_match:
                        st.error("Could not parse the AI's response. Displaying raw feedback:")
                        st.markdown(response_text)
                    else:
                        json_str = json_match.group(1)
                        data = json.loads(json_str)
                        scores = data.get("scores", {})
                        section_data = data.get("section_analysis", {})
                        qualitative_feedback = response_text[json_match.end():].strip()

                        st.divider()
                        st.header("📊 Your Visual Scorecard")
                        
                        # --- Display Gauges ---
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.plotly_chart(create_score_gauge(scores.get('Clarity_and_Formatting', 0), "Clarity"), use_container_width=True)
                        with c2:
                            st.plotly_chart(create_score_gauge(scores.get('Impact_and_Achievements', 0), "Impact"), use_container_width=True)
                        with c3:
                            st.plotly_chart(create_score_gauge(scores.get('ATS_Friendliness', 0), "ATS Score"), use_container_width=True)
                        with c4:
                            st.plotly_chart(create_score_gauge(scores.get('Job_Fit', 0), "Job Fit"), use_container_width=True)
                        
                        st.divider()
                        st.header("🔑 Keyword Analysis")
                        
                        # --- Display Word Clouds ---
                        wc1, wc2 = st.columns(2)
                        with wc1:
                            st.subheader("Your Resume's Keywords")
                            create_word_cloud(resume_text, "Your Resume")
                        with wc2:
                            st.subheader("Job Description's Keywords")
                            create_word_cloud(job_desc, "Job Description")
                        
                        st.divider()
                        
                        # --- Display Donut Chart and Detailed Feedback ---
                        fb1, fb2 = st.columns([1, 2])
                        with fb1:
                            st.header("Layout Analysis")
                            st.plotly_chart(create_donut_chart(section_data, "Resume Content Distribution"), use_container_width=True)

                        with fb2:
                            st.header("💡 Detailed Feedback")
                            st.markdown(qualitative_feedback)
            
            except json.JSONDecodeError:
                st.error("Error decoding the analysis data from the AI. Please try again.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")