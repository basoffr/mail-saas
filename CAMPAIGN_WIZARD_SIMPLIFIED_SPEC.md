# 🎯 Vereenvoudigde Campaign Wizard Specificatie

**Datum:** 30 September 2025  
**Doel:** Ultrasimple wizard volgens GuardRails  
**Basis:** globalcampaignsettings.md GuardRails + tab3_campagnes_implementatieplan.md

---

## 🔒 Hard-Coded Campaign Settings

### Flow/Domain/Template Koppeling (1-op-1)
| **Flow** | **Domain** | **Templates** | **Email Aliases** |
|----------|-----------|---------------|-------------------|
| v1 | punthelder-vindbaarheid.nl | v1m1, v1m2, v1m3, v1m4 | christian@punthelder-vindbaarheid.nl<br/>victor@punthelder-vindbaarheid.nl |
| v2 | punthelder-marketing.nl | v2m1, v2m2, v2m3, v2m4 | christian@punthelder-marketing.nl<br/>victor@punthelder-marketing.nl |
| v3 | punthelder-seo.nl | v3m1, v3m2, v3m3, v3m4 | christian@punthelder-seo.nl<br/>victor@punthelder-seo.nl |
| v4 | punthelder-zoekmachine.nl | v4m1, v4m2, v4m3, v4m4 | christian@punthelder-zoekmachine.nl<br/>victor@punthelder-zoekmachine.nl |

### 🔒 Hard-Coded Rules (Gedocumenteerd)
- **v1 = vindbaarheid** → christian@/victor@punthelder-vindbaarheid.nl
- **v2 = marketing** → christian@/victor@punthelder-marketing.nl
- **v3 = seo** → christian@/victor@punthelder-seo.nl
- **v4 = zoekmachine** → christian@/victor@punthelder-zoekmachine.nl
- **Throughput**: 12 mails/uur totaal (4 domains × 3 slots/uur)
- **Templates**: Auto-assigned per versie (v1m1-v1m4, etc.)
- **Domain consistency**: Lead blijft op gekozen domein voor alle 4 mails
- m1/m2 altijd FROM christian@{domain} (bijv. christian@punthelder-vindbaarheid.nl)
- m3/m4 altijd FROM victor@{domain}, Reply-To: christian@{domain}
- **Alle 4 mails blijven op hetzelfde domein per lead**

### Sending Policy (Hard-Coded)
{{ ... }}

```yaml
Timezone: Europe/Amsterdam
Werkdagen: ma-vr
Verzendvenster: 08:00-17:00 (laatste slot 16:40)
Grace period: tot 18:00

Throttle: 
  - 1 mail per 20 min PER DOMEIN
  - 4 domeinen parallel = 12 mails/uur totaal
  - Slot grid: :00, :20, :40
  - Daily cap per domein: 27 slots

Follow-up interval: +3 werkdagen (hard-coded)
Max retries: 2 (exponential backoff)
```

### Dedupe Rules (Hard-Coded)

```yaml
Forced filters:
  - Exclude suppressed leads (status=suppressed)
  - Exclude bounced leads (status=bounced)
  
Default filters (niet bewerkbaar):
  - Exclude contacted last 14 days
  - One per domain: optioneel (checkbox)
```

---

## ✨ Vereenvoudigde Wizard (3 Stappen)

### Stap 1: Campagne Basis

**Inputs:**
1. **Campagne naam** [text input - verplicht]
2. **Start timing** [radio buttons]:
   - ⚪ Nu starten (eerstvolgende geldige slot)
   - ⚪ Gepland starten op: [date/time picker]

**Backend auto-assigns:**
- ✅ Flow/versie (round-robin of eerste beschikbare domein)
- ✅ Domain (gekoppeld aan flow)
- ✅ Templates (4 templates gekoppeld aan flow versie)
- ✅ Alias (christian voor v1/v2, victor voor v3/v4)

