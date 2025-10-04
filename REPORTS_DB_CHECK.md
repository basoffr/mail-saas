# 📂 REPORTS DB CHECK - DEEP REVIEW ANALYSIS

## 🎯 EXECUTIVE SUMMARY
**Status**: ✅ **VOLLEDIG GEÏMPLEMENTEERD**  
**Database Ready**: ✅ **PRODUCTION READY**  
**Bulk Mapping**: ✅ **2 MODES ACTIEF + 1 RESEARCH**  
**UI Integration**: ✅ **COMPLETE LEAD INDICATORS**

---

## 📊 DATAMODEL ANALYSE

### 🗄️ Core Tables

#### **`reports` Table**
```sql
CREATE TABLE reports (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR NOT NULL,
    type VARCHAR NOT NULL CHECK (type IN ('pdf', 'xlsx', 'png', 'jpg', 'jpeg')),
    size_bytes INTEGER NOT NULL,
    storage_path VARCHAR NOT NULL,
    checksum VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    uploaded_by VARCHAR,
    meta JSONB
);
```

#### **`report_links` Table**
```sql
CREATE TABLE report_links (
    id VARCHAR PRIMARY KEY,
    report_id VARCHAR NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    lead_id VARCHAR REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id VARCHAR REFERENCES campaigns(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Business constraint: exactly one target
    CONSTRAINT check_single_target CHECK (
        (lead_id IS NOT NULL AND campaign_id IS NULL) OR
        (lead_id IS NULL AND campaign_id IS NOT NULL)
    )
);
```

### ✅ **Constraints & Validation**
- **Primary Keys**: UUID strings voor alle entities
- **Foreign Keys**: Cascade delete voor data consistency
- **Business Rules**: Single target constraint (lead XOR campaign)
- **File Types**: Enum constraint voor supported formats
- **Size Limits**: 10MB per file, 100MB bulk ZIP, 100 files max

---

## 🚀 BULK MAPPING ALGORITMEN

### **Mode 1: `by_image_key`** ✅ ACTIEF
**Use Case**: Dashboard images → PDF reports matching

```python
def map_by_image_key(filename: str, leads_data: List[Dict]) -> Dict:
    base_name = os.path.splitext(filename)[0].lower()
    
    # Special PDF normalization
    if filename.endswith('.pdf'):
        normalized = normalize_pdf_filename(filename)  # {root}_nl_report
        
        for lead in leads_data:
            image_key = lead.get("image_key", "").lower()
            
            # Direct match
            if image_key == base_name or image_key == normalized:
                return {"status": "matched", "target": {"kind": "lead", "id": lead["id"]}}
            
            # Smart match: image_key ends with '_picture'
            if image_key.endswith('_picture'):
                root_key = image_key[:-8]  # Remove '_picture'
                expected_pdf = f"{root_key}_nl_report"
                if expected_pdf == normalized:
                    return {"status": "matched", "target": {"kind": "lead", "id": lead["id"]}}
    
    # Standard image_key matching
    for lead in leads_data:
        if lead.get("image_key", "").lower() == base_name:
            return {"status": "matched", "target": {"kind": "lead", "id": lead["id"]}}
    
    return {"status": "unmatched", "reason": "No matching image_key found"}
```

### **Mode 2: `by_email`** ✅ ACTIEF
**Use Case**: Email prefix → Lead matching

```python
def map_by_email(filename: str, leads_data: List[Dict]) -> Dict:
    base_name = os.path.splitext(filename)[0].lower()
    
    for lead in leads_data:
        email = lead.get("email", "")
        if email:
            email_prefix = email.split("@")[0].lower()
            if email_prefix == base_name:
                return {
                    "status": "matched",
                    "target": {"kind": "lead", "id": lead["id"], "email": email}
                }
    
    return {"status": "unmatched", "reason": "No matching email found"}
```

### **Mode 3: `by_root_domain`** 🔬 RESEARCH NEEDED
**Use Case**: Domain-based grouping voor bulk campaigns

```python
# PROPOSED IMPLEMENTATION
def map_by_root_domain(filename: str, leads_data: List[Dict]) -> Dict:
    base_name = os.path.splitext(filename)[0].lower()
    
    # Extract potential domain from filename
    # Examples: "example_com_report.pdf" → "example.com"
    domain_pattern = re.sub(r'_com_|_nl_|_org_', lambda m: m.group(0).replace('_', '.'), base_name)
    
    matches = []
    for lead in leads_data:
        email = lead.get("email", "")
        if email:
            lead_domain = email.split("@")[1].lower()
            root_domain = extract_root_domain(lead_domain)  # Remove subdomains
            
            if root_domain in domain_pattern:
                matches.append(lead)
    
    if len(matches) == 1:
        return {"status": "matched", "target": {"kind": "lead", "id": matches[0]["id"]}}
    elif len(matches) > 1:
        return {"status": "ambiguous", "reason": f"Multiple matches ({len(matches)})"}
    else:
        return {"status": "unmatched", "reason": "No matching domain found"}
```

