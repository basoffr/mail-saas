# 🧪 FASE 4: TESTSEND BEHAVES LIKE REAL SENDS (STATS-EXEMPT)

**Status**: 📝 Planning Phase  
**Datum**: 9 oktober 2025  
**Priority**: High (User Experience Critical)

---

## 🎯 **OBJECTIVE**

Testsends moeten **identiek** werken als campagne-mails (rendering, assets, tracking), maar:
- ❌ **Niet meetellen** in statistieken/tiles/exports
- ❌ **Geen throttling** triggeren
- ❌ **Geen permanente state-mutaties** (unsub/bounce blijven test-only)

---

## 📊 **CURRENT STATE ANALYSIS**

### **✅ WAT WERKT**
1. **Testsend Service** (`app/services/testsend.py`):
   - Rate limiting (5/min per user)
   - SMTP sending (real + simulation)
   - Basic logging (`mail_send_ok`, `mail_send_err`)

2. **Campaign Pipeline** (`app/services/message_sender.py`):
   - Full personalization (lead.*, vars.*, campaign.*)
   - Asset embedding (signatures, dashboard images)
   - Tracking pixel injection
   - Event logging (sent, opened, bounced)
   - SMTP headers (From, Reply-To, Message-ID)

### **❌ WAT ONTBREEKT**
1. **Geen unified data model**:
   - Testsends slaan NIETS op in database
   - Geen log entries, geen tracking mogelijk
   - Geen zichtbaarheid in dashboard

2. **Testsends != Campaign mails**:
   - Andere code path (geen signature injection, assets, tracking)
   - Geen personalization met lead data
   - Geen CID embedding voor images

3. **Geen `is_test` flag**:
   - Stats queries kunnen niet filteren
   - Risk of pollution in production metrics

4. **Geen Test Center UI**:
   - Geen overzicht van verzonden testmails
   - Geen event timeline zichtbaar

---

## 🏗️ **ARCHITECTURE DESIGN**

### **1. DATA MODEL**

#### **New Table: `mail_logs`**
Unified log voor ALLE emails (campaign + test):

```sql
CREATE TABLE mail_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Type & flags
    is_test BOOLEAN NOT NULL DEFAULT false,
    mail_type VARCHAR(20) NOT NULL,  -- 'campaign', 'testsend', 'followup'
    
    -- References (nullable for tests)
    campaign_id UUID REFERENCES campaigns(id),
    message_id UUID REFERENCES messages(id),  -- NULL voor testsends
    lead_id UUID REFERENCES leads(id),        -- NULL indien geen lead
    template_id VARCHAR(50) NOT NULL,
    
    -- Recipient & sender
    to_email VARCHAR(255) NOT NULL,
    from_email VARCHAR(255) NOT NULL,
    reply_to_email VARCHAR(255),
    subject TEXT NOT NULL,
    
    -- Metadata
    domain_used VARCHAR(100),
    mail_number INTEGER,  -- 1-4 voor campaign flow
    alias VARCHAR(20),    -- 'christian' of 'victor'
    
    -- Assets
    with_signature BOOLEAN DEFAULT false,
    with_dashboard_image BOOLEAN DEFAULT false,
    with_report BOOLEAN DEFAULT false,
    
    -- Tracking IDs
    smtp_message_id VARCHAR(255) UNIQUE,
    tracking_pixel_url TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'queued',  -- 'queued', 'sent', 'bounced', 'failed'
    sent_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_mail_logs_is_test (is_test),
    INDEX idx_mail_logs_campaign (campaign_id),
    INDEX idx_mail_logs_lead (lead_id),
    INDEX idx_mail_logs_created (created_at DESC),
    INDEX idx_mail_logs_status (status)
);
```

#### **New Table: `mail_events`**
Tracking events voor ALLE emails:

