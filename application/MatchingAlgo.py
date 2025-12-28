import pyodbc
import pandas as pd
from typing import Dict, List, Tuple

class MatchingAlgorithm:
    """Calculate match scores between student profile and program requirements"""
    
    def __init__(self):
        # SQL Server connection
        self.conn = pyodbc.connect(
            'Driver={ODBC Driver 17 for SQL Server};'
            'Server=DESKTOP-2G14Q4N\\MSSQLSERVER01;'
            'Database=SmartScholar;'
            'Trusted_Connection=yes;'
        )
    
    def get_all_programs(self) -> pd.DataFrame:
        """Fetch all programs with their requirements"""
        query = """
        SELECT 
            ep.program_id,
            ep.program_name,
            ep.acronym,
            ep.field,
            ep.consortium,
            ep.website,
            ep.scholarship,
            ep.application_deadline,
            pr.min_toefl_score,
            pr.min_ielts_score,
            pr.min_cambridge_score,
            pr.min_cgpa,
            pr.cgpa_scale,
            pr.english_required,
            pr.work_experience_years,
            pr.accepted_degree_fields
        FROM EmjmdPrograms ep
        LEFT JOIN ProgramRequirements pr ON ep.program_id = pr.program_id
        ORDER BY ep.program_id
        """
        return pd.read_sql(query, self.conn)
    
    def get_programs_by_field(self, field: str) -> pd.DataFrame:
        """Fetch programs filtered by field"""
        query = f"""
        SELECT 
            ep.program_id,
            ep.program_name,
            ep.acronym,
            ep.field,
            ep.consortium,
            ep.website,
            ep.scholarship,
            ep.application_deadline,
            pr.min_toefl_score,
            pr.min_ielts_score,
            pr.min_cambridge_score,
            pr.min_cgpa,
            pr.cgpa_scale,
            pr.english_required,
            pr.work_experience_years,
            pr.accepted_degree_fields
        FROM EmjmdPrograms ep
        LEFT JOIN ProgramRequirements pr ON ep.program_id = pr.program_id
        WHERE ep.field LIKE '%{field}%'
        ORDER BY ep.program_id
        """
        return pd.read_sql(query, self.conn)
    
    def get_unique_fields(self) -> List[str]:
        """Get all unique program fields"""
        query = "SELECT DISTINCT field FROM EmjmdPrograms WHERE field IS NOT NULL ORDER BY field"
        result = pd.read_sql(query, self.conn)
        return result['field'].tolist() if not result.empty else []
    
    def normalize_cgpa(self, student_cgpa: float, student_scale: float, requirement_scale: float) -> float:
        """Normalize CGPA to requirement scale"""
        if student_scale == requirement_scale:
            return student_cgpa
        return (student_cgpa / student_scale) * requirement_scale
    
    def calculate_cgpa_match(self, student_cgpa: float, student_scale: float, req_cgpa: float, req_scale: float) -> Tuple[int, str]:
        """Calculate CGPA match score (0-25 points) - REDUCED PRIORITY"""
        if req_cgpa is None or pd.isna(req_cgpa):
            return 25, "No CGPA requirement"
        
        # Normalize student CGPA to requirement scale
        normalized_cgpa = self.normalize_cgpa(student_cgpa, student_scale, req_scale)
        
        if normalized_cgpa >= req_cgpa:
            return 25, f"Your CGPA {student_cgpa}/{student_scale} meets requirement {req_cgpa}/{req_scale}"
        else:
            gap = req_cgpa - normalized_cgpa
            # Partial credit for being close
            score = max(0, int(25 - (gap * 10)))
            return score, f"Your CGPA {student_cgpa}/{student_scale} is below requirement {req_cgpa}/{req_scale} (gap: {gap:.2f})"
    
    def calculate_language_match(self, toefl: int = None, ielts: float = None, cambridge: str = None, 
                                 req_toefl: int = None, req_ielts: float = None, req_cambridge: str = None) -> Tuple[int, str]:
        """Calculate language match score (0-15 points) - REDUCED PRIORITY"""
        if req_toefl is None and req_ielts is None and req_cambridge is None:
            return 15, "No specific language requirement"
        
        matches = 0
        feedback = []
        total_requirements = 0
        
        # TOEFL check
        if req_toefl is not None and not pd.isna(req_toefl):
            total_requirements += 1
            if toefl and toefl >= req_toefl:
                matches += 1
                feedback.append(f"✓ TOEFL {toefl} meets requirement {req_toefl}")
            elif toefl:
                feedback.append(f"✗ TOEFL {toefl} below requirement {req_toefl}")
            else:
                feedback.append(f"✗ No TOEFL score provided (requirement: {req_toefl})")
        
        # IELTS check
        if req_ielts is not None and not pd.isna(req_ielts):
            total_requirements += 1
            if ielts and ielts >= req_ielts:
                matches += 1
                feedback.append(f"✓ IELTS {ielts} meets requirement {req_ielts}")
            elif ielts:
                feedback.append(f"✗ IELTS {ielts} below requirement {req_ielts}")
            else:
                feedback.append(f"✗ No IELTS score provided (requirement: {req_ielts})")
        
        # Cambridge check
        if req_cambridge is not None and not pd.isna(req_cambridge):
            total_requirements += 1
            if cambridge and cambridge >= req_cambridge:
                matches += 1
                feedback.append(f"✓ Cambridge {cambridge} meets requirement {req_cambridge}")
            elif cambridge:
                feedback.append(f"✗ Cambridge {cambridge} below requirement {req_cambridge}")
            else:
                feedback.append(f"✗ No Cambridge score provided (requirement: {req_cambridge})")
        
        if matches > 0 and total_requirements > 0:
            score = int(15 * (matches / total_requirements))
            return score, " | ".join(feedback)
        else:
            return 0, " | ".join(feedback) if feedback else "No language test scores provided"
    
    def calculate_field_match(self, student_field: str, accepted_fields: str, program_field: str = None) -> Tuple[int, str]:
        """Calculate field match score (0-50 points) - NOW PRIMARY CRITERION
        Checks both: program's own field AND accepted degree fields"""
        
        student_field_lower = student_field.lower()
        
        # First priority: Check program's own field
        if program_field:
            program_field_lower = str(program_field).lower()
            
            # Perfect match with program field
            if student_field_lower in program_field_lower or program_field_lower in student_field_lower:
                return 50, f"Your field ({student_field}) matches program focus ({program_field})"
            
            # Partial match with program field
            keywords = student_field_lower.split()
            for keyword in keywords:
                if len(keyword) > 3 and keyword in program_field_lower:
                    return 45, f"Your field ({student_field}) is related to program focus ({program_field})"
        
        # Second priority: Check accepted degree fields
        if accepted_fields and not pd.isna(accepted_fields):
            accepted_list = [f.strip().lower() for f in str(accepted_fields).split(',')]
            
            # Perfect match in accepted fields
            if student_field_lower in accepted_list:
                return 40, f"Your field ({student_field}) is listed in accepted fields"
            
            # Partial match in accepted fields
            for field in accepted_list:
                if field in student_field_lower or student_field_lower in field:
                    return 30, f"Your field ({student_field}) is related to accepted fields"
        
        # No match found
        return 5, f"Your field ({student_field}) does not match program focus"
    
    def calculate_work_experience_match(self, student_years: int, required_years: int = None) -> Tuple[int, str]:
        """Calculate work experience match score (0-5 points) - REDUCED"""
        if required_years is None or pd.isna(required_years) or required_years == 0:
            return 5, "Work experience not required"
        
        if student_years >= required_years:
            return 5, f"Your {student_years} years meets requirement of {required_years} years"
        else:
            return 0, f"Your {student_years} years is below requirement of {required_years} years"
    
    def calculate_total_match(self, student_profile: Dict, program: pd.Series) -> Dict:
        """Calculate overall match score for a program
        
        NEW SCORING (out of 100):
        - Field: 50 points (PRIMARY - most important)
        - CGPA: 25 points
        - Language: 15 points
        - Work Experience: 5 points
        - Citizenship: 5 points
        = 100 points MAX
        """
        
        # Extract scores
        cgpa_score, cgpa_feedback = self.calculate_cgpa_match(
            student_profile['cgpa'],
            student_profile['cgpa_scale'],
            program['min_cgpa'],
            program['cgpa_scale'] if program['cgpa_scale'] else 4.0
        )
        
        language_score, language_feedback = self.calculate_language_match(
            student_profile.get('toefl'),
            student_profile.get('ielts'),
            student_profile.get('cambridge'),
            program['min_toefl_score'],
            program['min_ielts_score'],
            program['min_cambridge_score']
        )
        
        field_score, field_feedback = self.calculate_field_match(
            student_profile['field'],
            program['accepted_degree_fields'],
            program['field']  # Pass program's own field
        )
        
        work_exp_score, work_exp_feedback = self.calculate_work_experience_match(
            student_profile['work_experience'],
            program['work_experience_years']
        )
        
        # Total: 50 + 25 + 15 + 5 + 5 (citizenship) = 100
        total_score = cgpa_score + language_score + field_score + work_exp_score + 5
        
        # CAP AT 100 (fix for >100% issue)
        total_score = min(100, total_score)
        
        return {
            'program_id': program['program_id'],
            'program_name': program['program_name'],
            'acronym': program['acronym'],
            'field': program['field'],
            'website': program['website'],
            'consortium': program['consortium'],
            'scholarship': program['scholarship'],
            'deadline': program['application_deadline'],
            'overall_match': int(total_score),
            'cgpa_score': int(cgpa_score),
            'cgpa_feedback': cgpa_feedback,
            'language_score': int(language_score),
            'language_feedback': language_feedback,
            'field_score': int(field_score),
            'field_feedback': field_feedback,
            'work_exp_score': int(work_exp_score),
            'work_exp_feedback': work_exp_feedback
        }
    
    def match_programs(self, student_profile: Dict, programs_df: pd.DataFrame) -> List[Dict]:
        """Match student against all programs"""
        results = []
        
        for idx, program in programs_df.iterrows():
            match_result = self.calculate_total_match(student_profile, program)
            results.append(match_result)
        
        # Sort by match score descending
        results.sort(key=lambda x: x['overall_match'], reverse=True)
        return results
    
    def get_top_recommendations(self, match_results: List[Dict], top_n: int = 3) -> List[Dict]:
        """Get top N program recommendations"""
        return match_results[:top_n]
    
    def get_match_color(self, score: int) -> str:
        """Get color coding for match score"""
        if score >= 80:
            return "green"
        elif score >= 60:
            return "orange"
        else:
            return "red"
    
    def close(self):
        """Close database connection"""
        self.conn.close()