---

## 📈 PERFORMANCE INDEXES

### **Required Indexes**
```sql
-- Core performance indexes
CREATE INDEX idx_reports_filename ON reports(filename);
CREATE INDEX idx_reports_type ON reports(type);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX idx_reports_uploaded_by ON reports(uploaded_by);

-- Link table indexes
CREATE INDEX idx_report_links_report_id ON report_links(report_id);
CREATE INDEX idx_report_links_lead_id ON report_links(lead_id);
CREATE INDEX idx_report_links_campaign_id ON report_links(campaign_id);

-- Composite indexes for common queries
CREATE INDEX idx_reports_type_created ON reports(type, created_at DESC);
CREATE INDEX idx_report_links_lead_created ON report_links(lead_id, created_at DESC);
```

### **Query Performance Analysis**
- **List Reports**: `O(log n)` with pagination + type filtering
- **Lead Has Report**: `O(1)` lookup via lead_id index
- **Bulk Mapping**: `O(n*m)` where n=files, m=leads (acceptable for MVP)
- **Download URL**: `O(1)` direct report_id lookup

---

## 🔍 UI QUERY PATTERNS

### **Lead Drawer - Has Report Indicator**
```sql
-- Check if lead has report
SELECT r.id, r.filename, r.type, r.created_at
FROM reports r
JOIN report_links rl ON r.id = rl.report_id
WHERE rl.lead_id = $1
ORDER BY r.created_at DESC
LIMIT 1;
```

### **Reports List with Filtering**
```sql
-- Main reports list query
SELECT r.*, 
       CASE 
         WHEN rl.lead_id IS NOT NULL THEN 'lead'
         WHEN rl.campaign_id IS NOT NULL THEN 'campaign'
         ELSE NULL
       END as bound_kind,
       COALESCE(rl.lead_id, rl.campaign_id) as bound_id
FROM reports r
LEFT JOIN report_links rl ON r.id = rl.report_id
WHERE ($1 IS NULL OR r.type = ANY($1))  -- type filter
  AND ($2 IS NULL OR 
       ($2 = 'bound' AND rl.id IS NOT NULL) OR
       ($2 = 'unbound' AND rl.id IS NULL))  -- bound filter
  AND ($3 IS NULL OR r.filename ILIKE '%' || $3 || '%')  -- search
ORDER BY r.created_at DESC
LIMIT $4 OFFSET $5;
```

### **Unmatched Reports Query**
```sql
-- Find unbound reports for manual binding
SELECT r.id, r.filename, r.type, r.created_at
FROM reports r
LEFT JOIN report_links rl ON r.id = rl.report_id
WHERE rl.id IS NULL
ORDER BY r.created_at DESC;
```

---

## 🔧 CURRENT IMPLEMENTATION STATUS

### ✅ **Fully Implemented Features**
1. **Single Upload**: ✅ File validation, storage, optional binding
2. **Bulk ZIP Upload**: ✅ 2 mapping modes with comprehensive error handling
3. **Report Management**: ✅ Bind/unbind, list with filters, download URLs
4. **File Validation**: ✅ Type checking, size limits, checksum generation
5. **PDF Normalization**: ✅ Smart filename standardization
6. **Error Handling**: ✅ Comprehensive validation and user feedback

### ✅ **API Endpoints (7 total)**
- `GET /reports` - List with filtering/pagination
- `GET /reports/{id}` - Report details
- `POST /reports/upload` - Single file upload
- `POST /reports/bulk` - ZIP bulk upload
- `POST /reports/bind` - Manual binding
- `POST /reports/unbind` - Remove binding
- `GET /reports/{id}/download` - Signed download URL

### ✅ **Frontend Integration**
- **Services**: Complete `reports.ts` with all API methods
- **Components**: Upload UI, bulk processing, binding management
- **Types**: Full TypeScript coverage for all schemas
- **UI Indicators**: Lead drawer shows 📄 when report exists

---

## 🚨 EDGE CASES & HANDLING

### **Bulk Upload Edge Cases**
1. **Ambiguous Matches**: Multiple leads match same filename
   - **Status**: `"ambiguous"`
   - **Action**: Log for manual review
   