```sql
CREATE TABLE mail_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Reference
    mail_log_id UUID NOT NULL REFERENCES mail_logs(id) ON DELETE CASCADE,
    is_test BOOLEAN NOT NULL DEFAULT false,
    
    -- Event details
    event_type VARCHAR(20) NOT NULL,  -- 'sent', 'delivered', 'opened', 'clicked', 'bounced', 'unsubscribed'
    event_data JSONB,
    
    -- Tracking metadata
    user_agent TEXT,
    ip_address VARCHAR(45),
    referer TEXT,
    
    -- Link tracking (voor clicks)
    target_url TEXT,
    link_hash VARCHAR(64),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_mail_events_log (mail_log_id),
    INDEX idx_mail_events_is_test (is_test),
    INDEX idx_mail_events_type (event_type),
    INDEX idx_mail_events_created (created_at DESC)
);
```

---

### **2. SERVICE LAYER REFACTOR**

#### **New: `unified_mail_sender.py`**
Unified sending pipeline voor campaign + test:

```python
class UnifiedMailSender:
    """
    Unified mail sending pipeline.
    Handles both campaign and test emails with identical logic.
    """
    
    async def send_mail(
        self,
        template_id: str,
        to_email: str,
        lead_data: Dict[str, Any],
        is_test: bool = False,
        campaign_id: Optional[str] = None,
        mail_number: int = 1
    ) -> Dict[str, Any]:
        """
        Send email through unified pipeline.
        
        Args:
            template_id: Template to use
            to_email: Recipient email
            lead_data: Lead personalization data
            is_test: True for testsends, False for campaigns
            campaign_id: Optional campaign reference
            mail_number: Mail number in flow (1-4)
        
        Returns:
            {"success": bool, "log_id": str, "message_id": str}
        """
        
        # 1. Get template (hybrid service)
        template = hybrid_template_service.get_template(template_id)
        
        # 2. Render template with full personalization
        rendered = render_template_with_lead(
            template=template,
            lead_data=lead_data,
            campaign_data={...},
            inject_tracking=True,
            is_test=is_test
        )
        
        # 3. Inject signature (CID)
        alias = get_alias_from_mail_number(mail_number)
        html = inject_signature_cid(rendered['html'], alias)
        
        # 4. Inject tracking pixel
        log_id = str(uuid.uuid4())
        if settings.tracking_pixel_enabled:
            tracking_url = f"{BASE_URL}/t/o/{log_id}?t={'1' if is_test else '0'}"
            html = inject_tracking_pixel(html, tracking_url)
        
        # 5. Create mail log entry
        mail_log = await self._create_mail_log(
            log_id=log_id,
            is_test=is_test,
            template_id=template_id,
            to_email=to_email,
            subject=rendered['subject'],
            # ... other fields
        )
        
        # 6. Send via SMTP with assets
        smtp_result = await self._send_via_smtp(
            to_email=to_email,
            subject=rendered['subject'],
            html=html,
            assets={
                'signature': alias,
                'dashboard': lead_data.get('domain'),
                'report': template_id in ['v1_mail1', 'v2_mail1']
            }
        )
        
        # 7. Update log status
        if smtp_result['success']:
            await self._update_mail_log(log_id, {
                'status': 'sent',
                'sent_at': datetime.utcnow(),
                'smtp_message_id': smtp_result['message_id']
            })
            await self._create_event(log_id, 'sent', is_test=is_test)
        else:
            await self._update_mail_log(log_id, {
                'status': 'failed',
                'last_error': smtp_result['error']
            })
        
        return {
            'success': smtp_result['success'],
            'log_id': log_id,
            'message_id': smtp_result.get('message_id')
        }
```

---

### **3. TRACKING ENDPOINTS**

#### **Open Pixel Tracking**
```python
@router.get("/t/o/{log_id}")
async def track_open(log_id: str, t: str = "0", user_agent: str = Header(None)):
    """Track email open event"""
    is_test = (t == "1")
    
    # Create event
    await mail_events_store.create({
        'mail_log_id': log_id,
        'event_type': 'opened',
        'is_test': is_test,
        'user_agent': user_agent,
        'ip_address': request.client.host
    })
    
    # Update mail log
    if not is_test:
        await mail_logs_store.mark_opened(log_id)
    
    # Return 1x1 transparent pixel
    return Response(content=TRACKING_PIXEL_GIF, media_type="image/gif")
```

