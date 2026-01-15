import spacy
import pandas as pd
import pyodbc
import re
from datetime import datetime

# Load spaCy model
print("Loading spaCy NLP model...")
nlp = spacy.load("en_core_web_sm")
print("✓ spaCy model loaded!")

# SQL Server Connection
conn = pyodbc.connect(
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=DESKTOP-2G14Q4N\\MSSQLSERVER01;'
    'Database=SmartScholar;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()


# ==================== SPACY-BASED PARSERS ====================

def parse_toefl_spacy(doc, text):
    """Extract TOEFL using spaCy + regex fallback"""
    # spaCy finds NUMBERS
    numbers = [ent.text for ent in doc.ents if ent.label_ == "CARDINAL"]
    
    # Look for TOEFL context
    if "TOEFL" in text or "TOEFL iBT" in text:
        # Find numbers near "TOEFL"
        pattern = r'TOEFL\s+(?:iBT)?\s*(?:≥|>=|minimum\s+)?(\d{2,3})'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            score = int(match.group(1))
            if 50 <= score <= 120:
                return score, 0.95  # High confidence
    
    return None, 0.0

def parse_ielts_spacy(doc, text):
    """Extract IELTS using spaCy + regex"""
    # spaCy finds CARDINAL numbers (decimals)
    
    if "IELTS" in text or "IELTS Academic" in text:
        pattern = r'IELTS\s+(?:Academic)?\s*(?:≥|>=)?(\d\.\d)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            score = float(match.group(1))
            if 0.0 <= score <= 9.0:
                return score, 0.95  # High confidence
    
    return None, 0.0

def parse_cambridge_spacy(doc, text):
    """Extract Cambridge certificate using spaCy"""
    # Look for C1, C2 levels
    pattern = r'(?:Cambridge|C[12])\s*(?:Advanced|Proficiency|[C][12])?'
    
    if "Cambridge" in text or re.search(r'\bC[12]\b', text):
        c_match = re.search(r'\b(C[12])\b', text)
        if c_match:
            return c_match.group(1), 0.95
    
    return None, 0.0

def parse_cgpa_spacy(doc, text):
    """Extract CGPA using spaCy NER for numbers"""
    cgpa = None
    confidence = 0.0
    
    # Look for GPA/CGPA mentions
    if "GPA" in text or "CGPA" in text or "grade point" in text.lower():
        # spaCy recognizes CARDINAL and finds numbers
        for ent in doc.ents:
            if ent.label_ == "CARDINAL":
                try:
                    val = float(ent.text)
                    if 0.0 <= val <= 5.0 and (cgpa is None or val > cgpa):
                        cgpa = val
                        confidence = 0.90
                except:
                    pass
        
        # Fallback regex
        if cgpa is None:
            pattern = r'(?:GPA|CGPA|grade point average)\s*(?:of\s+)?(?:≥|>=|minimum\s+)?(\d\.\d+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cgpa = float(match.group(1))
                confidence = 0.85
    
    return cgpa, confidence

def parse_cgpa_scale_spacy(doc, text):
    """Determine CGPA scale using spaCy"""
    # Look for scale indicators
    if "/5" in text or "out of 5" in text.lower() or "scale of 5" in text.lower():
        return 5.0
    elif "/10" in text or "out of 10" in text.lower() or "scale of 10" in text.lower():
        return 10.0
    
    return 4.0

def parse_work_experience_spacy(doc, text):
    """Extract work experience using spaCy NER"""
    years = None
    confidence = 0.0
    
    # Look for year/experience context
    if "year" in text.lower() and "experience" in text.lower():
        # spaCy finds CARDINAL numbers
        for ent in doc.ents:
            if ent.label_ == "CARDINAL":
                try:
                    val = int(float(ent.text))
                    if 0 <= val <= 50 and val > 0:
                        years = val
                        confidence = 0.90
                except:
                    pass
        
        # Fallback regex
        if years is None:
            pattern = r'(?:minimum\s+)?(\d+)\+?\s+years?\s+(?:of\s+)?(?:work\s+)?experience'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                years = int(match.group(1))
                confidence = 0.85
    
    return years, confidence

def parse_accepted_fields_spacy(doc, text):
    """Extract accepted degree fields using spaCy NER"""
    fields = set()
    
    # Field keywords
    field_keywords = {
        'Computer Science': ['computer science', 'cs', 'computing', 'software'],
        'Engineering': ['engineering', 'mechanical', 'electrical', 'civil', 'chemical'],
        'Mathematics': ['mathematics', 'math', 'mathematical', 'maths'],
        'Physics': ['physics', 'physical'],
        'Chemistry': ['chemistry', 'chemical'],
        'Biology': ['biology', 'biological', 'life science'],
        'Medicine': ['medicine', 'medical', 'health'],
        'Business': ['business', 'commerce', 'management'],
        'Economics': ['economics', 'economic'],
        'Law': ['law', 'legal'],
        'Psychology': ['psychology'],
        'Statistics': ['statistics', 'statistical'],
        'Data Science': ['data science', 'data analytics'],
        'IT': ['it', 'information technology'],
        'Architecture': ['architecture'],
        'Environmental Science': ['environmental', 'sustainability'],
        'Humanities': ['humanities', 'language', 'literature', 'history'],
    }
    
    text_lower = text.lower()
    
    # Use spaCy NER to find domain-specific entities
    for ent in doc.ents:
        ent_text = ent.text.lower()
        
        # Check if entity matches any field keywords
        for field, keywords in field_keywords.items():
            for keyword in keywords:
                if keyword in ent_text or keyword in text_lower:
                    fields.add(field)
    
    # Fallback: keyword matching if NER didn't catch
    if not fields:
        for field, keywords in field_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    fields.add(field)
    
    if fields:
        return ', '.join(sorted(list(fields)))
    return None

def parse_english_required_spacy(doc, text):
    """Check if English is required using spaCy"""
    english_keywords = ['English', 'TOEFL', 'IELTS', 'Cambridge', 'proficiency', 'language test']
    
    for keyword in english_keywords:
        if keyword.lower() in text.lower():
            return 1
    
    return 0

def parse_requirement_row_spacy(program_id, requirement_text, program_name=""):
    """Parse requirement using spaCy NLP"""
    
    if not requirement_text:
        return None
    
    try:
        # Process text with spaCy
        doc = nlp(requirement_text)
        
        # Extract all components
        min_toefl, toefl_conf = parse_toefl_spacy(doc, requirement_text)
        min_ielts, ielts_conf = parse_ielts_spacy(doc, requirement_text)
        min_cambridge, cambridge_conf = parse_cambridge_spacy(doc, requirement_text)
        min_cgpa, cgpa_conf = parse_cgpa_spacy(doc, requirement_text)
        cgpa_scale = parse_cgpa_scale_spacy(doc, requirement_text)
        work_exp, work_exp_conf = parse_work_experience_spacy(doc, requirement_text)
        english_req = parse_english_required_spacy(doc, requirement_text)
        accepted_fields = parse_accepted_fields_spacy(doc, requirement_text)
        
        # Average confidence across all extractions
        confidences = [c for c in [toefl_conf, ielts_conf, cgpa_conf, work_exp_conf] if c > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.70
        
        return {
            'program_id': program_id,
            'min_toefl_score': min_toefl,
            'min_ielts_score': min_ielts,
            'min_cambridge_score': min_cambridge,
            'min_cgpa': min_cgpa,
            'cgpa_scale': cgpa_scale,
            'english_required': english_req,
            'work_experience_years': work_exp,
            'accepted_degree_fields': accepted_fields,
            'requirement_text_raw': requirement_text,
            'parsing_confidence': round(avg_confidence, 2)
        }
    
    except Exception as e:
        print(f"❌ Error parsing program {program_id}: {str(e)}")
        return None


# ==================== MAIN EXECUTION ====================

try:
    print("\n📖 Reading programs from SmartScholar database...")
    
    # Read all programs WITH requirement text
    query = """
    SELECT program_id, program_name, requirement_text_raw 
    FROM EmjmdPrograms 
    WHERE requirement_text_raw IS NOT NULL
    """
    programs_df = pd.read_sql(query, conn)
    
    print(f"✓ Found {len(programs_df)} programs with requirement text")
    
    # Parse each program using spaCy
    parsed_requirements = []
    
    for idx, row in programs_df.iterrows():
        program_id = row['program_id']
        requirement_text = row['requirement_text_raw']
        program_name = row['program_name']
        
        parsed = parse_requirement_row_spacy(program_id, requirement_text, program_name)
        
        if parsed:
            parsed_requirements.append(parsed)
            
            # Print progress
            toefl = parsed['min_toefl_score'] or 'N/A'
            ielts = parsed['min_ielts_score'] or 'N/A'
            cgpa = parsed['min_cgpa'] or 'N/A'
            conf = parsed['parsing_confidence']
            
            print(f"✓ Program {program_id}: TOEFL={toefl}, IELTS={ielts}, CGPA={cgpa}, Confidence={conf:.2f}")
    
    print(f"\n✅ Successfully parsed {len(parsed_requirements)} programs using spaCy NLP!")
    
    # ==================== RECREATE TABLE ====================
    
    print("\n🔨 Dropping old ProgramRequirements table...")
    
    drop_sql = "IF OBJECT_ID('dbo.ProgramRequirements', 'U') IS NOT NULL DROP TABLE dbo.ProgramRequirements;"
    cursor.execute(drop_sql)
    conn.commit()
    
    print("🔨 Creating new ProgramRequirements table...")
    
    create_table_sql = """
    CREATE TABLE ProgramRequirements (
        requirement_id INT PRIMARY KEY IDENTITY(1,1),
        program_id INT NOT NULL,
        min_toefl_score INT,
        min_ielts_score DECIMAL(3,1),
        min_cambridge_score NVARCHAR(10),
        min_cgpa DECIMAL(3,2),
        cgpa_scale DECIMAL(3,1),
        english_required BIT,
        work_experience_years INT,
        accepted_degree_fields NVARCHAR(MAX),
        requirement_text_raw NVARCHAR(MAX),
        parsing_confidence DECIMAL(3,2),
        created_at DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (program_id) REFERENCES EmjmdPrograms(program_id)
    );
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    print("✓ Table created successfully!")
    
    # ==================== INSERT PARSED DATA ====================
    
    print("\n📤 Inserting spaCy-parsed requirements into database...")
    
    insert_sql = """
    INSERT INTO ProgramRequirements 
    (program_id, min_toefl_score, min_ielts_score, min_cambridge_score, min_cgpa, 
     cgpa_scale, english_required, work_experience_years, accepted_degree_fields, 
     requirement_text_raw, parsing_confidence)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    for req in parsed_requirements:
        cursor.execute(insert_sql, (
            req['program_id'],
            req['min_toefl_score'],
            req['min_ielts_score'],
            req['min_cambridge_score'],
            req['min_cgpa'],
            req['cgpa_scale'],
            req['english_required'],
            req['work_experience_years'],
            req['accepted_degree_fields'],
            req['requirement_text_raw'],
            req['parsing_confidence']
        ))
    
    conn.commit()
    print(f"✅ Successfully inserted {len(parsed_requirements)} spaCy-parsed requirements!")
    
    # ==================== VERIFICATION ====================
    
    print("\n🔍 Verification - Sample parsed data (Top 10):")
    verify_sql = """
    SELECT TOP 10 program_id, min_toefl_score, min_ielts_score, min_cgpa, 
                  accepted_degree_fields, parsing_confidence 
    FROM ProgramRequirements 
    ORDER BY program_id
    """
    verify_df = pd.read_sql(verify_sql, conn)
    print(verify_df.to_string())
    
    print("\n✓ spaCy NLP parsing complete!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
    print("\n✓ Database connection closed.")