2. **Invalid Files**: Unsupported types, oversized files
   - **Status**: `"failed"`
   - **Action**: Skip with detailed error message
   
3. **Duplicate Filenames**: Same filename in ZIP
   - **Handling**: Process all, use unique report IDs
   
4. **Corrupted ZIP**: Invalid archive format
   - **Handling**: HTTP 422 with clear error message

### **Storage Edge Cases**
1. **Checksum Conflicts**: Same file uploaded multiple times
   - **Handling**: Allow duplicates, different report IDs
   
2. **Storage Failures**: Supabase storage unavailable
   - **Handling**: Rollback database transaction
   
3. **Large File Processing**: Memory constraints
   - **Handling**: Stream processing for ZIP files

---

## 📋 SQL MIGRATION DIFF

### **Production Migration Script**
```sql
-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR NOT NULL,
    type VARCHAR NOT NULL CHECK (type IN ('pdf', 'xlsx', 'png', 'jpg', 'jpeg')),
    size_bytes INTEGER NOT NULL,
    storage_path VARCHAR NOT NULL,
    checksum VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by VARCHAR,
    meta JSONB
);

-- Report links table
CREATE TABLE IF NOT EXISTS report_links (
    id VARCHAR PRIMARY KEY,
    report_id VARCHAR NOT NULL,
    lead_id VARCHAR,
    campaign_id VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_report_links_report FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    CONSTRAINT fk_report_links_lead FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
    CONSTRAINT fk_report_links_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    CONSTRAINT check_single_target CHECK (
        (lead_id IS NOT NULL AND campaign_id IS NULL) OR
        (lead_id IS NULL AND campaign_id IS NOT NULL)
    )
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_reports_filename ON reports(filename);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(type);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_uploaded_by ON reports(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_report_links_report_id ON report_links(report_id);
CREATE INDEX IF NOT EXISTS idx_report_links_lead_id ON report_links(lead_id);
CREATE INDEX IF NOT EXISTS idx_report_links_campaign_id ON report_links(campaign_id);
CREATE INDEX IF NOT EXISTS idx_reports_type_created ON reports(type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_links_lead_created ON report_links(lead_id, created_at DESC);

-- Add by_root_domain support (future enhancement)
ALTER TABLE reports ADD COLUMN IF NOT EXISTS extracted_domain VARCHAR;
CREATE INDEX IF NOT EXISTS idx_reports_extracted_domain ON reports(extracted_domain);
```

---

## 🔬 NEXT RESEARCH PRIORITIES

### **1. by_root_domain Implementation** 🎯 HIGH PRIORITY
**Research Questions:**
- How to reliably extract root domain from filenames?
- Handle edge cases: subdomains, international domains, typos?
- Performance impact of domain extraction algorithms?
- UI/UX for ambiguous domain matches?

**Proposed Research:**
```python
# Test cases needed:
test_cases = [
    "example_com_report.pdf",      # → example.com
    "sub_example_com_report.pdf",  # → example.com or sub.example.com?
    "example-nl_report.pdf",       # → example.nl
    "123accu_nl_report.pdf",       # → 123accu.nl
    "multi_word_company_com.pdf"   # → multi-word-company.com?
]
```

### **2. Advanced Matching Algorithms** 🎯 MEDIUM PRIORITY
**Fuzzy Matching Research:**
- Levenshtein distance for typo tolerance
- Phonetic matching for similar-sounding names
- Machine learning for pattern recognition

### **3. Performance Optimization** 🎯 MEDIUM PRIORITY
**Bulk Processing Improvements:**
- Parallel file processing
- Streaming ZIP extraction
- Caching for repeated domain lookups
- Background job processing for large uploads

### **4. Enhanced UI Indicators** 🎯 LOW PRIORITY
**Visual Improvements:**
- Report type icons (📄 PDF, 📊 Excel, 🖼️ Image)
- Upload progress indicators
- Bulk mapping preview before processing
- Drag-and-drop ZIP upload

---

## 🏆 CONCLUSION

**Reports module is PRODUCTION READY** with comprehensive implementation:

✅ **Database Schema**: Complete with proper constraints and indexes  
✅ **Bulk Mapping**: 2 active modes + 1 research mode planned  
✅ **API Coverage**: 7 endpoints covering all use cases  
✅ **Error Handling**: Robust validation and user feedback  
✅ **UI Integration**: Complete lead indicators and management interface  
✅ **Performance**: Optimized queries with proper indexing  

**Next Steps**: Implement `by_root_domain` research and advanced matching algorithms for enhanced bulk processing capabilities.

---
*Generated: 2025-10-03 11:25 CET*  
*Status: DEEP-REVIEW COMPLETE*
