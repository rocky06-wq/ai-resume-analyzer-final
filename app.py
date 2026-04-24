import streamlit as st
from groq import Groq
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import tempfile

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler\Library\bin"

st.set_page_config(page_title="AI Resume Analyzer", page_icon="💼")

st.markdown("""
<style>
.stApp{
background:linear-gradient(135deg,#0f172a,#111827,#1e293b);
color:white;
}
.stButton button{
background:#22c55e;
color:white;
border:none;
border-radius:10px;
height:45px;
width:100%;
font-size:18px;
font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

st.title("💼 AI Resume Analyzer")
st.write("AI Suggestions + Corporate Resume Generator")

uploaded_file = st.file_uploader("Upload Resume PDF", type=["pdf"])

def read_resume(file):
    text = ""

    try:
        reader = PdfReader(file)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    except:
        pass

    if len(text) < 40:
        try:
            images = convert_from_bytes(
                file.getvalue(),
                poppler_path=POPPLER_PATH
            )

            for img in images:
                text += pytesseract.image_to_string(img) + "\n"

        except:
            pass

    return text.strip()

def create_pdf(content):

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    path = temp.name

    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=25, leftMargin=35, rightMargin=35)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="title",
        parent=styles["Heading1"],
        fontSize=22,
        alignment=TA_CENTER,
        spaceAfter=14
    )

    normal = ParagraphStyle(
        name="normal",
        parent=styles["Normal"],
        fontSize=10.5,
        leading=14,
        spaceAfter=6
    )

    story = []

    first = True

    for line in content.split("\n"):

        if line.strip() == "":
            continue

        if first:
            story.append(Paragraph(line, title_style))
            first = False
        else:
            story.append(Paragraph(line, normal))

    doc.build(story)
    return path

if uploaded_file:

    st.success("✅ Resume Uploaded")

    text = read_resume(uploaded_file)

    if len(text) < 30:
        st.error("❌ Cannot read resume")
    else:

        st.success("✅ Resume Read Successfully")

        if st.button("🔍 Get AI Suggestions"):

            prompt = f"""
Analyze this resume professionally.

Give:

1. Missing Skills
2. Weak Points
3. Better Summary Example
4. ATS Improvements
5. Hiring Chances
6. Better Experience Example
7. Salary Growth Tips

Resume:
{text}
"""

            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role":"user","content":prompt}
                ]
            )

            st.subheader("📌 AI Suggestions")
            st.write(res.choices[0].message.content)

        if st.button("✨ Generate Corporate Resume"):

            prompt = f"""
Rewrite this resume in CORPORATE PROFESSIONAL format.

Make sections:

Name
Phone | Email | LinkedIn

Professional Summary

Skills

Experience

Education

Projects

Use bullet points.
ATS Friendly.
Strong professional wording.

Return only final resume.

Resume:
{text}
"""

            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role":"user","content":prompt}
                ]
            )

            final_resume = res.choices[0].message.content

            st.subheader("📄 Resume Preview")
            st.text_area("Preview", final_resume, height=550)

            pdf_path = create_pdf(final_resume)

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "📥 Download Resume PDF",
                    f,
                    file_name="Corporate_Resume.pdf",
                    mime="application/pdf"
                )