#!/usr/bin/env python3
"""Calculate bacterial colony results and update sample_details table.

Usage:
    python3 calculate_results.py              # Calculate for all samples
    python3 calculate_results.py --event 202605017  # Calculate for specific event

Calculation Rules (from AI_AGENT_HANDOVER.md):

1. Surface samples (桌面, 门把手, etc.):
   result = observation × 10 / sampling_area
   units: CFU/cm²
   if observation == 0: result = "< 0.2 CFU/cm²" (threshold)

2. Liquid disinfectant samples (使用中消毒液):
   result = observation × 10
   units: CFU/mL

3. Air samples (comma-separated multiple plates):
   result = average(plates)
   units: CFU/90mm平皿

4. UV samples (紫外线灯):
   Skipped - these are radiation measurements, not bacteria counts
"""

import sys
import re
import argparse
sys.path.insert(0, '.')
from utils import get_db_connection

def calculate_result(sample_name, sample_area, observation):
    """Calculate bacterial colony result based on sample type."""
    
    # Skip UV samples
    if '紫外线灯' in sample_name:
        return None
    
    # No observation data
    if observation is None or observation == '':
        return None
    
    # Air samples (comma-separated)
    if ',' in str(observation):
        try:
            plates = [float(x.strip()) for x in str(observation).split(',')]
            avg = sum(plates) / len(plates)
            return f"{avg:.1f} CFU/90mm平皿"
        except:
            return None
    
    # Numeric observation
    try:
        obs = float(observation)
    except:
        return None
    
    # Determine sample type
    is_liquid = sample_area and 'ml' in str(sample_area).lower()
    is_air = '空气' in sample_name
    
    if is_liquid:
        result = obs * 10
        if result == 0:
            return "0 CFU/mL"
        return f"{result:.0f} CFU/mL"
    
    elif is_air:
        return f"{obs:.1f} CFU/90mm平皿"
    
    else:
        # Surface sample
        if sample_area:
            try:
                area = float(re.search(r'(\d+)', str(sample_area)).group(1))
                if obs == 0:
                    return "< 0.2 CFU/cm²"
                result = obs * 10 / area
                return f"{result:.1f} CFU/cm²"
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
    conn.commit()
    
    if args.event:
        cur.execute("""
        SELECT sampleid, samplename, samplearea, observation 
        FROM sample_details WHERE event = %s ORDER BY sampleid
        """, (args.event,))
    else:
        cur.execute("""
        SELECT sampleid, samplename, samplearea, observation 
        FROM sample_details ORDER BY sampleid
        """)
    
    rows = cur.fetchall()
    print(f"Processing {len(rows)} samples...")
    
    updated = 0
    skipped = 0
    for sid, name, area, obs in rows:
        result = calculate_result(name, area, obs)
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
