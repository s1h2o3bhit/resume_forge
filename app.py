import streamlit as st
import json
import os
from fpdf import FPDF
from PyPDF2 import PdfReader
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="ResumeForge AI Pro", layout="wide")

# 1. INITIALIZATION
if 'master_data' not in st.session_state:
    st.session_state.master_data = {
        "contact": {"name": "", "email": "", "phone": "", "location": "Nagpur, Maharashtra"},
        "skills": "",
        "experience": "",
        "projects": ""
    }

for key in ['old_resume_text', 'new_resume_text', 'missing_keywords', 'jd_input']:
    if key not in st.session_state:
        st.session_state[key] = "" if key != 'missing_keywords' else []

# --- HELPERS ---
def clean_for_pdf(text):
    """Deep clean text to prevent FPDF encoding crashes and handle special characters."""
    if not text: return ""
    chars = {
        "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "•": "o",
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2022": "o"
    }
    for old, new in chars.items():
        text = text.replace(old, new)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def calculate_ats_score(resume_text, jd_text):
    """Core logic to compare resume content against the Job Description."""
    if not jd_text or not resume_text: return 0
    jd_words = set(re.findall(r'\w+', jd_text.lower()))
    res_words = set(re.findall(r'\w+', resume_text.lower()))
    stop_words = {'and', 'the', 'with', 'from', 'that', 'this', 'for', 'was', 'were'}
    jd_keywords = {word for word in jd_words if len(word) > 3 and word not in stop_words}
    if not jd_keywords: return 0
    matched_words = jd_keywords.intersection(res_words)
    return round((len(matched_words) / len(jd_keywords)) * 100, 2)

# --- ATS-OPTIMIZED PDF CLASS ---
class PDF(FPDF):
    def header(self):
        """Creates the professional header with clear hierarchy for ATS."""
        if self.page_no() == 1:
            # Name - Bold and Large (Left-aligned for professional readability)
            self.set_font('helvetica', 'B', 24)
            self.set_text_color(40, 40, 40)
            name = st.session_state.master_data['contact'].get('name', 'YOUR NAME')
            self.cell(0, 15, clean_for_pdf(name.upper()), ln=True, align='L')
            
            # Contact Line - Plain text (No icons to ensure 100% ATS capture)
            self.set_font('helvetica', '', 10)
            self.set_text_color(80, 80, 80)
            c = st.session_state.master_data['contact']
            contact = f"{c['location']} | {c['phone']} | {c['email']}"
            self.cell(0, 5, clean_for_pdf(contact), ln=True, align='L')
            self.ln(5)

    def section_header(self, title):
        """Standardized Sectioning for consistent ATS Recognition."""
        self.ln(4)
        self.set_font('helvetica', 'B', 11)
        self.set_text_color(0, 0, 0)
        # Bold Header
        self.cell(0, 8, clean_for_pdf(title.upper()), ln=True)
        # Structural Divider Line (Visual for humans, anchor for machines)
        self.set_draw_color(180, 180, 180)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

# --- MAIN UI ---
st.title("🛡️ ResumeForge AI: Pro Transformation Engine")
tabs = st.tabs(["📥 Import & Memory", "🔬 AI Comparison Lab", "📄 Final Export & Validation"])

