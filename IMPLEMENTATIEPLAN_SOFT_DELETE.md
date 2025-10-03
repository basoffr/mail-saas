# 🗑️ IMPLEMENTATIEPLAN: SOFT DELETE VOOR LEADS

**Datum:** 3 oktober 2025  
**Feature:** Soft delete functionaliteit voor leads met restore mogelijkheid  
**Type:** Non-breaking additive feature

---

## 🎯 DOEL

Implementeer soft delete functionaliteit waarmee:
- Leads kunnen worden "verwijderd" zonder data te verliezen
- Verwijderde leads niet meer verschijnen in standaard lijsten
- Verwijderde leads kunnen worden teruggehaald (restore)
- Audit trail behouden blijft
- Bulk delete mogelijk is voor meerdere leads

---

## ✨ FEATURES

### **Core Functionaliteit:**
1. ✅ Soft delete individual lead (zet `deleted_at` timestamp)
2. ✅ Bulk soft delete (multiple leads tegelijk)
3. ✅ Restore deleted lead (reset `deleted_at` naar `null`)
4. ✅ Filter deleted leads uit standaard queries
5. ✅ Optionele view voor deleted leads (prullenbak)

### **UI Components:**
1. ✅ Delete button in lead drawer
2. ✅ Bulk delete voor geselecteerde leads
3. ✅ Confirmation dialog met waarschuwing
4. ✅ Optioneel: "Deleted Leads" tab/filter
5. ✅ Restore button voor deleted leads

---

## 📋 STAP-VOOR-STAP IMPLEMENTATIE

### **FASE 1: BACKEND - DATA MODEL**

#### **Stap 1.1: Lead Model Update**
**Bestand:** `backend/app/models/lead.py`

**Toevoegen:**
```python
from datetime import datetime
from sqlmodel import Field, Column
from sqlalchemy import DateTime

class Lead(SQLModel, table=True):
    # ... bestaande fields
    deleted_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), index=True)
    )
```

**Impact:** Alle leads krijgen `deleted_at` field (nullable, geïndexeerd voor snelle queries)

---

#### **Stap 1.2: Lead Schema Update**
**Bestand:** `backend/app/schemas/lead.py`

**Update LeadOut:**
```python
class LeadOut(BaseModel):
    # ... bestaande fields
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False  # Computed field voor UI
```

**Nieuwe schemas:**
```python
class LeadDeleteRequest(BaseModel):
    """Request to soft delete lead(s)."""
    lead_ids: List[str] = Field(..., min_items=1, max_items=100)
    reason: Optional[str] = None  # Optioneel: delete reden voor audit

class LeadDeleteResponse(BaseModel):
    """Response after soft delete operation."""
    deleted_count: int
    deleted_ids: List[str]
    failed_ids: List[str] = []
    
class LeadRestoreResponse(BaseModel):
    """Response after restore operation."""
    restored_count: int
    restored_ids: List[str]
    failed_ids: List[str] = []
```

---

### **FASE 2: BACKEND - STORE LOGIC**

#### **Stap 2.1: LeadsStore Updates**
**Bestand:** `backend/app/services/leads_store.py`

**Update _LeadRec dataclass:**
```python
@dataclass
class _LeadRec:
    # ... bestaande fields
    deleted_at: Optional[datetime] = None
```