**Validatie:**
- Naam niet leeg
- Bij "gepland": datum ≥ nu en binnen werkdagen/venster

---

### Stap 2: Doelgroep Selectie

**Inputs:**
1. **Lead selectie** [lead selector component]:
   - Import vanuit Leads tab (URL params: `?source=leads&ids=...`)
   - Of: inline selectie via tabel/filters

**Read-only info boxes:**
```
ℹ️ Auto-filters (altijd actief):
  ✓ Suppressed leads uitgesloten
  ✓ Bounced emails uitgesloten  
  ✓ Recent gecontacteerd (< 14 dagen) uitgesloten
  
☐ One per domain (optioneel)
```

**Preview:**
- Aantal leads na filters: **X leads**
- Steekproef: eerste 5 leads tonen

**Validatie:**
- Minimaal 1 lead na filters

---

### Stap 3: Review & Launch

**Read-only samenvatting:**

```
┌─────────────────────────────────────────┐
│ Campagne: "Mijn Campaign Naam"          │
│ Doelgroep: 250 leads                    │
│                                         │
│ 🎯 Toegewezen configuratie:             │
│ ────────────────────────────────────    │
│ Flow: v2 (Vindbaarheid)                 │
│ Domain: punthelder-vindbaarheid.nl      │
│ Alias: Christian                        │
│                                         │
│ 📧 Planning:                            │
│ • 4 mails per lead (1.000 mails totaal) │
│ • Over 9 werkdagen vanaf start          │
│ • m1+m2: Christian (dag 0, +3)          │
│ • m3+m4: Victor (dag +6, +9)            │
│                                         │
│ ⚙️ Verzendregels (hard-coded):          │
│ • 1 mail per 20 min op dit domein       │
│ • Verzendvenster: ma-vr 08:00-17:00     │
│ • Timezone: Europe/Amsterdam            │
│                                         │
│ 🚀 Start: [gekozen start timing]        │
└─────────────────────────────────────────┘
```

**Acties:**
- **[Dry-run]** button → Toon planning simulatie
- **[◀ Terug]** button → Vorige stap
- **[▶ Start Campagne]** button → Create + start

**Dry-run result:**
```
Dry-run Resultaat:
─────────────────────────────────────────
Dag 1 (ma):  50 mails (08:00-16:40)
Dag 2 (di):  50 mails
Dag 3 (wo):  50 mails  
...
Dag 9 (di):  50 mails

Totaal: 1.000 mails over 9 werkdagen
Gem. 12 mails/uur (4 domeinen parallel)

⚠️ Waarschuwingen:
• 3 leads hebben recent gebounced
• 12 leads missen template variabelen
```

---

## 🔄 Backend Logica

### Flow Assignment Algorithm

```python
def assign_campaign_flow(start_at: datetime) -> CampaignFlow:
    """Assign next available flow/domain (round-robin)"""
    
    # Get all flows ordered by version
    flows = get_all_flows()  # v1, v2, v3, v4
    
    # Check which domains are busy at start_at
    for flow in flows:
        if not is_domain_busy_at(flow.domain, start_at):
            return flow
    
    # All busy - find next available slot
    raise ValueError("All domains busy - no available slots")

def is_domain_busy_at(domain: str, check_time: datetime) -> bool:
    """Check if domain has active campaign at given time"""
    # Max 1 active campaign per domain (GuardRail)
    active_campaigns = campaign_store.get_active_campaigns_for_domain(domain)
    
    for campaign in active_campaigns:
        # Check if campaign is running during check_time
        if campaign.start_at <= check_time <= campaign.end_at:
            return True
    
    return False
```

### Campaign Creation Flow

