import re
import pandas as pd
import pyodbc
from datetime import datetime

# SQL Server Connection with Windows Authentication
conn = pyodbc.connect(
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=DESKTOP-2G14Q4N\\MSSQLSERVER01;'
    'Database=SmartScholar;'
    'Trusted_Connection=yes;'
)

cursor = conn.cursor()


# NLP PARSER - Extract Requirements from Text


def parse_toefl(text):
    """Extract minimum TOEFL score"""
    if not text:
        return None
    
    # Patterns: "TOEFL iBT ≥ 90", "TOEFL 90", "TOEFL iBT minimum 90"
    patterns = [
        r'TOEFL\s+iBT\s*(?:≥|>=|minimum\s+|score\s+)?(\d{2,3})',
        r'TOEFL\s*(?:iBT)?\s*(?:≥|>=)?(\d{2,3})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 50 <= score <= 120:  # Valid TOEFL range
                return score
    return None

def parse_ielts(text):
    """Extract minimum IELTS score"""
    if not text:
        return None
    
    # Patterns: "IELTS ≥ 6.5", "IELTS 6.5", "IELTS Academic ≥ 6.5"
    patterns = [
        r'IELTS\s+(?:Academic)?\s*(?:≥|>=)?(\d\.\d)',
        r'IELTS\s*(?:≥|>=)?(\d\.\d)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            if 0.0 <= score <= 9.0:  # Valid IELTS range
                return score
    return None

def parse_cambridge(text):
    """Extract Cambridge certificate level"""
    if not text:
        return None
    
    # Patterns: "Cambridge C1", "Cambridge C2", "C1 Advanced", "C2 Proficiency"
    patterns = [
        r'Cambridge\s+(C[12])',
        r'(C[12])\s+(?:Advanced|Proficiency)',
        r'(C[12])\s+Advanced',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def parse_cgpa(text):
    """Extract minimum CGPA/GPA requirement"""
    if not text:
        return None
    
    # Patterns: "GPA 3.0", "CGPA 3.5/4.0", "minimum GPA 3.0", "≥ 3.0"
    patterns = [
        r'(?:GPA|CGPA)\s*(?:of\s+)?(?:≥|>=|minimum\s+)?(\d\.\d+)',
        r'(?:≥|>=)\s*(\d\.\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            if 0.0 <= score <= 5.0:  # Valid GPA range
                return score
    return None

def parse_cgpa_scale(text):
    """Determine CGPA scale (4.0, 5.0, 10.0)"""
    if not text:
        return 4.0
    
    # Patterns: "3.0/4.0", "out of 5.0", "on a scale of 10"
    if '/5' in text or 'out of 5' in text.lower():
        return 5.0
    elif '/10' in text or 'scale of 10' in text.lower():
        return 10.0
    
    return 4.0

def parse_english_required(text):
    """Check if English is required"""
    if not text:
        return 0
    
    english_required_keywords = ['English', 'TOEFL', 'IELTS', 'Cambridge', 'proficiency', 'certificate']
    
    for keyword in english_required_keywords:
        if keyword.lower() in text.lower():
            return 1
    return 0

def parse_work_experience(text):
    """Extract work experience requirement (in years)"""
    if not text:
        return None
    
    # Patterns: "2+ years", "2 years", "minimum 3 years"
    patterns = [
        r'(?:minimum\s+)?(\d+)\+?\s+years?\s+(?:of\s+)?(?:work\s+)?experience',
        r'(\d+)\s+years?\s+(?:experience|professional)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            years = int(match.group(1))
            if 0 <= years <= 50:  # Valid range
                return years
    return None

def parse_accepted_fields(text):
    """Extract accepted degree fields"""
    if not text:
        return None
    
    # Look for field mentions
    fields = []
    field_keywords = [
        'Computer Science', 'Engineering', 'Mathematics', 'Physics', 'Chemistry',
        'Biology', 'Medicine', 'Pharmacy', 'Business', 'Economics', 'Law',
        'Psychology', 'Sociology', 'History', 'Languages', 'Architecture',
        'Environmental Science', 'Agriculture', 'Geology', 'Astronomy',
        'Statistics', 'Data Science', 'IT', 'Informatics'
    ]
    
    for field in field_keywords:
        if field.lower() in text.lower():
            fields.append(field)
    
    if fields:
        return ', '.join(list(set(fields)))  # Remove duplicates
    return None

def parse_requirement_row(program_id, requirement_text):
    """Parse a single requirement row"""
    try:
        return {
            'program_id': program_id,
            'min_toefl_score': parse_toefl(requirement_text),
            'min_ielts_score': parse_ielts(requirement_text),
            'min_cambridge_score': parse_cambridge(requirement_text),
            'min_cgpa': parse_cgpa(requirement_text),
            'cgpa_scale': parse_cgpa_scale(requirement_text),
            'english_required': parse_english_required(requirement_text),
            'work_experience_years': parse_work_experience(requirement_text),
            'accepted_degree_fields': parse_accepted_fields(requirement_text),
            'requirement_text_raw': requirement_text,
            'parsing_confidence': 0.85  # Default confidence
        }
    except Exception as e:
        print(f"Error parsing row {program_id}: {str(e)}")
        return None

 
# READ DATA FROM SQL SERVER


try:
    print("📖 Reading programs from SmartScholar database...")
    
    # Read all programs
    query = "SELECT program_id, program_name, requirement_text_raw FROM EmjmdPrograms"
    programs_df = pd.read_sql(query, conn)
    
    print(f"✓ Found {len(programs_df)} programs")
    
    # Parse each program
    parsed_requirements = []
    
    for idx, row in programs_df.iterrows():
        program_id = row['program_id']
        requirement_text = row['requirement_text_raw']
        program_name = row['program_name']
        
        parsed = parse_requirement_row(program_id, requirement_text)
        
        if parsed:
            parsed_requirements.append(parsed)
            
            # Print progress
            toefl = parsed['min_toefl_score'] or 'N/A'
            ielts = parsed['min_ielts_score'] or 'N/A'
            cgpa = parsed['min_cgpa'] or 'N/A'
            
            print(f"✓ Program {program_id}: TOEFL={toefl}, IELTS={ielts}, CGPA={cgpa}")
    
    print(f"\n✅ Successfully parsed {len(parsed_requirements)} programs!")

    # CREATE ProgramRequirements TABLE

    
    print("\n🔨 Creating ProgramRequirements table...")
    
    create_table_sql = """
    IF OBJECT_ID('dbo.ProgramRequirements', 'U') IS NOT NULL 
        DROP TABLE dbo.ProgramRequirements;
    
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
    

    # INSERT PARSED DATA

    
    print("\n📤 Inserting parsed requirements into database...")
    
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
    print(f"✅ Successfully inserted {len(parsed_requirements)} parsed requirements!")
    
  
    # VERIFICATION
 
    
    print("\n🔍 Verification - Sample parsed data:")
    verify_sql = "SELECT TOP 5 program_id, min_toefl_score, min_ielts_score, min_cgpa FROM ProgramRequirements"
    verify_df = pd.read_sql(verify_sql, conn)
    print(verify_df.to_string())
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
    print("\n✓ Database connection closed.")