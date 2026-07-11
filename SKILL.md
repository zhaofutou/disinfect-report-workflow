---
name: disinfect-report-workflow
description: Process CDC disinfection monitoring reports — extract from photos/docx, deposit into Supabase
triggers:
  - disinfection report
  - CDC inspection
  - 消毒监测
  - 委托协议书
  - sample details
  - observation results
---

# Disinfection Report Workflow

## Purpose
Extract inspection data from Jining CDC disinfection monitoring reports and deposit into Supabase database.

## Three Data Sources

### 1. Event Photos (委托协议书)
**Location:** `event_deposition/`
**Tool:** `vision_analyze` on each photo
**Extract:** eventID, sampleCount, clientInfo, inspectionDate, inspectionTarget, inspectionStandards
**Output:** `event_inspections` table

**Step-by-step:**
1. List files in event_deposition/
2. For each photo, use vision_analyze with extraction prompt
3. Parse: eventID = report number, sampleCount = sample ID range
4. Insert into event_inspections via direct PostgreSQL

**Extraction prompt:**
```
Extract these fields from this Chinese CDC inspection form:
1) 报告书号/样品编号 (report/sample ID)
2) 客户名称 (client name)
3) 检测日期 (inspection date)
4) 检测项目 (inspection target)
5) 检测评价依据 (inspection standards/evaluation basis)
Return the raw Chinese text for each field.
```

### 2. Sample Info (docx)
**Location:** `sample_info/`
**Tool:** `python-docx` library
**Extract:** sampleID, sampleLocation, sampleName, sampleArea, bacteria results
**Output:** `sample_details` table

**Step-by-step:**
1. List .docx files in sample_info/
2. Infer client name from filename using CLIENT_MAPPINGS
3. Parse tables: skip header row, extract columns 0-10
4. Convert √ marks to 1, empty to 0
5. For UV column: if has numeric value → 1, else 0
6. Insert into sample_details

**Run:** `python3 scripts/extract_samples.py`

### 3. Observation Results (JPG)
**Location:** `observation_results/`
**Tool:** `vision_analyze` on each photo
**Extract:** observation values per sample
**Output:** Updates `observation` column in `sample_details`

**Step-by-step:**
1. Files should be named by eventID (e.g., 202605017.jpg)
2. Use vision_analyze to extract red numbers and values
3. Map red number N → sampleID = eventID + str(N).zfill(3)
4. For air samples: match handwritten dept to DB location
5. Call update_observations_batch() to insert data

**Extraction prompt:**
```
Extract ALL data from this observation result sheet:
1) For each red number with a value, what is the observation value?
2) For air samples (department groups), what are the handwritten 
   department names and comma-separated values?
Return structured data.
```

## Key Rules

1. **UV column:** If docx has numeric value for 紫外线灯辐射照度 → mark as 1
2. **Air samples:** Store comma-separated values as-is (e.g., "0,1,1,0,0")
3. **Blank observations:** Skip entries with no value
4. **Client mapping:** Infer from filename keywords (西院区, 兖州院区, etc.)
5. **Fuzzy matching:** Use semantic mappings for handwritten locations

## Database Access

**Direct PostgreSQL** (for any SQL including DDL):
```python
conn = psycopg2.connect(
    host="aws-0-ap-southeast-1.pooler.supabase.com",
    port=6543,
    database="postgres",
    user="postgres.npipndqgrfehecmnpmiw",
    password="TfecmNjxDVyaMlXg"
)
```

**Supabase client** (for CRUD operations):
```python
from supabase import create_client
client = create_client(url, service_role_key)
```

## File Structure
```
workflow/
├── config/config.yaml        # Supabase credentials
├── scripts/
│   ├── utils.py              # Shared utilities
│   ├── setup_db.py           # Create tables
│   ├── extract_samples.py    # Process docx files
│   └── extract_observations.py # Process observation JPGs
├── templates/
│   └── department_mappings.yaml # Handwritten → DB mappings
└── references/
    └── table_schemas.md      # Database schema docs
```

## Dependencies
```
pip install psycopg2-binary python-docx pyyaml supabase
```
