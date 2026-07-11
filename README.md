# Disinfection Report Workflow

Automated pipeline for extracting inspection data from CDC disinfection monitoring reports and depositing into Supabase.

## Purpose

Processes three types of documents from Jining CDC disinfection monitoring:

1. **Event Photos** (`event_deposition/`) — 委托协议书 (Entrustment Agreements)
   - Extracts: eventID, sampleCount, clientInfo, inspectionDate, inspectionTarget, inspectionStandards
   - Output: `event_inspections` table

2. **Sample Info** (`sample_info/`) — .docx files with sample details
   - Extracts: sampleID, sampleLocation, sampleName, sampleArea, bacteria test results (bacCount, ronglian, jinpu, tonglv, UV)
   - Output: `sample_details` table

3. **Observation Results** (`observation_results/`) — .jpg photos of handwritten results
   - Extracts: observation values per sample (numeric or comma-separated for air samples)
   - Matches handwritten department names to DB locations via fuzzy matching
   - Output: Updates `observation` column in `sample_details` table

## Quick Start

### 1. Configure Supabase

Copy the config template and fill in your credentials:

```bash
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml` with your Supabase URL, service role key, and database password.

### 2. Setup Database Tables

```bash
python3 scripts/setup_db.py
```

This creates the `event_inspections` and `sample_details` tables if they don't exist.

### 3. Process Event Photos

Place event photos in `event_deposition/` directory, then:

```bash
python3 scripts/extract_events.py
```

Or use the agent workflow: load `SKILL.md` and let the AI extract data from photos using vision.

### 4. Process Sample Info

Place .docx files in `sample_info/` directory, then:

```bash
python3 scripts/extract_samples.py
```

### 5. Process Observation Results

Place .jpg files in `observation_results/` (named by eventID, e.g., `202605017.jpg`), then:

```bash
python3 scripts/extract_observations.py
```

## File Structure

```
workflow/
├── README.md                  # This file
├── SKILL.md                   # Hermes agent skill definition
├── config/
│   ├── config.example.yaml    # Config template
│   └── config.yaml            # Your config (gitignored)
├── scripts/
│   ├── setup_db.py            # Create/update database tables
│   ├── extract_events.py      # Extract from event photos
│   ├── extract_samples.py     # Extract from docx files
│   ├── extract_observations.py # Extract from observation JPGs
│   └── utils.py               # Shared utilities
├── templates/
│   └── department_mappings.yaml # Handwritten → DB location mappings
└── references/
    └── table_schemas.md       # Database schema reference
```

## Database Schema

### event_inspections
| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL PK | Auto-increment ID |
| eventID | TEXT | Report number (e.g., 202605014) |
| sampleCount | TEXT | Sample ID range (e.g., 202605014001-202605014002) |
| clientInfo | TEXT | Client hospital name |
| inspectionDate | DATE | Inspection date |
| inspectionTarget | TEXT | What was tested |
| inspectionStandards | TEXT | Evaluation standards/basis |
| created_at | TIMESTAMPTZ | Record creation time |

### sample_details
| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL PK | Auto-increment ID |
| event | TEXT | Event ID (first 9 chars of sampleID) |
| client | TEXT | Client hospital name |
| sampleID | TEXT | Full sample ID (e.g., 202605017001) |
| sampleLocation | TEXT | Department/location |
| sampleName | TEXT | Sample type |
| sampleArea | TEXT | Sample area (cm², ml, or count) |
| bacCount | INT | Bacteria count (1=present, 0=absent) |
| ronglian | INT | 溶血性链球菌 (1=√, 0=absent) |
| jinpu | INT | 金黄色葡萄球菌 (1=√, 0=absent) |
| tonglv | INT | 铜绿假单胞菌 (1=√, 0=absent) |
| UV | INT | UV radiation (1=has value, 0=absent) |
| observation | TEXT | Observation value (number or comma-separated) |
| created_at | TIMESTAMPTZ | Record creation time |

## Fuzzy Matching for Handwritten Locations

The observation results use handwritten department names that may not exactly match the database. The system uses:

1. **Semantic mappings** — Known equivalents (e.g., CT室→放射科, 牙科→口腔科)
2. **Contains matching** — One string contains the other
3. **Fuzzy matching** — SequenceMatcher similarity > 0.5

See `templates/department_mappings.yaml` for the mapping rules.

## Notes

- UV column: If the original docx has a number value for 紫外线灯辐射照度, mark as 1
- Air samples: Store comma-separated observation values as-is (e.g., "0,1,1,0,0")
- Blank observation entries are skipped
- The `.doc` format may not parse correctly; prefer `.docx`
