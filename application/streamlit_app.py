import streamlit as st
import pandas as pd
from MatchingAlgo import MatchingAlgorithm
from fpdf import FPDF
import io
import re

def generate_pdf(profile, results):
    # Tightened margins to maximize vertical space
    pdf = FPDF(unit='mm', format='A4')
    pdf.set_margins(10, 5, 10) 
    pdf.add_page()
    
    # --- HEADER SECTION (More compact) ---
    pdf.set_fill_color(20, 40, 80)
    pdf.rect(0, 0, 210, 30, 'F')
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(8)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 8, "ScholarAI Eligibility Report", ln=True, align='C')
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, "Official Erasmus Mundus Compatibility Assessment", ln=True, align='C')
    
    # --- CANDIDATE PROFILE SECTION ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(32)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 7, "CANDIDATE PROFILE SUMMARY", ln=True)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(1)
    
    pdf.set_font("Arial", '', 9)
    # Using 6mm height for rows to save space
    pdf.cell(95, 6, f"Major Field: {profile['field']}")
    pdf.cell(95, 6, f"CGPA: {profile['cgpa']} / {profile['cgpa_scale']}", ln=True)
    pdf.cell(95, 6, f"English Score: {profile['ielts'] if profile['ielts'] > 0 else profile['toefl']}")
    pdf.cell(95, 6, f"Work Experience: {profile['work_experience']} Years", ln=True)
    
    # --- MATCHING RESULTS TABLE ---
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 7, "PROGRAM COMPATIBILITY RANKING", ln=True)
    
    # Professional Header
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(230, 235, 245)
    pdf.cell(12, 9, "Rank", 1, 0, 'C', True)
    pdf.cell(123, 9, " Program Name", 1, 0, 'L', True)
    pdf.cell(25, 9, "Match Index", 1, 0, 'C', True)
    pdf.cell(30, 9, "Standing", 1, 1, 'C', True)
    
    # ROW HEIGHT REDUCED TO 8.0mm TO ENSURE 1-PAGE FIT
    pdf.set_font("Arial", '', 8)
    for i, res in enumerate(results[:15], 1):
        clean_name = re.sub(r'[^\x00-\x7F]+', '', res['program_name'])
        name = (clean_name[:78] + '..') if len(clean_name) > 78 else clean_name
        
        pdf.cell(12, 8.0, str(i), 1, 0, 'C')
        pdf.cell(123, 8.0, f" {name}", 1, 0, 'L')
        
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(25, 8.0, f"{res['overall_match']}%", 1, 0, 'C')
        
        if res['overall_match'] >= 80:
            pdf.set_text_color(0, 100, 0)
            status_text = "HIGHLY MATCHED"
        elif res['overall_match'] >= 60:
            pdf.set_text_color(180, 120, 0)
            status_text = "QUALIFIED"
        else:
            pdf.set_text_color(150, 0, 0)
            status_text = "LOW MATCH"
            
        pdf.cell(30, 8.0, status_text, 1, 1, 'C')
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", '', 8)

    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

st.set_page_config(page_title="ScholarAI", layout="wide")
st.title("🎓 ScholarAI - Erasmus Mundus Matcher")

if 'session_matcher' not in st.session_state:
    st.session_state.session_matcher = MatchingAlgorithm()

with st.sidebar:
    st.header("📋 Your Profile")
    with st.form("input_form"):
        cgpa = st.number_input("Your CGPA", 0.0, 10.0, 0.0, step=0.01)
        cgpa_scale = st.selectbox("CGPA Scale", [4.0, 5.0, 10.0])
        field = st.text_input("Bachelor's Degree Field", value="", placeholder="e.g., Bachelors in Physics")
        st.subheader("English Proficiency")
        c1, c2 = st.columns(2)
        toefl = c1.number_input("TOEFL", 0, 120, 0)
        ielts = c2.number_input("IELTS", 0.0, 9.0, 0.0)
        work_exp = st.number_input("Years of Experience", 0, 20, 0)
        submit = st.form_submit_button("🔍 Find Programs", type="primary", use_container_width=True)

if submit and field:
    profile = {'cgpa': cgpa, 'cgpa_scale': cgpa_scale, 'field': field, 'ielts': ielts, 'toefl': toefl, 'work_experience': work_exp}
    st.session_state.current_profile = profile
    df = st.session_state.session_matcher.get_all_programs()
    st.session_state.results = sorted([st.session_state.session_matcher.calculate_total_match(profile, row) for _, row in df.iterrows()], 
                                     key=lambda x: x['overall_match'], reverse=True)

if 'results' in st.session_state:
    p = st.session_state.current_profile
    st.subheader("📊 Your Profile Summary")
    sum_cols = st.columns(4)
    sum_cols[0].metric("CGPA", f"{p['cgpa']} / {int(p['cgpa_scale'])}")
    sum_cols[1].metric("Field", p['field'])
    sum_cols[2].metric("IELTS/TOEFL", f"{p['ielts'] if p['ielts'] > 0 else p['toefl']}")
    sum_cols[3].metric("Experience", f"{p['work_experience']} yrs")

    recs = [r for r in st.session_state.results if r['overall_match'] >= 60][:5]
    if recs:
        st.subheader("🏆 Top Recommended Programs")
        for i, res in enumerate(recs, 1):
            with st.container(border=True):
                main_col, score_col = st.columns([4, 1])
                with main_col:
                    st.markdown(f"### #{i} - {res['program_name']} ({res['acronym']})")
                    st.write(f"**Field:** {res['field']} | **Deadline:** {res['deadline']}")
                    st.write(f"**Scholarship:** {res['scholarship']}")
                with score_col:
                    st.markdown(f"## {res['overall_match']}%")
                    st.write(f"Status: {res['status']}")
                st.caption(f"Breakdown: Field {res['field_score']} | CGPA {res['cgpa_score']} | Lang {res['lang_score']} | Exp {res['exp_score']}")

    st.divider()
    st.subheader("📋 Ranked Match Results")
    res_df = pd.DataFrame(st.session_state.results)
    st.dataframe(res_df[['status', 'program_name', 'overall_match', 'field_score', 'cgpa_score']], use_container_width=True, hide_index=True)
    
    st.subheader("📂 Export Report")
    pdf_bytes = generate_pdf(st.session_state.current_profile, st.session_state.results)
    st.download_button("📄 Download PDF Report", data=pdf_bytes, file_name="ScholarAI_Report.pdf", mime="application/pdf", use_container_width=True)