**Nieuwe methodes toevoegen:**
```python
def soft_delete(self, lead_id: str) -> bool:
    """Soft delete a lead by setting deleted_at timestamp.
    
    Returns True if successful, False if lead not found.
    """
    for rec in self._leads:
        if rec.id == lead_id:
            rec.deleted_at = _now()
            rec.updated_at = _now()
            return True
    return False

def soft_delete_bulk(self, lead_ids: List[str]) -> Tuple[List[str], List[str]]:
    """Soft delete multiple leads.
    
    Returns (deleted_ids, failed_ids)
    """
    deleted = []
    failed = []
    
    for lead_id in lead_ids:
        if self.soft_delete(lead_id):
            deleted.append(lead_id)
        else:
            failed.append(lead_id)
    
    return deleted, failed

def restore(self, lead_id: str) -> bool:
    """Restore a soft-deleted lead by clearing deleted_at.
    
    Returns True if successful, False if lead not found.
    """
    for rec in self._leads:
        if rec.id == lead_id:
            rec.deleted_at = None
            rec.updated_at = _now()
            return True
    return False

def restore_bulk(self, lead_ids: List[str]) -> Tuple[List[str], List[str]]:
    """Restore multiple soft-deleted leads.
    
    Returns (restored_ids, failed_ids)
    """
    restored = []
    failed = []
    
    for lead_id in lead_ids:
        if self.restore(lead_id):
            restored.append(lead_id)
        else:
            failed.append(lead_id)
    
    return restored, failed

def get_deleted_leads(
    self,
    *,
    page: int = 1,
    page_size: int = 25,
    search: Optional[str] = None
) -> Tuple[List[LeadOut], int]:
    """Get all soft-deleted leads (for trash view).
    
    Returns (leads, total_count)
    """
    data = [r for r in self._leads if r.deleted_at is not None]
    
    if search:
        q = search.lower()
        data = [
            r for r in data
            if q in r.email.lower()
            or (r.company or "").lower().find(q) != -1
        ]
    
    total = len(data)
    start = (page - 1) * page_size
    end = start + page_size
    
    return [r.to_out() for r in data[start:end]], total
```

**Update query() methode:**
```python
def query(
    self,
    *,
    page: int,
    page_size: int,
    status: Optional[List[LeadStatus]] = None,
    # ... andere bestaande params
    include_deleted: bool = False,  # NIEUW
) -> Tuple[List[LeadOut], int]:
    # Filter deleted leads UNLESS explicitly requested
    if include_deleted:
        data = list(self._leads)
    else:
        data = [r for r in self._leads if r.deleted_at is None]
    
    # ... rest van filtering logic blijft hetzelfde
```

**Update to_out() methode:**
```python
def to_out(self) -> LeadOut:
    return LeadOut(
        # ... bestaande fields
        deleted_at=self.deleted_at,
        is_deleted=(self.deleted_at is not None),
    )
```

---

### **FASE 3: BACKEND - API ENDPOINTS**

#### **Stap 3.1: Leads API Updates**
**Bestand:** `backend/app/api/leads.py`

**Nieuwe endpoints toevoegen:**

```python
from app.schemas.lead import (
    LeadDeleteRequest, 
    LeadDeleteResponse,
    LeadRestoreResponse
)

@router.post("/leads/delete", response_model=DataResponse[LeadDeleteResponse])
async def soft_delete_leads(
    payload: LeadDeleteRequest,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Soft delete one or more leads.
    
    Sets deleted_at timestamp. Leads will be filtered from standard queries.
    """
    deleted_ids, failed_ids = store.soft_delete_bulk(payload.lead_ids)
    
    logger.info("leads_soft_deleted", extra={
        "user": user.get("sub"),
        "deleted_count": len(deleted_ids),
        "failed_count": len(failed_ids),
        "reason": payload.reason
    })
    
    return {
        "data": {
            "deleted_count": len(deleted_ids),
            "deleted_ids": deleted_ids,
            "failed_ids": failed_ids
        },
        "error": None
    }

@router.post("/leads/restore", response_model=DataResponse[LeadRestoreResponse])
async def restore_leads(
    payload: LeadDeleteRequest,  # Reuse same schema (lead_ids)
    user: Dict[str, Any] = Depends(require_auth)
):
    """Restore soft-deleted leads.
    
    Clears deleted_at timestamp. Leads will reappear in standard queries.
    """
    restored_ids, failed_ids = store.restore_bulk(payload.lead_ids)
    
    logger.info("leads_restored", extra={
        "user": user.get("sub"),
        "restored_count": len(restored_ids),
        "failed_count": len(failed_ids)
    })
    
    return {
        "data": {
            "restored_count": len(restored_ids),
            "restored_ids": restored_ids,
            "failed_ids": failed_ids
        },
        "error": None
    }

@router.get("/leads/deleted", response_model=DataResponse[LeadsListResponse])
async def list_deleted_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Get all soft-deleted leads (trash view).
    
    Returns leads where deleted_at is not null.
    """
    items, total = store.get_deleted_leads(
        page=page,
        page_size=page_size,
        search=search
    )
    
    # Don't enrich deleted leads (performance optimization)
    return {
        "data": {
            "items": items,
            "total": total
        },
        "error": None
    }
```

