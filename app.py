import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from groq import Groq
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# -------------------------
# LOAD ENV
# -------------------------
load_dotenv(".env")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("Groq API Key Missing")
    st.stop()

client = Groq(api_key=api_key)

# -------------------------
# OCR PATHS
# -------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler\Library\bin"

# -------------------------
# PAGE
# -------------------------
st.set_page_config(page_title="AI Resume Analyzer", page_icon="💼", layout="wide")

st.markdown("""
<style>
.stApp{
background:linear-gradient(135deg,#020617,#0f172a,#111827);
color:white;
}
h1,h2,h3,p,label{
color:white!important;
}
.stButton>button{
background:#16a34a;
color:white;
border:none;
padding:12px 20px;
border-radius:10px;
font-weight:bold;
font-size:18px;
}
</style>
""", unsafe_allow_html=True)

st.title("💼 AI Resume Analyzer")
st.write("Upload Resume ➜ Get AI Suggestions + Updated Resume PDF")

# -------------------------
# FUNCTIONS
# -------------------------
def extract_text(uploaded_file):
    text = ""

    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except:
        pass

    if len(text.strip()) > 80:
        return text

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name

        images = convert_from_path(temp_path, poppler_path=POPPLER_PATH)

        for img in images:
            text += pytesseract.image_to_string(img)

        os.unlink(temp_path)

    except:
        pass

    return text


def get_ai_response(resume_text):

    prompt = f"""
You are a professional resume expert.

Analyze this resume and give:

1. Resume Score out of 100
2. Strengths
3. Weaknesses
4. Missing Skills
5. ATS Improvement Tips
6. Professional Improved Resume Rewrite

Resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        temperature=0.4
    )

    return response.choices[0].message.content


def create_pdf(text):

    file_name = "Updated_Resume.pdf"

    doc = SimpleDocTemplate(
        file_name,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        name="title",
        fontSize=20,
        leading=24,
        alignment=1,
        spaceAfter=20
    )

    normal = ParagraphStyle(
        name="normal",
        fontSize=11,
        leading=15,
        spaceAfter=8
    )

    story = []

    story.append(Paragraph("Professional Updated Resume", title))
    story.append(Spacer(1,12))

    for line in text.split("\n"):
        if line.strip():
            story.append(Paragraph(line, normal))

    doc.build(story)

    return file_name

# -------------------------
# UI
# -------------------------
uploaded_file = st.file_uploader("Upload Resume PDF", type=["pdf"])

if uploaded_file:

    st.success("Resume Uploaded")

    text = extract_text(uploaded_file)

    if len(text.strip()) < 50:
        st.error("Resume text not readable")
        st.stop()

    if st.button("Generate Full AI Analysis"):

        with st.spinner("AI analyzing..."):

            result = get_ai_response(text)

            st.subheader("📊 AI Suggestions & Analysis")
            st.write(result)

            pdf_file = create_pdf(result)

            with open(pdf_file, "rb") as f:
                st.download_button(
                    "📄 Download Updated Resume PDF",
                    f,
                    file_name="Updated_Resume.pdf",
                    mime="application/pdf"
                )

            st.success("Resume Ready")