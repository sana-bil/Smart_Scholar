-- Drop the old table
DROP TABLE EmjmdPrograms;

-- Recreate it with PRIMARY KEY from the start
CREATE TABLE EmjmdPrograms (
    program_id INT PRIMARY KEY NOT NULL,
    program_name NVARCHAR(500),
    acronym NVARCHAR(100),
    consortium NVARCHAR(MAX),
    website NVARCHAR(500),
    field NVARCHAR(300),
    degree_requirement NVARCHAR(MAX),
    accepted_fields NVARCHAR(MAX),
    cgpa_gpa NVARCHAR(200),
    english_requirement NVARCHAR(MAX),
    english_exemptions NVARCHAR(MAX),
    work_experience NVARCHAR(MAX),
    application_deadline NVARCHAR(200),
    selection_process NVARCHAR(MAX),
    scholarship NVARCHAR(MAX),
    requirement_text_raw NVARCHAR(MAX)
);

-- Now reload the data
BULK INSERT EmjmdPrograms
FROM 'C:\Users\Home\Documents\Projects\Smart Scholar\dataset_clean.txt'
WITH (
    FIELDTERMINATOR = '|',
    ROWTERMINATOR = '\n',
    FIRSTROW = 2,
    KEEPNULLS
);

-- Verify
SELECT * FROM EmjmdPrograms;
