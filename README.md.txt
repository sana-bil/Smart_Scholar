# ScholarAI - Erasmus Mundus Program Matcher

An intelligent NLP-powered system that matches students with Erasmus Mundus Master's programs.

## Features

✨ **Smart Matching**: Field-first matching algorithm
🎯 **89 Programs**: All official Erasmus Mundus Master's programs
📊 **Intelligent Scoring**: Color-coded match percentages (Green >80%, Yellow 60-80%, Red <60%)
🏆 **Top Recommendations**: Personalized program suggestions
📄 **PDF Reports**: Downloadable match reports with detailed analysis

## Tech Stack

- **Frontend**: Streamlit
- **Backend Logic**: Python with NLP
- **Database**: SQL Server
- **NLP**: spaCy, NLTK, Regex-based extraction

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run src/streamlit_app.py
```

## How It Works

1. Enter your academic profile (CGPA, field, English scores, experience)
2. Select or filter programs by field
3. Get intelligent match scores based on:
   - Field alignment (50%)
   - CGPA requirements (25%)
   - Language proficiency (15%)
   - Work experience (5%)
   - Citizenship (5%)
4. View top recommendations with detailed feedback
5. Download PDF report with all matches

Smart Scholar/
│
├── application/
│   ├── streamlit_app.py        # Main Streamlit application
│   ├── MatchingAlgo.py         # Matching logic
│   ├── nlpParser.py            # NLP parsing
│   ├── insertion.py            # Data insertion logic
│   ├── testconnection.py       # Database connection testing
│   └── __pycache__/
│
├── SQL script/
│   └── Main DB.sql              # SQL Server database schema
│
├── dataset.txt                  # Raw dataset (ignored in Git)
├── dataset_clean.txt            # Cleaned dataset (ignored in Git)
├── .env.example                 # Environment variables template
├── .gitignore
└── README.md

## Database Schema

**EmjmdPrograms**: 89 Erasmus Mundus Master's programs
**ProgramRequirements**: Parsed requirements (CGPA, TOEFL, IELTS, etc.)

## Author
Sanabil Tanveer
Built for Erasmus Mundus applicants worldwide

