#!/usr/bin/env python3
"""Extract sample details from .docx files and insert into Supabase.

Usage:
    python3 extract_samples.py                    # Process all docx in sample_info/
    python3 extract_samples.py file1.docx file2.docx  # Process specific files

Expected docx structure:
    - Tables with columns: 编号, 采样地点, 环境类别, 样品名称, 采样时间, 采样面积, 
      细菌菌落总数, 溶血性链球菌, 金黄色葡萄球菌, 铜绿假单胞菌, 紫外线灯辐射照度
    - First row is header, rest are data rows
    - Multiple tables per document (one per department section)
"""

import sys
import os
sys.path.insert(0, '.')
from pathlib import Path
from docx import Document
from utils import load_config, get_db_connection, to_binary, get_event_id

# Map filenames to client names
# Adjust these mappings for your specific files
CLIENT_MAPPINGS = {
    '西院区': '市直机关医院（西院区）',
    '洸河路院区': '市直机关医院（洸河路院区）',
    '洸河院区': '市直机关医院（洸河路院区）',
    '总院区': '市直机关医院（总院区）',
    '兖州院区': '皮肤病防治院（兖州院区）',
    '济宁院区': '皮肤病防治院（济宁院区）',
}

def infer_client(filename):
    """Infer client name from filename."""
    for keyword, client in CLIENT_MAPPINGS.items():
        if keyword in filename:
            return client
    return None

def extract_from_docx(filepath, client_name=None):
    """Extract sample records from a .docx file.
    
    Returns list of tuples: (event, client, sampleID, sampleLocation, sampleName, 
                             sampleArea, bacCount, ronglian, jinpu, tonglv, uv)
    """
    doc = Document(filepath)
    filename = Path(filepath).name
    
    if client_name is None:
        client_name = infer_client(filename)
    if client_name is None:
        print(f"  ⚠ Cannot infer client from filename: {filename}")
        return []
    
    records = []
    for table in doc.tables:
        for row in table.rows[1:]:  # Skip header
            cells = [cell.text.strip() for cell in row.cells]
            sample_id = cells[0]
            
            # Skip invalid rows
            if not sample_id or not sample_id.startswith('2026'):
                continue
            
            # UV: check if last column has a number value
            uv_raw = cells[10]
            uv_val = 1 if uv_raw and any(c.isdigit() for c in uv_raw) else to_binary(uv_raw)
            
            record = (
                get_event_id(sample_id),   # event
                client_name,                # client
                sample_id,                  # sampleID
                cells[1],                   # sampleLocation
                cells[3],                   # sampleName
                cells[5] if cells[5] else None,  # sampleArea
                to_binary(cells[6]),        # bacCount
                to_binary(cells[7]),        # ronglian
                to_binary(cells[8]),        # jinpu
                to_binary(cells[9]),        # tonglv
                uv_val                      # UV
            )
            records.append(record)
    
    return records

def insert_records(records):
    """Insert records into sample_details table."""
    if not records:
        return 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.executemany("""
    INSERT INTO sample_details 
    (event, client, sampleID, sampleLocation, sampleName, sampleArea, 
     bacCount, ronglian, jinpu, tonglv, UV)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, records)
    
    count = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return count

def main():
    config = load_config()
    sample_dir = Path(__file__).parent.parent / config['paths']['sample_docs']
    
    # Determine files to process
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:]]
    else:
        files = list(sample_dir.glob('*.docx'))
    
    if not files:
        print("No .docx files found.")
        return
    
    print(f"Processing {len(files)} files...\n")
    
    total_records = []
    for filepath in files:
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"  ✗ File not found: {filepath}")
            continue
        
        print(f"  Processing: {filepath.name}")
        records = extract_from_docx(filepath)
        
        if records:
            event_id = records[0][0]
            client = records[0][1]
            print(f"    → Event: {event_id}, Client: {client}, Samples: {len(records)}")
            total_records.extend(records)
        else:
            print(f"    → No records extracted")
    
    if total_records:
        print(f"\nInserting {len(total_records)} records...")
        count = insert_records(total_records)
        print(f"✓ Inserted {count} records into sample_details")
    else:
        print("\nNo records to insert.")

if __name__ == "__main__":
    main()