```python
@router.post("/campaigns")
async def create_campaign(payload: SimplifiedCampaignPayload):
    """Create campaign with auto-assigned flow/domain/templates"""
    
    # 1. Assign flow (round-robin, eerste beschikbaar)
    flow = assign_campaign_flow(payload.start_at or datetime.now())
    
    # 2. Get templates for this flow version
    templates = get_templates_for_flow(flow.version)  # v1m1-v1m4
    
    # 3. Determine alias based on version
    alias = "christian" if flow.version in [1, 2] else "victor"
    
    # 4. Create campaign
    campaign = Campaign(
        id=str(uuid.uuid4()),
        name=payload.name,
        flow_version=flow.version,
        domain=flow.domain,
        alias=alias,
        start_at=payload.start_at or get_next_valid_slot(),
        status=CampaignStatus.draft
    )
    
    # 5. Create messages (4 per lead)
    messages = []
    for lead_id in payload.lead_ids:
        for step in flow.steps:
            message = Message(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                lead_id=lead_id,
                mail_number=step.mail_number,
                template_id=templates[step.mail_number - 1].id,
                alias=step.alias,  # christian or victor
                scheduled_at=calculate_scheduled_time(
                    campaign.start_at, 
                    step.workdays_offset
                )
            )
            messages.append(message)
    
    # 6. Store & schedule
    campaign_store.create_campaign(campaign)
    campaign_store.create_messages(messages)
    
    # 7. If start_mode=now, start immediately
    if payload.start_type == "now":
        await start_campaign(campaign.id)
    
    return {"id": campaign.id}
```

---

## 📋 Simplified Payload Schema

### Frontend → Backend

```typescript
interface SimplifiedCampaignPayload {
  name: string;                    // User input
  start_type: 'now' | 'scheduled'; // User choice
  start_at?: string;               // ISO datetime if scheduled
  lead_ids: string[];              // User selection
  one_per_domain: boolean;         // Optional checkbox
  
  // NIET AANWEZIG - auto-assigned:
  // template_id ❌
  // flow_version ❌
  // domain ❌
  // throttle ❌
  // window ❌
  // retry_policy ❌
  // followup_days ❌
}
```

### Backend Response

```typescript
interface CampaignCreated {
  id: string;
  name: string;
  
  // Auto-assigned values (voor UI display)
  flow_version: number;        // 1-4
  domain: string;              // punthelder-{type}.nl
  alias: string;               // christian/victor
  templates: string[];         // [v1m1, v1m2, v1m3, v1m4]
  
  total_messages: number;      // lead_count * 4
  estimated_days: number;      // 9 werkdagen
  start_at: string;           // Calculated eerste slot
  
  status: 'draft' | 'running';
}
```

---

## 🎨 UI Components Aanpassingen

### CampaignNew.tsx - Simplified

**VERWIJDEREN:**
- ❌ Step "Verzendregels" (alles hard-coded)
- ❌ Template dropdown (auto-assigned)
- ❌ Domain checkboxes (auto-assigned)
- ❌ Throttle inputs (hard-coded)
- ❌ Window time pickers (hard-coded)
- ❌ Retry policy inputs (hard-coded)
- ❌ Follow-up days input (hard-coded: 3 dagen)

**BEHOUDEN:**
- ✅ Campaign naam input
- ✅ Start timing (now/scheduled)
- ✅ Lead selector
- ✅ One-per-domain checkbox
- ✅ Dry-run functie
- ✅ Review overzicht

**TOEVOEGEN:**
- ✅ Auto-assigned info display:
  ```tsx
  <Card className="p-4 bg-muted/30">
    <h4 className="font-semibold mb-2">Auto-toegewezen</h4>
    <div className="space-y-1 text-sm">
      <p>Flow: <Badge>v{flowVersion} ({domainName})</Badge></p>
      <p>Alias: <Badge variant="outline">{alias}</Badge></p>
      <p>Templates: {templates.length} mails</p>
    </div>
  </Card>
  ```

### Review Step - Enhanced

