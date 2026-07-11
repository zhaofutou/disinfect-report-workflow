#!/usr/bin/env python3
"""Extract observation data from handwritten result photos and update Supabase.

Usage:
    python3 extract_observations.py                    # Process all JPGs in observation_results/
    python3 extract_observations.py 202605017.jpg      # Process specific file

This script provides the DATA STRUCTURE for observation extraction.
The actual OCR/vision extraction should be done by an AI agent using vision tools,
as handwritten Chinese text requires AI interpretation.

Agent Workflow:
    1. Use vision_analyze on each observation photo
    2. Extract: red number → observation value mapping
    3. Extract: department name → comma-separated values for air samples
    4. Call update_observations() to insert data

Expected observation sheet structure:
    - Red numbers 1-60 as row identifiers
    - Each red number maps to sampleID = eventID + suffix (e.g., 001, 002, ...)
    - Regular samples: single numeric observation value
    - Air samples (usually 40s-50s): handwritten department name + comma-separated values
"""

import sys
sys.path.insert(0, '.')
from pathlib import Path
from utils import load_config, get_db_connection

# Known semantic mappings for handwritten department names
# Add new mappings here as they appear
SEMANTIC_MAPPINGS = {
    'CT室': '放射科',
    'B超室': '彩超室',
    '抽血厅': '抽血室',
    '预防接种门诊': '接种门诊',
    '牙科': '口腔科',
    '二病室': '照护病房',
    '4楼中医室': '针灸康复科',
    '针灸治疗科': '针灸康复科',
    '门诊理疗室': '理疗科',
}

def fuzzy_match_location(handwritten, db_locations):
    """Match handwritten location to database location.
    
    Uses: 1) Semantic mappings, 2) Contains matching, 3) Fuzzy similarity
    """
    from difflib import SequenceMatcher
    
    # 1. Check semantic mappings
    if handwritten in SEMANTIC_MAPPINGS:
        target = SEMANTIC_MAPPINGS[handwritten]
        for loc in db_locations:
            if loc == target:
                return loc, 1.0, "semantic"
    
    # 2. Check contains
    for loc in db_locations:
        if handwritten in loc or loc in handwritten:
            return loc, 0.9, "contains"
    
    # 3. Fuzzy match
    best_match = None
    best_score = 0
    for loc in db_locations:
        score = SequenceMatcher(None, handwritten, loc).ratio()
        if score > best_score:
            best_score = score
            best_match = loc
    
    if best_score > 0.5:
        return best_match, best_score, "fuzzy"
    
    return None, 0, "none"

def get_air_sample_locations(event_id):
    """Get air sample locations for an event from database."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT sampleid, samplelocation 
    FROM sample_details 
    WHERE event = %s AND samplename LIKE '%%空气%%'
    ORDER BY sampleid
    """, (event_id,))
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def update_observation(sample_id, observation_value):
    """Update observation for a specific sample."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    UPDATE sample_details 
    SET observation = %s 
    WHERE sampleid = %s
    """, (str(observation_value), sample_id))
    
    count = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return count

def update_observations_batch(updates):
    """Batch update observations.
    
    Args:
        updates: list of (sample_id, observation_value) tuples
    """
    if not updates:
        return 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    total = 0
    for sample_id, obs_value in updates:
        cur.execute("""
        UPDATE sample_details 
        SET observation = %s 
        WHERE sampleid = %s
        """, (str(obs_value), sample_id))
        total += cur.rowcount
    
    conn.commit()
    cur.close()
    conn.close()
    return total

def map_red_number_to_sample_id(event_id, red_number):
    """Map red number from observation sheet to sampleID."""
    return f"{event_id}{red_number:03d}"

def process_observation_data(event_id, regular_samples, air_samples):
    """Process extracted observation data and update database.
    
    Args:
        event_id: e.g., "202605017"
        regular_samples: dict of {red_number: observation_value}
        air_samples: dict of {handwritten_dept: comma_separated_values}
    
    Returns:
        Number of rows updated
    """
    updates = []
    
    # Process regular samples
    for red_num, obs_value in regular_samples.items():
        if obs_value is None or obs_value == '':
            continue
        sample_id = map_red_number_to_sample_id(event_id, red_num)
        updates.append((sample_id, str(obs_value)))
    
    # Process air samples
    if air_samples:
        air_locations = get_air_sample_locations(event_id)
        db_locs = [loc for _, loc in air_locations]
        
        for hw_dept, obs_value in air_samples.items():
            matched_loc, score, method = fuzzy_match_location(hw_dept, db_locs)
            
            if matched_loc:
                # Find sampleID for this location
                for sid, loc in air_locations:
                    if loc == matched_loc:
                        updates.append((sid, obs_value))
                        print(f"  Air: '{hw_dept}' → '{matched_loc}' ({method}, {score:.2f})")
                        break
            else:
                print(f"  ⚠ Unmatched: '{hw_dept}'")
    
    # Batch update
    if updates:
        count = update_observations_batch(updates)
        return count
    return 0

# Template for agent to fill in after vision extraction
OBSERVATION_TEMPLATE = """
# Copy and fill this template for each observation photo
# Then call process_observation_data()

event_id = "202605017"  # From filename

regular_samples = {
    1: 4,      # red_number: observation_value
    2: 0,
    3: 0,
    # ... add more
}

air_samples = {
    '预防接种门诊': '0,0,0',   # handwritten_name: comma_separated_values
    '抽血厅': '0,1,1,0,0',
    # ... add more
}

# Then run:
# count = process_observation_data(event_id, regular_samples, air_samples)
# print(f"Updated {count} rows")
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nTemplate for data extraction:")
    print(OBSERVATION_TEMPLATE)
