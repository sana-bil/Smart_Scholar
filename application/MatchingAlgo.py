import pyodbc
import pandas as pd
from typing import Dict
from sentence_transformers import SentenceTransformer, util
import torch
import re

class MatchingAlgorithm:
    def __init__(self):
        self.conn = pyodbc.connect(
            'Driver={ODBC Driver 17 for SQL Server};'
            'Server=DESKTOP-2G14Q4N\\MSSQLSERVER01;'
            'Database=SmartScholar;'
            'Trusted_Connection=yes;'
        )
        self.nlp_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        self.main_domains = [
            "Engineering & Technology", "Law & Governance", "Mathematics & Statistics",
            "Psychology & Cognitive Science", "Biology & Life Sciences", "Physics & Physical Sciences",
            "Business & Economics", "Humanities & Social Sciences", "Medicine & Health", "Environmental Science"
        ]

    def _clean_text(self, text: str) -> str:
        """Removes filler academic words so AI focuses on the core subject."""
        if not text: return ""
        pattern = r'\b(bachelors?|masters?|degree|bsc|ba|bba|engg|in)\b'
        cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return cleaned.strip()

    def infer_domain(self, text: str) -> str:
        try:
            text = self._clean_text(text)
            if not text: return "Engineering & Technology"
            low_text = text.lower()
            if any(k in low_text for k in ['ai', 'machine learning', 'data science', 'analytics', 'software', 'computer']):
                return "Engineering & Technology"
            if any(k in low_text for k in ['art', 'design', 'creative', 'culture', 'humanities']):
                return "Humanities & Social Sciences"

            text_emb = self.nlp_model.encode(text, convert_to_tensor=True)
            domain_embs = self.nlp_model.encode(self.main_domains, convert_to_tensor=True)
            sims = util.pytorch_cos_sim(text_emb, domain_embs)[0]
            return self.main_domains[sims.argmax().item()]
        except:
            return "Engineering & Technology"

    def calculate_total_match(self, student_profile: Dict, program: pd.Series) -> Dict:
        s_clean_field = self._clean_text(student_profile.get('field', ''))
        p_raw_text = program['field'] if program['field'] else program['program_name']
        p_clean_text = self._clean_text(p_raw_text)

        if self.infer_domain(s_clean_field) != self.infer_domain(p_clean_text):
            return self._create_result(program, 0, "🔴", "Domain Mismatch")

        student_emb = self.nlp_model.encode(s_clean_field, convert_to_tensor=True)
        program_emb = self.nlp_model.encode(p_clean_text, convert_to_tensor=True)
        similarity = float(util.pytorch_cos_sim(student_emb, program_emb)[0][0])
        
        if similarity < 0.28: 
            return self._create_result(program, 0, "🔴", "Unrelated Field")

        f_score = 50 if similarity >= 0.45 else 42 if similarity >= 0.35 else 30
        req_cgpa = program['min_cgpa'] if not pd.isna(program['min_cgpa']) else 0
        norm_student = (student_profile['cgpa'] / student_profile['cgpa_scale']) * (program['cgpa_scale'] if not pd.isna(program['cgpa_scale']) else 4.0)
        c_score = 25 if norm_student >= req_cgpa else max(5, int(25 - ((req_cgpa - norm_student) * 10)))
        
        l_score = 0
        if student_profile.get('ielts') and not pd.isna(program['min_ielts_score']):
            if student_profile['ielts'] >= program['min_ielts_score']: l_score = 15
        elif student_profile.get('toefl') and not pd.isna(program['min_toefl_score']):
            if student_profile['toefl'] >= program['min_toefl_score']: l_score = 15

        e_score = 5 if student_profile['work_experience'] >= 1 else 0
        total = min(100, int(f_score + c_score + l_score + e_score + 5))
        return self._create_result(program, total, "🟢" if total >= 80 else "🟡" if total >= 60 else "🔴", "Match Found", f_score, c_score, l_score, e_score)

    def _create_result(self, program, match_val, status, reason, f=0, c=0, l=0, e=0):
        return {
            'status': status, 'program_name': program['program_name'], 'acronym': program['acronym'],
            'field': program['field'], 'overall_match': match_val, 'field_score': f, 'cgpa_score': c,
            'lang_score': l, 'exp_score': e, 'consortium': program['consortium'],
            'deadline': program['application_deadline'], 'scholarship': program['scholarship'], 'reason': reason
        }

    def get_all_programs(self):
        return pd.read_sql("SELECT ep.*, pr.* FROM EmjmdPrograms ep LEFT JOIN ProgramRequirements pr ON ep.program_id = pr.program_id", self.conn)