**Update bestaand list_leads endpoint:**
```python
@router.get("/leads", response_model=DataResponse[LeadsListResponse])
async def list_leads(
    # ... bestaande params
    include_deleted: bool = Query(False),  # NIEUW: optioneel deleted leads tonen
):
    items, total = store.query(
        # ... bestaande params
        include_deleted=include_deleted
    )
    # ... rest blijft hetzelfde
```

---

### **FASE 4: FRONTEND - TYPES & SERVICE**

#### **Stap 4.1: TypeScript Types**
**Bestand:** `vitalign-pro/src/types/lead.ts`

**Update Lead interface:**
```typescript
export interface Lead {
  // ... bestaande fields
  deletedAt?: Date;
  isDeleted: boolean;
}
```

**Nieuwe types:**
```typescript
export interface LeadDeleteRequest {
  lead_ids: string[];
  reason?: string;
}

export interface LeadDeleteResponse {
  deleted_count: number;
  deleted_ids: string[];
  failed_ids: string[];
}

export interface LeadRestoreResponse {
  restored_count: number;
  restored_ids: string[];
  failed_ids: string[];
}
```

---

#### **Stap 4.2: Leads Service**
**Bestand:** `vitalign-pro/src/services/leads.ts`

**Nieuwe methodes:**
```typescript
export const leadsService = {
  // ... bestaande methodes
  
  async deleteLeads(leadIds: string[], reason?: string): Promise<LeadDeleteResponse> {
    const payload: LeadDeleteRequest = {
      lead_ids: leadIds,
      reason
    };
    
    return await authService.apiCall<LeadDeleteResponse>('/leads/delete', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  
  async restoreLeads(leadIds: string[]): Promise<LeadRestoreResponse> {
    const payload: LeadDeleteRequest = {
      lead_ids: leadIds
    };
    
    return await authService.apiCall<LeadRestoreResponse>('/leads/restore', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  
  async getDeletedLeads(query: { 
    page?: number; 
    limit?: number; 
    search?: string;
  } = {}): Promise<LeadsResponse> {
    const queryString = buildQueryString({
      page: query.page || 1,
      page_size: query.limit || 25,
      search: query.search
    });
    
    const endpoint = `/leads/deleted${queryString ? `?${queryString}` : ''}`;
    return await authService.apiCall<LeadsResponse>(endpoint);
  }
};
```

---

### **FASE 5: FRONTEND - UI COMPONENTS**

#### **Stap 5.1: Delete Button in Lead Drawer**
**Bestand:** `vitalign-pro/src/pages/leads/Leads.tsx`

