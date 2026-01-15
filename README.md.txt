# 🎓 ScholarAI: AI-Powered Erasmus Mundus Matcher

Smart Scholar is a full-stack AI application designed to bridge the gap between students and the complex requirements of Erasmus Mundus Joint Masters (EMJM). 
It uses Natural Language Processing (NLP) to extract program criteria and Semantic Similarity to match student backgrounds with 89 academic programs.

## 🚀 The AI Pipeline (How it's Built)

1. **Data Extraction (ETL):** Aggregated raw data using Perplexity/Claude, cleaned via Python, and stored in a Relational SQL Server database.
2. **NLP Requirements Parsing:** Used **spaCy (NER)** and custom Regex heuristics to transform unstructured requirement text into structured data (CGPA, IELTS, TOEFL, Exp).
3. **Semantic Matching Engine:** Powered by **Sentence-Transformers (`all-MiniLM-L6-v2`)**. It calculates the Cosine Similarity between a student's degree and program fields, moving beyond simple keyword matching.
4. **Professional Reporting:** Custom FPDF engine that generates a single-page Executive Compatibility Report.

## ✨ Key Features

- 🧠 **Vector-Based Matching**: Understands that "Software Engineering" is similar to "Computer Science" using AI embeddings.
- 🔍 **Domain Guardrails**: Prevents mismatches between unrelated fields (e.g., Arts vs. Physics) using an inference layer.
- 📈 **Dynamic Scoring**: A 100-point weighted algorithm (Field: 50%, CGPA: 25%, Language: 15%, Experience: 10%).
- 📄 **Executive PDF Export**: Generates professional, one-page compatibility dossiers for applicants.

## 🛠 Tech Stack

- **Frontend**: Streamlit (Dashboard & Metrics)
- **NLP/AI**: spaCy (Entity Recognition), Sentence-Transformers (Embeddings)
- **Database**: Microsoft SQL Server (T-SQL)
- **Backend**: Python (pandas, pyodbc, torch)

## 📂 Project Structure



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

