import streamlit as st
import PyPDF2
import os
import google.generativeai as genai
from dotenv import load_dotenv
import io
from openai import OpenAI
load_dotenv()

st.set_page_config(page_title="AI Resume Critiquer", page_icon=":page:", layout="centered")

st.title("AI Resume Critiquer ")
st.markdown(
    "Upload your resume in PDF format and get feedback on how to improve it. "
    "The AI will analyze your resume and provide suggestions for improvement."
)

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
job_role = st.text_input("Enter the job role you are applying for(optional)", "")

analyze_button = st.button("Analyze Resume")

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    return uploaded_file.read().decode("utf-8")

if analyze_button and uploaded_file:
    try:
        file_content = extract_text_from_file(uploaded_file)
        if not file_content.strip():
            st.error("The uploaded file is empty or could not be read.")
            st.stop()

        prompt = f"""
       Please analyze this resume and provide constructive feedback.
       Focus on the following aspects:
       1. Content clarity and impact
       2. Skill presentation
       3. Experience description
       4. Specific improvements for the job role: {job_role if job_role else 'general'}
       Here is the resume content:
       {file_content}
       Please provide your feedback in a clear and concise manner.
        """
        
       # Generate response using Gemini
        response = model.generate_content(prompt)
        
        
        st.markdown("### Analysis Result")
        st.markdown(response.text.strip())
    except Exception as e:
        st.error(f"An error occurred while processing the resume: {e}")