import streamlit as st
import pandas as pd
from MatchingAlgo import MatchingAlgorithm
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from datetime import datetime
import io


# STREAMLIT PAGE CONFIG


st.set_page_config(
    page_title="ScholarAI - Erasmus Mundus Matcher",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎓 ScholarAI - Erasmus Mundus Program Matcher")
st.markdown("Find your perfect Erasmus Mundus Master's program with intelligent matching!")

# INITIALIZE SESSION STATE


if 'matcher' not in st.session_state:
    st.session_state.matcher = MatchingAlgorithm()

if 'match_results' not in st.session_state:
    st.session_state.match_results = None

if 'student_profile' not in st.session_state:
    st.session_state.student_profile = None


# SIDEBAR - INPUT FORM


with st.sidebar:
    st.header("📋 Your Profile")
    
    st.subheader("Academic Information")
    cgpa = st.number_input("Your CGPA", min_value=0.0, max_value=5.0, step=0.1, value=3.5)
    cgpa_scale = st.selectbox("CGPA Scale", [4.0, 5.0, 10.0], index=0)
    
    field = st.text_input("Bachelor's Degree Field", placeholder="e.g., Computer Science, Engineering")
    
    st.subheader("English Proficiency")
    col1, col2, col3 = st.columns(3)
    with col1:
        toefl = st.number_input("TOEFL (iBT)", min_value=0, max_value=120, step=1, value=None)
    with col2:
        ielts = st.number_input("IELTS", min_value=0.0, max_value=9.0, step=0.5, value=0.0)
    with col3:
        cambridge = st.selectbox("Cambridge", ["None", "C1", "C2"], index=0)
    
    st.subheader("Experience")
    work_exp = st.number_input("Years of Work Experience", min_value=0, max_value=50, step=1, value=0)
    
    st.subheader("Filter by Field (Optional)")
    all_fields = st.session_state.matcher.get_unique_fields()
    selected_field_filter = st.selectbox(
        "Filter programs by field",
        ["All Fields"] + all_fields,
        index=0
    )
    
    st.divider()
    
    if st.button("🔍 Find Programs", type="primary", use_container_width=True):
        # Validate input
        if not field:
            st.error("Please enter your bachelor's degree field")
        else:
            # Store student profile
            st.session_state.student_profile = {
                'cgpa': cgpa,
                'cgpa_scale': cgpa_scale,
                'field': field,
                'toefl': toefl if toefl and toefl > 0 else None,
                'ielts': ielts if ielts and ielts > 0 else None,
                'cambridge': cambridge if cambridge != "None" else None,
                'work_experience': work_exp
            }
            
            # Get programs
            if selected_field_filter == "All Fields":
                programs_df = st.session_state.matcher.get_all_programs()
            else:
                programs_df = st.session_state.matcher.get_programs_by_field(selected_field_filter)
            
            # Calculate matches
            st.session_state.match_results = st.session_state.matcher.match_programs(
                st.session_state.student_profile,
                programs_df
            )
            
            st.success(f"✅ Matched {len(st.session_state.match_results)} programs!")

# ============================================
# MAIN CONTENT - RESULTS
# ============================================

if st.session_state.match_results:
    student = st.session_state.student_profile
    results = st.session_state.match_results
    
    # Display student profile summary
    st.subheader("📊 Your Profile Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("CGPA", f"{student['cgpa']:.1f}/{int(student['cgpa_scale'])}")
    with col2:
        st.metric("Field", student['field'][:20])
    with col3:
        toefl_val = student['toefl'] if student['toefl'] else "N/A"
        st.metric("TOEFL", toefl_val)
    with col4:
        ielts_val = f"{student['ielts']:.1f}" if student['ielts'] else "N/A"
        st.metric("IELTS", ielts_val)
    with col5:
        st.metric("Work Experience", f"{student['work_experience']} yrs")
    
    st.divider()
    
    # TOP 3 RECOMMENDATIONS
    st.subheader("🏆 Top 3 Recommended Programs For You")
    
    top_3 = st.session_state.matcher.get_top_recommendations(results, top_n=3)
    
    for idx, program in enumerate(top_3, 1):
        color = st.session_state.matcher.get_match_color(program['overall_match'])
        
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### #{idx} - {program['program_name']} ({program['acronym']})")
                st.markdown(f"**Field:** {program['field']}")
                if program['consortium']:
                    st.markdown(f"**Consortium:** {program['consortium']}")
                if program['deadline']:
                    st.markdown(f"**Deadline:** {program['deadline']}")
                if program['scholarship']:
                    st.markdown(f"**Scholarship:** {program['scholarship']}")
            
            with col2:
                # Color-coded match percentage
                if color == "green":
                    st.markdown(f"### ✅ {program['overall_match']}%")
                    st.markdown("*Strong Fit*")
                elif color == "orange":
                    st.markdown(f"### ⚠️ {program['overall_match']}%")
                    st.markdown("*Moderate Fit*")
                else:
                    st.markdown(f"### ❌ {program['overall_match']}%")
                    st.markdown("*Weak Fit*")
            
            # Score breakdown
            st.markdown("**Match Breakdown:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.caption(f"CGPA: {program['cgpa_score']}/25")
            with col2:
                st.caption(f"Language: {program['language_score']}/15")
            with col3:
                st.caption(f"Field: {program['field_score']}/50")
            with col4:
                st.caption(f"Experience: {program['work_exp_score']}/5")
            
            # Detailed feedback
            with st.expander(f"View detailed feedback for {program['acronym']}"):
                st.markdown(f"**CGPA:** {program['cgpa_feedback']}")
                st.markdown(f"**Language:** {program['language_feedback']}")
                st.markdown(f"**Field:** {program['field_feedback']}")
                st.markdown(f"**Work Experience:** {program['work_exp_feedback']}")
                if program['website']:
                    st.markdown(f"[Visit Program Website]({program['website']})")
    
    st.divider()
    
    # ALL RESULTS TABLE
    st.subheader("📋 All Programs (Ranked by Match)")
    
    # Convert to display format
    display_results = []
    for prog in results:
        color_emoji = "🟢" if prog['overall_match'] >= 80 else "🟡" if prog['overall_match'] >= 60 else "🔴"
        display_results.append({
            "": color_emoji,
            "Program Name": prog['program_name'],
            "Acronym": prog['acronym'],
            "Field": prog['field'],
            "Match %": prog['overall_match'],
            "CGPA": prog['cgpa_score'],
            "Language": prog['language_score'],
            "Field": prog['field_score'],
            "Exp": prog['work_exp_score']
        })
    
    df_display = pd.DataFrame(display_results)
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # PDF DOWNLOAD
    st.subheader("📥 Download Your Report")
    
    if st.button("📄 Generate PDF Report", use_container_width=True):
        # Generate PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12,
            alignment=1
        )
        story.append(Paragraph("ScholarAI Report", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Student Info
        story.append(Paragraph("Student Profile", styles['Heading2']))
        student_data = [
            ["CGPA", f"{student['cgpa']:.1f}/{int(student['cgpa_scale'])}"],
            ["Field", student['field']],
            ["TOEFL", student['toefl'] if student['toefl'] else "N/A"],
            ["IELTS", student['ielts'] if student['ielts'] else "N/A"],
            ["Work Experience", f"{student['work_experience']} years"],
            ["Report Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        student_table = Table(student_data, colWidths=[2*inch, 3*inch])
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(student_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Top 3 Recommendations
        story.append(Paragraph("Top 3 Recommended Programs", styles['Heading2']))
        for idx, prog in enumerate(top_3, 1):
            story.append(Paragraph(f"{idx}. {prog['program_name']} ({prog['acronym']}) - {prog['overall_match']}% Match", styles['Heading3']))
            story.append(Paragraph(f"Field: {prog['field']}<br/>Deadline: {prog['deadline']}", styles['Normal']))
            story.append(Spacer(1, 0.15*inch))
        
        story.append(PageBreak())
        
        # All Results
        story.append(Paragraph("All Program Matches", styles['Heading2']))
        all_prog_data = [["Rank", "Program", "Acronym", "Match %", "Field"]]
        for idx, prog in enumerate(results[:20], 1):  # Top 20
            all_prog_data.append([
                str(idx),
                prog['program_name'][:30],
                prog['acronym'],
                f"{prog['overall_match']}%",
                prog['field'][:20]
            ])
        
        all_prog_table = Table(all_prog_data)
        all_prog_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(all_prog_table)
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_buffer.getvalue(),
            file_name=f"ScholarAI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        st.success("✅ PDF ready for download!")

else:
    st.info("👈 Enter your profile in the sidebar and click 'Find Programs' to get started!")


# FOOTER

st.divider()
st.markdown("""
---
**ScholarAI** - Powered by NLP-based requirement parsing
Built for Erasmus Mundus applicants worldwide 🌍
""")