# TAB 1: IMPORT & CONTACT INFO
with tabs[0]:
    st.header("Step 1: Build the Memory")
    uploaded_file = st.file_uploader("Upload Old Resume (PDF)", type="pdf")
    
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        raw_text = "".join([page.extract_text() for page in reader.pages])
        st.session_state.old_resume_text = raw_text
        st.success("Resume scanned successfully!")

    st.subheader("Contact Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.master_data['contact']['name'] = st.text_input("Full Name", st.session_state.master_data['contact']['name'])
    with col2:
        st.session_state.master_data['contact']['email'] = st.text_input("Email Address", st.session_state.master_data['contact']['email'])
    with col3:
        st.session_state.master_data['contact']['phone'] = st.text_input("Phone Number", st.session_state.master_data['contact']['phone'])

# TAB 2: AI TRANSFORMATION
with tabs[1]:
    st.header("Step 2: AI Comparison Lab")
    st.session_state.jd_input = st.text_area("Paste Target Job Description", height=150)
    
    if st.button("🪄 Run AI Transformation Model"):
        if st.session_state.old_resume_text and st.session_state.jd_input:
            clean_text = clean_for_pdf(st.session_state.old_resume_text)
            jd_words = set(re.findall(r'\w+', st.session_state.jd_input.lower()))
            resume_words = set(re.findall(r'\w+', clean_text.lower()))
            
            missing = [word for word in (jd_words - resume_words) if len(word) > 5][:8]
            
            transformed = clean_text + "\n\n--- PROFESSIONAL ACHIEVEMENTS & OPTIMIZATIONS ---\n"
            for word in missing:
                transformed += f"- Strategic implementation of {word} to improve efficiency and analytical accuracy.\n"
            
            st.session_state.new_resume_text = transformed
            st.success("AI Transformation Complete!")
        else:
            st.error("Please ensure you have uploaded a resume and provided a Job Description.")

    if st.session_state.new_resume_text:
        st.subheader("Review Optimized Content")
        st.session_state.new_resume_text = st.text_area("Edit Final Text", st.session_state.new_resume_text, height=300)

# TAB 3: EXPORT & ATS CHECKER
with tabs[2]:
    st.header("Step 3: Generate & Verify")
    
    if st.session_state.new_resume_text:
        col_pdf, col_ats = st.columns([1, 1])
        
        with col_pdf:
            st.subheader("1. Download Optimized PDF")
            if st.button("🖨️ Create ATS-Friendly Resume"):
                pdf = PDF()
                pdf.set_left_margin(15)
                pdf.set_right_margin(15)
                pdf.add_page()
                
                # SECTION: SUMMARY
                pdf.section_header("Professional Summary")
                pdf.set_font("helvetica", '', 10)
                summary_text = "Highly analytical professional with expertise in Python-driven data automation and dashboarding. Proven track record in streamlining data workflows and delivering actionable business insights."
                pdf.multi_cell(0, 5, clean_for_pdf(summary_text))
                
                # SECTION: SKILLS
                pdf.section_header("Technical Skills")
                pdf.set_font("helvetica", 'B', 10)
                pdf.cell(40, 6, "Programming:", ln=0)
                pdf.set_font("helvetica", '', 10)
                pdf.cell(0, 6, "Python (Pandas, NumPy, Scikit-learn), SQL (MS SQL, MySQL)", ln=True)
                
                pdf.set_font("helvetica", 'B', 10)
                pdf.cell(40, 6, "Visualization:", ln=0)
                pdf.set_font("helvetica", '', 10)
                pdf.cell(0, 6, "Power BI, Tableau, Streamlit, Matplotlib", ln=True)
                
                # SECTION: EXPERIENCE
                pdf.section_header("Professional Experience")
                pdf.set_font("helvetica", '', 10)
                pdf.multi_cell(0, 5, clean_for_pdf(st.session_state.new_resume_text))
                
                # SECTION: EDUCATION
                pdf.section_header("Education")
                pdf.set_font("helvetica", 'B', 10)
                pdf.cell(0, 5, "Master of Computer Management", ln=True)
                pdf.set_font("helvetica", '', 10)
                pdf.cell(0, 5, "Taywade College, Nagpur | CGPA: 8.42", ln=True)

                pdf_bytes = bytes(pdf.output())
                st.download_button(
                    label="📥 Download Final Resume", 
                    data=pdf_bytes, 
                    file_name="Optimized_Analyst_Resume.pdf",
                    mime="application/pdf"
                )

        with col_ats:
            st.subheader("2. ATS Score Checker")
            uploaded_check = st.file_uploader("Upload PDF to Verify Score", type="pdf", key="verify_tool")
            if uploaded_check:
                v_reader = PdfReader(uploaded_check)
                v_text = "".join([p.extract_text() for p in v_reader.pages])
                final_score = calculate_ats_score(v_text, st.session_state.jd_input)
                
                st.metric("Final ATS Match Score", f"{final_score}%")
                if final_score >= 85:
                    st.balloons()
                    st.success("🔥 Outstanding match! Ready for submission.")
                else:
                    st.warning("Consider adding more keywords from the JD to improve the score.")
    else:
        st.warning("Complete the AI Transformation in Tab 2 to generate the PDF.")