#### **Link Click Tracking**
```python
@router.get("/t/c/{log_id}/{link_hash}")
async def track_click(
    log_id: str, 
    link_hash: str, 
    t: str = "0",
    user_agent: str = Header(None)
):
    """Track link click and redirect"""
    is_test = (t == "1")
    
    # Get target URL from hash
    target_url = await link_tracker.get_url(link_hash)
    
    # Create event
    await mail_events_store.create({
        'mail_log_id': log_id,
        'event_type': 'clicked',
        'is_test': is_test,
        'target_url': target_url,
        'link_hash': link_hash,
        'user_agent': user_agent
    })
    
    # Redirect
    return RedirectResponse(url=target_url)
```

---

### **4. STATISTICS EXCLUSION**

#### **SQL Views for Production Stats**
```sql
-- View: Production-only mail logs
CREATE VIEW mail_logs_prod AS
SELECT * FROM mail_logs
WHERE is_test = false;

-- View: Production-only events
CREATE VIEW mail_events_prod AS
SELECT * FROM mail_events
WHERE is_test = false;

-- Stats aggregation example
CREATE VIEW campaign_stats AS
SELECT
    campaign_id,
    COUNT(*) as total_sent,
    COUNT(CASE WHEN status = 'sent' THEN 1 END) as delivered,
    COUNT(CASE WHEN status = 'opened' THEN 1 END) as opened,
    COUNT(CASE WHEN status = 'bounced' THEN 1 END) as bounced
FROM mail_logs_prod
GROUP BY campaign_id;
```

#### **Application-level Filtering**
```python
# In statistics service
class StatsService:
    def get_global_stats(self, include_tests: bool = False):
        """Get global statistics"""
        filter_clause = "" if include_tests else "WHERE is_test = false"
        
        query = f"""
            SELECT 
                COUNT(*) as total_sent,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as delivered,
                (COUNT(CASE WHEN status = 'opened' THEN 1 END)::float / 
                 NULLIF(COUNT(CASE WHEN status = 'sent' THEN 1 END), 0)) * 100 as open_rate
            FROM mail_logs
            {filter_clause}
        """
        
        return await self.db.execute(query)
```

---

### **5. BUSINESS RULES**

#### **No Throttling for Tests**
```python
# In scheduler
async def schedule_next_slot(is_test: bool = False):
    if is_test:
        # Tests bypass throttling completely
        return datetime.utcnow()
    
    # Normal throttling for campaigns
    return await self._get_next_available_slot(domain)
```

#### **No Permanent State Mutations**
```python
# In event handler
async def handle_unsubscribe_event(event: MailEvent):
    if event.is_test:
        # Log event but DON'T update lead
        logger.info(f"Test unsubscribe: {event.mail_log_id} (NO ACTION TAKEN)")
        return
    
    # Real unsubscribe: update lead to suppressed
    lead = await leads_store.get_by_email(event.to_email)
    lead.status = LeadStatus.suppressed
    await leads_store.update(lead)

async def handle_bounce_event(event: MailEvent):
    if event.is_test:
        # Log event but DON'T mark lead as bounced
        logger.info(f"Test bounce: {event.mail_log_id} (NO ACTION TAKEN)")
        return
    
    # Real bounce: mark lead
    lead = await leads_store.get_by_email(event.to_email)
    lead.status = LeadStatus.bounced
    await leads_store.update(lead)
```

---

## 🚀 **IMPLEMENTATION PHASES**

### **Phase 1: Data Model (SQL)**
- [ ] Create `mail_logs` table
- [ ] Create `mail_events` table
- [ ] Create production views (`mail_logs_prod`, `mail_events_prod`)
- [ ] Add indexes for performance

### **Phase 2: Service Layer**
- [ ] Create `unified_mail_sender.py`
- [ ] Refactor testsend to use unified sender
- [ ] Add `is_test` parameter throughout pipeline
- [ ] Update template renderer for tracking URLs

### **Phase 3: Tracking Endpoints**
- [ ] Implement `/t/o/{log_id}` (open pixel)
- [ ] Implement `/t/c/{log_id}/{hash}` (link click)
- [ ] Add `is_test` handling in all tracking
- [ ] Test tracking with real Gmail/Outlook

