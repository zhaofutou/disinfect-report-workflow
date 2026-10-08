import docx
import sqlite3
import re
from pathlib import Path

# Path to docx
docx_path = r'C:\Users\zhaoj\OneDrive\2026工作\消毒报告3.0版\消毒科采样单\济宁市公共卫生医疗中心 2026.7.29.docx'
db_path = r'C:\Users\zhaoj\disinfect-report-workflow\disinfect.db'

# 1. Connect SQLite DB
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS sample_details")
cur.execute("""
CREATE TABLE sample_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    client TEXT,
    sampleID TEXT NOT NULL,
    sampleLocation TEXT,
    sampleCategory TEXT,
    sampleName TEXT,
    sampleDuration TEXT,
    sampleArea TEXT,
    bacCount INTEGER DEFAULT 0,
    ronglian INTEGER DEFAULT 0,
    jinpu INTEGER DEFAULT 0,
    tonglv INTEGER DEFAULT 0,
    UV INTEGER DEFAULT 0,
    observation TEXT,
    result TEXT
);
""")

# 2. Extract sample info from docx
doc = docx.Document(docx_path)
client_name = '济宁市公共卫生医疗中心'
event_id = '202605029'

records = []
for t in doc.tables:
    for row in t.rows[1:]:
        c = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
        sid = c[0]
        if not sid or not sid.startswith('2026'):
            continue
        
        loc = c[1]
        cat = c[2]
        name = c[3]
        dur = c[4]
        area = c[5]
        bac = 1 if '√' in c[6] else 0
        rl = 1 if '√' in c[7] else 0
        jp = 1 if '√' in c[8] else 0
        tl = 1 if '√' in c[9] else 0
        uv = 1 if (c[10] and any(ch.isdigit() for ch in c[10])) else (1 if '√' in c[10] else 0)
        
        records.append((
            event_id, client_name, sid, loc, cat, name, dur, area,
            bac, rl, jp, tl, uv
        ))

