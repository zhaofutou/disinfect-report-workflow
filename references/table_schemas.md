# Database Table Schemas

## event_inspections

Stores one record per inspection agreement (委托协议书).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | BIGSERIAL | NO | Primary key, auto-increment |
| eventID | TEXT | NO | Report number, e.g., "202605014" |
| sampleCount | TEXT | YES | Sample ID range, e.g., "202605014001-202605014002" |
| clientInfo | TEXT | YES | Client hospital name |
| inspectionDate | DATE | YES | Date of inspection |
| inspectionTarget | TEXT | YES | What was tested (e.g., sterilization effect) |
| inspectionStandards | TEXT | YES | Evaluation standards/basis |
| created_at | TIMESTAMPTZ | YES | Record creation timestamp (auto) |

### Sample Data
```sql
INSERT INTO event_inspections (eventID, sampleCount, clientInfo, inspectionDate, inspectionTarget, inspectionStandards)
VALUES ('202605014', '202605014001-202605014002', '济宁市皮肤病防治院（济宁院区）', '2026-06-23', 
        '嗜热脂肪杆菌芽孢菌杀灭效果', '1、卫生部《消毒技术规范》（2002年版）2、GB/T 15981-2021 消毒器械灭菌效果评价方法');
```

---

## sample_details

Stores one record per sample. Linked to event_inspections via `event` = `eventID`.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | BIGSERIAL | NO | Primary key, auto-increment |
| event | TEXT | NO | Event ID (first 9 chars of sampleID) |
| client | TEXT | YES | Client hospital name |
| sampleID | TEXT | NO | Full sample ID, e.g., "202605017001" |
| sampleLocation | TEXT | YES | Department/location name |
| sampleName | TEXT | YES | Sample type (e.g., "医务人员手", "空气") |
| sampleArea | TEXT | YES | Area: "60" (cm²), "10ml", "30" (count), etc. |
| bacCount | INTEGER | YES | 细菌菌落总数: 1=present (√), 0=absent |
| ronglian | INTEGER | YES | 溶血性链球菌: 1=present (√), 0=absent |
| jinpu | INTEGER | YES | 金黄色葡萄球菌: 1=present (√), 0=absent |
| tonglv | INTEGER | YES | 铜绿假单胞菌: 1=present (√), 0=absent |
| UV | INTEGER | YES | 紫外线灯辐射照度: 1=has numeric value, 0=absent |
| observation | TEXT | YES | Observation: single number or comma-separated for air |
| created_at | TIMESTAMPTZ | YES | Record creation timestamp (auto) |

### Notes
- `event` column is the first 9 characters of `sampleID`
- `bacCount`, `ronglian`, `jinpu`, `tonglv`: Original doc uses √ mark → stored as 1
- `UV`: If original doc has a numeric value for 紫外线灯辐射照度 → stored as 1
- `observation`: 
  - Regular samples: single number (e.g., "4", "116", "0")
  - Air samples: comma-separated values (e.g., "0,1,1,0,0")
  - NULL if no observation recorded

### Sample Data
```sql
-- Regular sample
INSERT INTO sample_details (event, client, sampleID, sampleLocation, sampleName, sampleArea, bacCount, ronglian, jinpu, tonglv, UV, observation)
VALUES ('202605017', '市直机关医院（西院区）', '202605017001', '放射科', '医务人员手（医疗）', '60', 1, 1, 1, 1, 0, '4');

-- Air sample
INSERT INTO sample_details (event, client, sampleID, sampleLocation, sampleName, sampleArea, bacCount, ronglian, jinpu, tonglv, UV, observation)
VALUES ('202605017', '市直机关医院（西院区）', '202605017028', '接种门诊', '空气', NULL, 1, 0, 0, 0, 0, '0,0,0');
```

---

## Relationships

```
event_inspections.eventID ←→ sample_details.event
```

To join:
```sql
SELECT e.eventID, e.clientInfo, e.inspectionDate, 
       s.sampleID, s.sampleLocation, s.sampleName, s.observation
FROM event_inspections e
JOIN sample_details s ON e.eventID = s.event
ORDER BY e.eventID, s.sampleID;
```