```tsx
const renderReviewStep = () => (
  <div className="space-y-6">
    {/* Campaign Summary */}
    <Card>
      <h3>Campagne: {data.name}</h3>
      <p>Doelgroep: {data.leadIds.length} leads</p>
    </Card>
    
    {/* Auto-assigned Config */}
    <Card className="border-primary/20 bg-primary/5">
      <h3>🎯 Toegewezen Configuratie</h3>
      <dl>
        <dt>Flow:</dt>
        <dd>v{assignedFlow.version} ({assignedFlow.domain})</dd>
        
        <dt>Alias:</dt>
        <dd>{assignedAlias} (v1/v2=christian, v3/v4=victor)</dd>
        
        <dt>Planning:</dt>
        <dd>
          • 4 mails per lead = {data.leadIds.length * 4} totaal<br/>
          • Over 9 werkdagen vanaf {formatDate(startTime)}<br/>
          • m1+m2: Christian (dag 0, +3)<br/>
          • m3+m4: Victor (dag +6, +9, Reply-To: Christian)
        </dd>
      </dl>
    </Card>
    
    {/* Hard-coded Rules */}
    <Card>
      <h3>⚙️ Verzendregels (hard-coded)</h3>
      <ul>
        <li>1 mail per 20 min op {assignedFlow.domain}</li>
        <li>Verzendvenster: ma-vr 08:00-17:00</li>
        <li>Timezone: Europe/Amsterdam</li>
        <li>Parallel: 4 domeinen = 12 mails/uur totaal</li>
      </ul>
    </Card>
    
    {/* Dry-run Result */}
    {dryRunResult && (
      <Card>
        <h3>📊 Dry-run Planning</h3>
        <DryRunTimeline data={dryRunResult} />
      </Card>
    )}
    
    {/* Actions */}
    <div className="flex gap-3">
      <Button onClick={handleDryRun} variant="outline">
        Dry-run Simulatie
      </Button>
      <Button onClick={handleSubmit} className="flex-1">
        ▶ Start Campagne
      </Button>
    </div>
  </div>
);
```

---

## ✅ GuardRails Compliance Checklist

- [x] **GEEN overrides** in UI per campagne
- [x] **GEEN override** per alias (auto via versie)
- [x] **/settings** alleen GET (POST=405)
- [x] **Domein-throttle heilig**: 1/20m per domein
- [x] **Max 1 actief** per domein (409 bij busy)
- [x] **Intervals +3 werkdagen** (hard-coded)
- [x] **Backlog doorgerold** (geen skip)
- [x] **Alias-rollen vast**: v1/v2=christian, v3/v4=victor
- [x] **Templates hard-coded** per versie
- [x] **M3/M4 headers**: From=Victor, Reply-To=Christian

---

## 🚀 Implementation Checklist

### Backend Changes
- [ ] Remove override fields from `CampaignCreatePayload`
- [ ] Implement `assign_campaign_flow()` logic
- [ ] Add `get_templates_for_flow(version)` helper
- [ ] Update campaign creation to auto-assign flow/domain/templates
- [ ] Add alias determination: `v1/v2=christian, v3/v4=victor`
- [ ] Enforce 1 active campaign per domain (409 error)

### Frontend Changes
- [ ] Simplify `CampaignNew.tsx` to 3 steps
- [ ] Remove Step 3 "Verzendregels" (all hard-coded)
- [ ] Remove template dropdown
- [ ] Remove domain checkboxes
- [ ] Add auto-assigned info display in Review
- [ ] Update payload to `SimplifiedCampaignPayload`
- [ ] Enhance dry-run to show flow/alias info

### Documentation
- [ ] Update `api.md` with simplified payload
- [ ] Add alias-per-version to campaign docs
- [ ] Document 12 mails/uur capacity (4 domains parallel)

---

**Status:** ✅ Spec Complete - Ready for Implementation  
**Estimated Effort:** 4-6 hours (backend 2h, frontend 3h, testing 1h)
