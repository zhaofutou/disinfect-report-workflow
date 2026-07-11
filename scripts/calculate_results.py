#!/usr/bin/env python3
"""Calculate bacterial colony results and update sample_details table.

Usage:
    python3 calculate_results.py              # Calculate for all samples
    python3 calculate_results.py --event 202605017  # Calculate for specific event

Calculation Rules:

1. Surface samples (桌面, 门把手, etc.):
   result = observation × 10 / sampling_area
   Output: just the number (e.g., "0.7")
   if observation == 0: result = "<0.2"

2. Liquid disinfectant samples (酒精, 消毒剂, 碘伏, 使用中酒精, 使用中消毒剂, 使用中碘伏):
   result = observation × 10
   Output: "{result} CFU/mL(十倍稀释)"
   if observation == 0: result = "<10 CFU/mL(十倍稀释)"

3. Air samples (comma-separated multiple plates):
   result = average(plates)
   Output: "{result} CFU/90mm平皿·{duration}min"

4. UV samples (紫外线灯):
   Skipped - these are radiation measurements, not bacteria counts
"""

import sys
import re
import argparse
sys.path.insert(0, '.')
from utils import get_db_connection

LIQUID_PATTERNS = ['酒精', '消毒剂', '碘伏']

def is_liquid_sample(sample_name):
    return any(p in sample_name for p in LIQUID_PATTERNS)

def calculate_result(sample_name, sample_area, observation, duration=None):
    """Calculate bacterial colony result based on sample type."""
    
    if '紫外线灯' in sample_name:
        return None
    if observation is None or observation == '':
        return None
    
    # Air samples (comma-separated)
    if ',' in str(observation):
        try:
            plates = [float(x.strip()) for x in str(observation).split(',')]
            avg = sum(plates) / len(plates)
            dur_suffix = f"·{duration}min" if duration else ""
            return f"{avg:.1f} CFU/90mm平皿{dur_suffix}"
        except:
            return None
    
    try:
        obs = float(observation)
    except:
        return None
    
    # Liquid disinfectant
    if is_liquid_sample(sample_name):
        if obs == 0:
            return "<10 CFU/mL(十倍稀释)"
        return f"{obs * 10:.0f} CFU/mL(十倍稀释)"
    
    # Air samples (single value)
    if '空气' in sample_name:
        dur_suffix = f"·{duration}min" if duration else ""
        return f"{obs:.1f} CFU/90mm平皿{dur_suffix}"
    
    # Surface samples
    if sample_area:
        try:
            area = float(re.search(r'(\d+)', str(sample_area)).group(1))
            if obs == 0:
                return "<0.2"
            return f"{obs * 10 / area:.1f}"
        except:
            pass
    
    return f"{obs}"

def main():
    parser = argparse.ArgumentParser(description='Calculate bacterial colony results')
    parser.add_argument('--event', help='Calculate for specific event ID only')
    args = parser.parse_args()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("ALTER TABLE sample_details ADD COLUMN IF NOT EXISTS result TEXT")
    cur.execute("ALTER TABLE sample_details ADD COLUMN IF NOT EXISTS sampleDuration TEXT")
    conn.commit()
    
    if args.event:
        cur.execute("""
        SELECT sampleid, samplename, samplearea, observation, sampleduration
        FROM sample_details WHERE event = %s ORDER BY sampleid
        """, (args.event,))
    else:
        cur.execute("""
        SELECT sampleid, samplename, samplearea, observation, sampleduration
        FROM sample_details ORDER BY sampleid
        """)
    
    rows = cur.fetchall()
    print(f"Processing {len(rows)} samples...")
    
    updated = 0
    skipped = 0
    for sid, name, area, obs, dur in rows:
        result = calculate_result(name, area, obs, dur)
        if result:
            cur.execute("UPDATE sample_details SET result = %s WHERE sampleid = %s", (result, sid))
            updated += cur.rowcount
        else:
            skipped += 1
    
    conn.commit()
    print(f"Updated {updated} rows with calculated results")
    print(f"Skipped {skipped} rows (UV samples or no observation)")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