cur.executemany("""
INSERT INTO sample_details 
(event, client, sampleID, sampleLocation, sampleCategory, sampleName, sampleDuration, sampleArea,
 bacCount, ronglian, jinpu, tonglv, UV)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", records)
conn.commit()

print(f"Inserted {len(records)} records into sample_details table.")

# 3. Define complete observation map for all 168 samples
obs_map = {}

# 1-30 from IMG_1186.jpeg
img_1_30 = {
    1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 5,
    11: 2, 12: 0, 13: 0, 14: 85, 15: 1, 16: 0, 17: 0, 18: 0, 19: 1, 20: 0,
    21: 0, 22: 0, 23: 0, 24: 0, 25: 0, 26: 0, 27: 0, 28: 0, 29: 0, 30: 2
}
obs_map.update(img_1_30)

# 31-60 from IMG_1178.jpeg
img_31_60 = {
    31: 21, 32: 35, 33: 0, 34: 2, 35: 0, 36: 0, 37: 0, 38: 0, 39: 1, 40: 1,
    41: 55, 42: 0, 43: 0, 44: 0, 45: 11, 46: 452, 47: 0, 48: 4, 49: 2, 50: 0,
    51: 235, 52: 9, 53: 0, 54: 4, 55: 186, 56: 0, 57: 0, 58: 0, 59: 0, 60: 0
}
obs_map.update(img_31_60)

# 61-90 from IMG_1179.jpeg
img_61_90 = {
    61: 0, 62: 442, 63: 1, 64: 26, 65: 0, 66: 0, 67: 0, 68: 0, 69: 0, 70: 0,
    71: 0, 72: 0, 73: 1, 74: 0, 75: 0, 76: 186, 77: 72, 78: 0, 79: 6, 80: 0,
    81: 0, 82: 0, 83: 0, 84: 0, 85: 0, 86: 0, 87: 0, 88: 0, 89: 566, 90: 0
}
obs_map.update(img_61_90)

# 91 defaults to 0
obs_map[91] = 0

# 92-104 Scope Tube #s (IMG_1185)
scope_obs = {
    92: 0, 93: 0, 94: 0, 95: 0, 96: 0, 97: 0, 98: 1,
    99: 0, 100: 0, 101: 0, 102: 0, 103: 0, 104: 0
}
obs_map.update(scope_obs)

# 105 Air sample
obs_map[105] = "0,0,1"

# 106-120 from IMG_1177/1181
img_106_120 = {
    106: 31, 107: 9, 108: 0, 109: 0, 110: 0, 111: 0, 112: 0, 113: 0, 114: 0,
    115: 0, 116: 0, 117: 0, 118: 0, 119: 311, 120: 0
}
obs_map.update(img_106_120)

# 121-150 from IMG_1180
img_121_150 = {
    121: 12, 122: 26, 123: 0, 124: 0, 125: 0, 126: 0, 127: 0, 128: 1, 129: 0,
    130: 16, 131: 0, 132: 0, 133: 0, 134: 0, 135: 1, 136: 0, 137: 0, 138: 0,
    139: 0, 140: 0, 141: 0, 142: 0, 143: 0, 144: 1, 145: 74, 146: 0, 147: 0,
    148: 1, 149: 0, 150: 0
}
obs_map.update(img_121_150)

# 151 defaults to 0
obs_map[151] = 0

# 152-168 Air samples from IMG_1182 / IMG_1184
air_obs = {
    152: "0,0,0",
    153: "1,0,0,0,1",
    154: "0,0,0,0",
    155: "1,0,1,1,0",
    156: "0,0,0",
    157: "0,0",
    158: "0,0",
    159: "0,0,0",
    160: "0,0,0",
    161: "0",
    162: "2,1,0",
    163: "0,0,0,2",
    164: "1,1,2",
    165: "0,0,0",
    166: "3,0,0",
    167: "1,2,0",
    168: "1,2,1"
}
obs_map.update(air_obs)

# Helper to check if disinfectant liquid
LIQUID_PATTERNS = ['酒精', '消毒剂', '碘伏', '邻苯二甲醛', '过氧乙酸', '手消']
def is_disinfectant(sample_name):
    return any(p in sample_name for p in LIQUID_PATTERNS)

# 4. Update observations & calculate results
cur.execute("SELECT sampleID, sampleName, sampleArea, sampleDuration FROM sample_details ORDER BY sampleID")
rows = cur.fetchall()

updated_count = 0
for sid, name, area, dur in rows:
    num = int(sid[-3:])
    val = obs_map.get(num, None)
    if val is None:
        continue
    
    # Character replacement φ -> ⌀
    name_clean = name.replace('φ', '⌀').replace('Φ', '⌀')
    
    # Format observation cell
    if is_disinfectant(name_clean):
        obs_text = f"{val}(十倍稀释)"
    else:
        obs_text = str(val)
    
    # Calculate result
    result_text = None
    if '紫外线' in name_clean:
        result_text = None
    elif ',' in str(val):
        # Air sample with comma
        plates = [float(x.strip()) for x in str(val).split(',')]
        avg = sum(plates) / len(plates)
        dur_str = f"·{dur}min" if dur else ""
        result_text = f"{avg:.1f} CFU/⌀90mm平皿{dur_str}"
    else:
        try:
            obs_num = float(val)
            if is_disinfectant(name_clean):
                # Disinfectant: result cell must NOT contain (十倍稀释)
                if obs_num == 0:
                    result_text = "<10 CFU/mL"
                else:
                    result_text = f"{obs_num * 10:.0f} CFU/mL"
            elif '空气' in name_clean or '气' in name_clean:
                dur_str = f"·{dur}min" if dur else ""
                result_text = f"{obs_num:.1f} CFU/⌀90mm平皿{dur_str}"
            elif area:
                m = re.search(r'(\d+)', str(area))
                if m:
                    area_num = float(m.group(1))
                    if obs_num == 0:
                        result_text = "<0.2"
                    else:
                        result_text = f"{obs_num * 10 / area_num:.1f}"
                else:
                    result_text = str(obs_num)
            else:
                result_text = str(obs_num)
        except Exception as e:
            result_text = str(val)

    cur.execute("""
    UPDATE sample_details
    SET sampleName = ?, observation = ?, result = ?
    WHERE sampleID = ?
    """, (name_clean, obs_text, result_text, sid))
    updated_count += cur.rowcount

conn.commit()
print(f"Updated observation & result for {updated_count} / {len(rows)} samples.")
conn.close()