**In LeadDetails component toevoegen:**
```typescript
// Import toevoegen
import { Trash2 } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

// State toevoegen in LeadDetails
const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
const [isDeleting, setIsDeleting] = useState(false);

// Handler toevoegen
const handleDelete = async () => {
  setIsDeleting(true);
  try {
    await leadsService.deleteLeads([lead.id]);
    toast({
      title: 'Lead Deleted',
      description: `${lead.email} has been moved to trash.`
    });
    // Refresh leads list of sluit drawer
    window.location.reload(); // Of elegantere state update
  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to delete lead',
      variant: 'destructive'
    });
  } finally {
    setIsDeleting(false);
    setDeleteDialogOpen(false);
  }
};

// In de drawer JSX (na Template Test sectie):
<div className="border-t pt-4">
  <Button
    variant="destructive"
    className="w-full"
    onClick={() => setDeleteDialogOpen(true)}
  >
    <Trash2 className="w-4 h-4 mr-2" />
    Delete Lead
  </Button>
</div>

{/* Delete Confirmation Dialog */}
<AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Delete Lead?</AlertDialogTitle>
      <AlertDialogDescription>
        Are you sure you want to delete <strong>{lead.email}</strong>?
        <br /><br />
        This will soft-delete the lead. You can restore it from the trash later.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction 
        onClick={handleDelete}
        disabled={isDeleting}
        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
      >
        {isDeleting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
        Delete Lead
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

---

#### **Stap 5.2: Bulk Delete voor Geselecteerde Leads**
**Bestand:** `vitalign-pro/src/pages/leads/Leads.tsx`

**In main Leads component:**
```typescript
// State
const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);
const [isDeleting, setIsDeleting] = useState(false);

// Handler
const handleBulkDelete = async () => {
  setIsDeleting(true);
  try {
    const leadIds = Array.from(selectedLeads);
    const result = await leadsService.deleteLeads(leadIds);
    
    toast({
      title: 'Leads Deleted',
      description: `${result.deleted_count} lead(s) moved to trash.`
    });
    
    setSelectedLeads(new Set());
    fetchLeads(); // Refresh list
  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to delete leads',
      variant: 'destructive'
    });
  } finally {
    setIsDeleting(false);
    setBulkDeleteDialogOpen(false);
  }
};

// In de bulk actions bar (na export button):
<Button
  variant="destructive"
  size="sm"
  onClick={() => setBulkDeleteDialogOpen(true)}
  disabled={selectedLeads.size === 0}
>
  <Trash2 className="w-4 h-4 mr-2" />
  Delete ({selectedLeads.size})
</Button>

{/* Bulk Delete Dialog - vergelijkbaar met single delete */}
```

---

#### **Stap 5.3: Deleted Leads View (Optioneel - Prullenbak Tab)**
**Nieuw bestand:** `vitalign-pro/src/pages/leads/DeletedLeads.tsx`

**Component structuur:**
```typescript
export function DeletedLeads() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeads, setSelectedLeads] = useState<Set<string>>(new Set());
  
  // Fetch deleted leads
  useEffect(() => {
    fetchDeletedLeads();
  }, []);
  
  const fetchDeletedLeads = async () => {
    setLoading(true);
    try {
      const response = await leadsService.getDeletedLeads();
      setLeads(response.items);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load deleted leads',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleRestore = async () => {
    const leadIds = Array.from(selectedLeads);
    const result = await leadsService.restoreLeads(leadIds);
    
    toast({
      title: 'Leads Restored',
      description: `${result.restored_count} lead(s) restored.`
    });
    
    setSelectedLeads(new Set());
    fetchDeletedLeads();
  };
  
  return (
    <div className="space-y-6">
      {/* Header met restore button */}
      {/* Table met deleted leads */}
      {/* Restore button voor geselecteerde leads */}
    </div>
  );
}
```

**Toevoegen aan routing:**
```typescript
// In src/App.tsx of routing file
<Route path="/leads/deleted" element={<DeletedLeads />} />
```

---

## 🧪 TESTING

### **Backend Tests** (nieuw bestand)

**`backend/app/tests/test_soft_delete.py`:**
```python
def test_soft_delete_single_lead():
    """Test soft deleting a single lead."""
    # Create lead, soft delete, verify deleted_at set
    
def test_soft_delete_bulk():
    """Test bulk soft delete."""
    # Create multiple leads, bulk delete, verify all deleted
    
