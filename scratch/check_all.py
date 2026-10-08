import docx

doc_path = r'C:\Users\zhaoj\OneDrive\2026工作\消毒报告3.0版\消毒科采样单\济宁市公共卫生医疗中心 2026.7.29.docx'
doc = docx.Document(doc_path)

records = []
for t in doc.tables:
    for row in t.rows[1:]:
        c = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
        if c[0] and c[0].startswith('2026'):
            records.append({
                'id': c[0],
                'num': int(c[0][-3:]),
                'loc': c[1],
                'cat': c[2],
                'name': c[3],
                'dur': c[4],
                'area': c[5],
                'bac': c[6],
                'rl': c[7],
                'jp': c[8],
                'tl': c[9],
                'uv': c[10]
            })

print(f"Total samples: {len(records)}")
for r in records:
    print(f"{r['num']:03d} | {r['id']} | {r['loc']} | {r['name']} | {r['area']} | UV={r['uv']}")