### **Phase 4: Statistics Exclusion**
- [ ] Update all stats queries with `WHERE is_test = false`
- [ ] Add `include_tests` toggle for debugging
- [ ] Verify dashboard tiles exclude tests
- [ ] Verify exports exclude tests

### **Phase 5: UI - Test Center**
- [ ] Create "Test Mails" tab in dashboard
- [ ] List view with filters (date, template, recipient)
- [ ] Detail view with event timeline
- [ ] Preview link for test emails

### **Phase 6: Business Rules**
- [ ] Bypass throttling for `is_test=true`
- [ ] No-op unsub for tests
- [ ] No-op bounce for tests
- [ ] Add structured logging with `is_test` flag

---

## ✅ **ACCEPTANCE CRITERIA**

### **Functional**
1. ✅ POST `/templates/v1_mail1/testsend` sends mail with:
   - Correct personalization (lead.*, vars.*)
   - Inline signature via CID
   - Working tracking pixel
   - Working link tracking

2. ✅ Test events are logged in `mail_events` with `is_test=true`

3. ✅ Test unsub does NOT change lead status

4. ✅ Test bounce does NOT change lead status

5. ✅ Dashboard stats/tiles exclude tests (unless toggle enabled)

### **Technical**
6. ✅ Render logs show `mail_send_ok {"is_test": true}`

7. ✅ SQL query `SELECT * FROM mail_logs WHERE is_test=true` shows test sends

8. ✅ No throttling delay for test sends

9. ✅ Test Center UI shows all test mails with events

### **Performance**
10. ✅ Test send completes in <5s
11. ✅ Stats queries remain fast (<100ms) with `is_test` index

---

## 🔒 **SECURITY & RATE LIMITING**

### **Testsend Rate Limiting**
- **Current**: 5/min per user (in-memory)
- **Production**: Redis-backed, 20/min per user

### **Auth Requirements**
- All `/testsend` endpoints require JWT
- All `/t/*` tracking endpoints are public (by design)

### **Abuse Prevention**
- IP-based rate limiting on tracking endpoints
- Honeypot detection for bot traffic
- User-Agent validation

---

## 📊 **MONITORING & OBSERVABILITY**

### **Structured Logs**
```json
{
  "event": "mail_send_ok",
  "is_test": true,
  "log_id": "uuid",
  "template_id": "v1_mail1",
  "to": "test@example.com",
  "message_id": "smtp-id",
  "duration_ms": 234
}
```

### **Metrics to Track**
- `mail_send_total{is_test="true"}` - Total test sends
- `mail_send_duration{is_test="true"}` - Test send latency
- `mail_events_total{is_test="true", event_type="opened"}` - Test opens
- `testsend_rate_limit_hits` - Rate limit rejections

---

## 🎯 **ROLLOUT PLAN**

### **Week 1: Foundation**
- Implement data model (SQL)
- Create unified sender service
- Basic tracking endpoints

### **Week 2: Integration**
- Refactor testsend to use unified pipeline
- Add statistics exclusion
- Implement business rules (no state mutations)

### **Week 3: UI & Polish**
- Build Test Center UI
- Add debugging toggle for stats
- Comprehensive testing

### **Week 4: Production Release**
- Deploy to staging
- User acceptance testing
- Deploy to production
- Monitor metrics

---

## 📝 **MIGRATION NOTES**

### **Backward Compatibility**
- Existing `messages` table remains unchanged
- Campaign sends continue to use `messages` + new `mail_logs`
- Old stats queries work (filter `WHERE campaign_id IS NOT NULL`)

### **Data Backfill**
Not needed - fresh start for `mail_logs` table.

---

## 🔗 **RELATED DOCUMENTS**
- `FASE_3_HYBRID_TEMPLATE_STORE_PLAN.md` - Template system
- `FASE_3_ASSETS_DOCUMENTATIE.md` - Asset handling
- `backend/app/services/message_sender.py` - Current campaign pipeline
- `backend/app/services/testsend.py` - Current testsend service