def test_restore_lead():
    """Test restoring a soft-deleted lead."""
    # Delete lead, restore, verify deleted_at cleared
    
def test_query_excludes_deleted():
    """Test that normal queries exclude deleted leads."""
    # Create leads, delete some, verify query only returns non-deleted
    
def test_get_deleted_leads():
    """Test fetching only deleted leads."""
    # Create leads, delete some, verify get_deleted_leads returns correct set
    
def test_deleted_lead_not_in_campaigns():
    """Test that deleted leads are excluded from campaign selection."""
    # Verify scheduler doesn't pick up deleted leads
```

---

## 📁 BESTANDEN OVERZICHT

### **Backend (7 bestanden):**
1. ✏️ `backend/app/models/lead.py` - Add `deleted_at` field
2. ✏️ `backend/app/schemas/lead.py` - Add delete/restore schemas
3. ✏️ `backend/app/services/leads_store.py` - Add soft delete methods
4. ✏️ `backend/app/api/leads.py` - Add delete/restore endpoints
5. ✨ `backend/app/tests/test_soft_delete.py` - NEW test file

### **Frontend (5 bestanden):**
6. ✏️ `vitalign-pro/src/types/lead.ts` - Add delete types
7. ✏️ `vitalign-pro/src/services/leads.ts` - Add delete methods
8. ✏️ `vitalign-pro/src/pages/leads/Leads.tsx` - Add delete UI
9. ✨ `vitalign-pro/src/pages/leads/DeletedLeads.tsx` - NEW trash view
10. ✏️ `vitalign-pro/src/App.tsx` - Add deleted route

**Totaal: 10 bestanden (2 nieuw, 8 updates)**

---

## ⚠️ BELANGRIJK

### **Migration Considerations:**
- Bestaande leads hebben `deleted_at=None` (not deleted)
- Index op `deleted_at` voor snelle filtering
- Deleted leads blijven in database (disk space)

### **Business Logic:**
- **Campaigns:** Deleted leads NIET selecteren voor nieuwe campaigns
- **Messages:** Bestaande messages naar deleted leads blijven zichtbaar
- **Statistics:** Deleted leads NIET meetellen in actieve lead counts
- **Import:** Duplicate check moet deleted leads NEGEREN (of warning geven)

### **Performance:**
- `deleted_at IS NULL` filter in alle queries (geïndexeerd)
- Bulk operations max 100 leads per call
- Deleted leads view kan langzaam worden → paginatie cruciaal

---

## 🚀 DEPLOYMENT

### **Stap 1:** Backend deployment
- Database krijgt nieuwe `deleted_at` kolom (nullable, default NULL)
- Alle bestaande leads hebben `deleted_at=None`
- API endpoints beschikbaar

### **Stap 2:** Frontend deployment  
- Delete buttons verschijnen in UI
- Users kunnen leads soft-deleten
- Trash view beschikbaar

### **Rollback plan:**
- Deleted leads kunnen worden restored
- Geen data verlies bij rollback
- `deleted_at` kolom kan blijven staan (backward compatible)

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Lead kan worden soft-deleted via drawer button
- [ ] Meerdere leads kunnen bulk worden deleted
- [ ] Confirmation dialog toont voor delete operatie
- [ ] Deleted lead verdwijnt uit standaard leads lijst
- [ ] Deleted lead verschijnt in trash view
- [ ] Deleted lead kan worden restored
- [ ] Bulk restore werkt voor meerdere leads
- [ ] Deleted leads worden uitgesloten van campaigns
- [ ] API endpoints retourneren correct deleted_count
- [ ] Tests dekken happy path + edge cases

---

## 📊 GESCHATTE EFFORT

- **Backend:** 3-4 uur
- **Frontend:** 4-5 uur  
- **Testing:** 2 uur
- **Documentation:** 1 uur

**Totaal: ~10-12 uur**

---

**Einde implementatieplan** - Klaar voor review en goedkeuring ✅
