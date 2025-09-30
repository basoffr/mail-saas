# Global Campaign Settings Implementation Plan

## Overzicht
Plan voor het implementeren van bewerkbare globale instellingen (Timezone, Verzendvenster, Throttle) die gebruikt worden als defaults voor alle campagnes, met mogelijkheid voor per-campagne overrides.

## 1. Backend Aanpassingen

### 1.1 Settings Schema Updates
**File**: `backend/app/schemas/settings.py`

```python
# Toevoegen aan SettingsUpdate
class SettingsUpdate(BaseModel):
    # Bestaande velden
    unsubscribe_text: Optional[str] = None
    tracking_pixel_enabled: Optional[bool] = None
    
    # NIEUWE VELDEN
    timezone: Optional[str] = None
    sending_window_start: Optional[str] = None  # "HH:MM" format
    sending_window_end: Optional[str] = None    # "HH:MM" format
    sending_days: Optional[List[str]] = None    # ["Mon", "Tue", ...]
    throttle_minutes: Optional[int] = None      # 1-120 minuten

# Nieuwe validatie schemas
class TimezoneValidator(BaseModel):
    timezone: str
    
    @validator('timezone')
    def validate_timezone(cls, v):
        import pytz
        if v not in pytz.all_timezones:
            raise ValueError('Invalid timezone')
        return v

class TimeValidator(BaseModel):
    time: str
    
    @validator('time')
    def validate_time_format(cls, v):
        import re
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Time must be in HH:MM format')
        return v
```

### 1.2 Settings Service Updates
**File**: `backend/app/services/settings.py`

```python
def update_settings(self, updates: SettingsUpdate) -> SettingsOut:
    """Update settings - UITBREIDEN met nieuwe velden"""
    
    # Bestaande validatie...
    
    # NIEUWE VALIDATIES
    if updates.timezone is not None:
        self._validate_timezone(updates.timezone)
        self._settings.timezone = updates.timezone
    
    if updates.sending_window_start is not None:
        self._validate_time_format(updates.sending_window_start)
        self._settings.sending_window_start = updates.sending_window_start
    
    if updates.sending_window_end is not None:
        self._validate_time_format(updates.sending_window_end)
        self._settings.sending_window_end = updates.sending_window_end
        
    if updates.sending_days is not None:
        self._validate_sending_days(updates.sending_days)
        self._settings.sending_days = updates.sending_days
    
    if updates.throttle_minutes is not None:
        self._validate_throttle_minutes(updates.throttle_minutes)
        self._settings.throttle_minutes = updates.throttle_minutes
    
    return self.get_settings()

# NIEUWE VALIDATIE METHODEN
def _validate_timezone(self, timezone: str):
    import pytz
    if timezone not in pytz.all_timezones:
        raise ValueError(f"Invalid timezone: {timezone}")

def _validate_time_format(self, time_str: str):
    import re
    if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
        raise ValueError(f"Invalid time format: {time_str}")

def _validate_sending_days(self, days: List[str]):
    valid_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for day in days:
        if day not in valid_days:
            raise ValueError(f"Invalid day: {day}")

def _validate_throttle_minutes(self, minutes: int):
    if not (1 <= minutes <= 120):
        raise ValueError("Throttle must be between 1 and 120 minutes")
```

### 1.3 Campaign Model Updates
**File**: `backend/app/models/campaign.py`

```python
class Campaign(SQLModel, table=True):
    # Bestaande velden...
    
    # NIEUWE OVERRIDE VELDEN
    timezone_override: Optional[str] = None
    sending_window_start_override: Optional[str] = None
    sending_window_end_override: Optional[str] = None
    sending_days_override: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    throttle_minutes_override: Optional[int] = None
    
    # Helper methods
    def get_effective_timezone(self, global_settings) -> str:
        return self.timezone_override or global_settings.timezone
    
    def get_effective_window(self, global_settings) -> tuple:
        start = self.sending_window_start_override or global_settings.sending_window_start
        end = self.sending_window_end_override or global_settings.sending_window_end
        return (start, end)
    
    def get_effective_days(self, global_settings) -> List[str]:
        return self.sending_days_override or global_settings.sending_days
    
    def get_effective_throttle(self, global_settings) -> int:
        return self.throttle_minutes_override or global_settings.throttle_minutes
```

### 1.4 Campaign Schema Updates
**File**: `backend/app/schemas/campaign.py`

```python
class CampaignCreate(BaseModel):
    # Bestaande velden...
    
    # NIEUWE OVERRIDE VELDEN (optioneel)
    timezone_override: Optional[str] = None
    sending_window_start_override: Optional[str] = None
    sending_window_end_override: Optional[str] = None
    sending_days_override: Optional[List[str]] = None
    throttle_minutes_override: Optional[int] = None

class CampaignOut(BaseModel):
    # Bestaande velden...
    
    # NIEUWE VELDEN
    effective_timezone: str
    effective_window: dict  # {"start": "08:00", "end": "17:00"}
    effective_days: List[str]
    effective_throttle: int
    
    # Override indicators
    has_timezone_override: bool
    has_window_override: bool
    has_days_override: bool
    has_throttle_override: bool
```

### 1.5 Campaign Service Updates
**File**: `backend/app/services/campaign_store.py`

```python
def create_campaign(self, campaign_data: dict) -> dict:
    # Bestaande logica...
    
    # SETTINGS INTEGRATION
    from app.services.settings import settings_service
    global_settings = settings_service._settings
    
    # Apply global settings als defaults
    if 'timezone_override' not in campaign_data:
        campaign_data['effective_timezone'] = global_settings.timezone
    
    # Etc. voor alle settings...
    
    return campaign
```

### 1.6 Campaign Scheduler Updates
**File**: `backend/app/services/campaign_scheduler.py`

```python
def schedule_campaign(self, campaign_id: str) -> dict:
    campaign = campaign_store.get_campaign(campaign_id)
    global_settings = settings_service._settings
    
    # GEBRUIK EFFECTIVE SETTINGS
    timezone = campaign.get_effective_timezone(global_settings)
    window_start, window_end = campaign.get_effective_window(global_settings)
    sending_days = campaign.get_effective_days(global_settings)
    throttle = campaign.get_effective_throttle(global_settings)
    
    # Schedule met deze instellingen...
```

### 1.7 Message Sender Updates
**File**: `backend/app/services/message_sender.py`

```python
def send_message(self, message_id: str):
    message = messages_store.get_message(message_id)
    campaign = campaign_store.get_campaign(message['campaign_id'])
    global_settings = settings_service._settings
    
    # GEBRUIK EFFECTIVE THROTTLE
    throttle = campaign.get_effective_throttle(global_settings)
    
    # Apply throttle per domain...
```

## 2. Frontend Aanpassingen

### 2.1 Settings Types Update
**File**: `vitalign-pro/src/types/settings.ts`

```typescript
export interface SettingsUpdateRequest {
  // Bestaande velden
  unsubscribeText?: string;
  trackingPixelEnabled?: boolean;
  
  // NIEUWE VELDEN
  timezone?: string;
  sendingWindowStart?: string;  // "HH:MM"
  sendingWindowEnd?: string;    // "HH:MM"
  sendingDays?: string[];       // ["ma", "di", ...]
  throttleMinutes?: number;     // 1-120
}

export interface Settings {
  // Bestaande velden...
  
  // Update window type
  window: {
    days: string[];
    from: string;
    to: string;
    editable: boolean;  // NIEUW
  };
  
  throttle: {
    emailsPer: number;
    minutes: number;
    editable: boolean;  // NIEUW
  };
  
  timezone: string;
  timezoneEditable: boolean;  // NIEUW
}
```

### 2.2 Settings Service Update
**File**: `vitalign-pro/src/services/settings.ts`

```typescript
async updateSettings(updates: SettingsUpdateRequest): Promise<SettingsResponse> {
  // NIEUWE VALIDATIES
  if (updates.timezone && !this.isValidTimezone(updates.timezone)) {
    return { ok: false, message: 'Ongeldige timezone' };
  }
  
  if (updates.sendingWindowStart && !this.isValidTimeFormat(updates.sendingWindowStart)) {
    return { ok: false, message: 'Ongeldige start tijd format (HH:MM)' };
  }
  
  // Etc...
  
  // Update local state
  if (updates.timezone) this.settings.timezone = updates.timezone;
  if (updates.sendingWindowStart) this.settings.window.from = updates.sendingWindowStart;
  // Etc...
}

private isValidTimezone(timezone: string): boolean {
  // Timezone validatie
}

private isValidTimeFormat(time: string): boolean {
  return /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/.test(time);
}
```

### 2.3 Settings UI Components
**File**: `vitalign-pro/src/components/settings/EditableSettingsSection.tsx`

```typescript
// NIEUWE COMPONENT voor bewerkbare instellingen
export const EditableSettingsSection = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    timezone: '',
    sendingWindowStart: '',
    sendingWindowEnd: '',
    sendingDays: [],
    throttleMinutes: 20
  });
  
  // Form handling, validation, submit...
};
```

### 2.4 Campaign Types Update
**File**: `vitalign-pro/src/types/campaigns.ts`

```typescript
export interface CampaignCreateRequest {
  // Bestaande velden...
  
  // NIEUWE OVERRIDE VELDEN
  timezoneOverride?: string;
  sendingWindowStartOverride?: string;
  sendingWindowEndOverride?: string;
  sendingDaysOverride?: string[];
  throttleMinutesOverride?: number;
}

export interface Campaign {
  // Bestaande velden...
  
  // NIEUWE EFFECTIVE SETTINGS
  effectiveTimezone: string;
  effectiveWindow: { start: string; end: string };
  effectiveDays: string[];
  effectiveThrottle: number;
  
  // OVERRIDE INDICATORS
  hasTimezoneOverride: boolean;
  hasWindowOverride: boolean;
  hasDaysOverride: boolean;
  hasThrottleOverride: boolean;
}
```

### 2.5 Campaign Wizard Updates
**File**: `vitalign-pro/src/pages/campaigns/NewCampaign.tsx`

```typescript
// Step 3: Verzendregels - UITBREIDEN
const VerzendregelsStep = () => {
  const { data: globalSettings } = useQuery(['settings'], settingsService.getSettings);
  const [useGlobalSettings, setUseGlobalSettings] = useState(true);
  const [overrides, setOverrides] = useState({});
  
  return (
    <div>
      <div className="mb-4">
        <Label>
          <Checkbox 
            checked={useGlobalSettings}
            onCheckedChange={setUseGlobalSettings}
          />
          Gebruik globale instellingen
        </Label>
      </div>
      
      {!useGlobalSettings && (
        <div>
          {/* Override formulieren voor timezone, window, throttle */}
        </div>
      )}
      
      <div className="mt-4 p-4 bg-muted rounded">
        <h4>Effectieve Instellingen:</h4>
        <p>Timezone: {getEffectiveTimezone()}</p>
        <p>Verzendvenster: {getEffectiveWindow()}</p>
        <p>Throttle: {getEffectiveThrottle()}</p>
      </div>
    </div>
  );
};
```

## 3. Testing Updates

### 3.1 Settings Tests
**File**: `backend/app/tests/test_settings.py`

```python
def test_update_timezone():
    """Test timezone update"""
    
def test_update_sending_window():
    """Test sending window update"""
    
def test_update_throttle():
    """Test throttle update"""
    
def test_invalid_timezone():
    """Test invalid timezone rejection"""
    
def test_invalid_time_format():
    """Test invalid time format rejection"""
```

### 3.2 Campaign Integration Tests
**File**: `backend/app/tests/test_campaign_settings_integration.py`

```python
def test_campaign_inherits_global_settings():
    """Test dat nieuwe campagne globale settings overneemt"""
    
def test_campaign_override_settings():
    """Test dat campagne eigen settings kan hebben"""
    
def test_effective_settings_calculation():
    """Test berekening van effective settings"""
```

## 4. Database Migratie Voorbereiding

### 4.1 Settings Table
```sql
-- Nieuwe kolommen voor bewerkbare status
ALTER TABLE settings ADD COLUMN timezone_editable BOOLEAN DEFAULT TRUE;
ALTER TABLE settings ADD COLUMN window_editable BOOLEAN DEFAULT TRUE;
ALTER TABLE settings ADD COLUMN throttle_editable BOOLEAN DEFAULT TRUE;
```

### 4.2 Campaign Table
```sql
-- Override kolommen
ALTER TABLE campaigns ADD COLUMN timezone_override VARCHAR(50);
ALTER TABLE campaigns ADD COLUMN sending_window_start_override TIME;
ALTER TABLE campaigns ADD COLUMN sending_window_end_override TIME;
ALTER TABLE campaigns ADD COLUMN sending_days_override JSON;
ALTER TABLE campaigns ADD COLUMN throttle_minutes_override INTEGER;
```

## 5. Implementatie Volgorde

### Fase 1: Backend Core (Week 1)
1. Settings schema updates
2. Settings service validation
3. Basic tests

### Fase 2: Campaign Integration (Week 2)
1. Campaign model updates
2. Campaign service integration
3. Scheduler updates
4. Message sender updates

### Fase 3: Frontend Core (Week 3)
1. Settings types updates
2. Settings service updates
3. Basic UI components

### Fase 4: Campaign Frontend (Week 4)
1. Campaign wizard updates
2. Campaign detail updates
3. Override UI components

### Fase 5: Testing & Polish (Week 5)
1. Comprehensive testing
2. UI/UX improvements
3. Documentation updates

## 6. Risico's & Overwegingen

### Technische Risico's
- **Backward Compatibility**: Bestaande campagnes moeten blijven werken
- **Performance**: Extra queries voor settings bij elke campaign operation
- **Validation Complexity**: Meerdere lagen van validatie (client/server/database)

### UX Overwegingen
- **Complexity**: Niet te complex maken voor gebruikers
- **Clear Hierarchy**: Duidelijk maken wat globaal vs campagne-specifiek is
- **Impact Warnings**: Waarschuwen bij wijzigingen die actieve campagnes beïnvloeden

### Mitigatie Strategieën
- **Caching**: Settings cachen om performance te behouden
- **Gradual Rollout**: Feature flags voor geleidelijke uitrol
- **Extensive Testing**: Vooral edge cases en backward compatibility

## 7. Success Criteria

### Functioneel
- ✅ Globale settings zijn bewerkbaar via UI
- ✅ Nieuwe campagnes nemen globale settings over
- ✅ Campagnes kunnen settings overriden
- ✅ Scheduler respecteert effective settings
- ✅ Throttling werkt per effective settings

### Technisch
- ✅ Alle tests passing (>95% coverage)
- ✅ Performance impact <10%
- ✅ Backward compatibility maintained
- ✅ Clean code architecture

### UX
- ✅ Intuitive settings interface
- ✅ Clear override indicators
- ✅ Helpful validation messages
- ✅ Impact warnings where needed

---

**Totale Geschatte Effort**: 5 weken (1 developer)
**Complexiteit**: Hoog (raakt alle lagen van de applicatie)
**Business Value**: Hoog (flexibiliteit voor verschillende campagne types)

# 🔒 Guardrails (Niet-onderhandelbaar)

- GEEN overrides in UI of per campagne of alias. Elk PR dat dit toevoegt = reject.
- /settings: alleen GET. POST/PUT/PATCH voor sending policy/flows = 405 of `{error:"hard-coded"}`.
- Domein-throttle is heilig: 1/20m PER DOMEIN, slotgrid :00/:20/:40, [08:00,17:00), laatste slot 16:40, dagcap 27, grace tot 18:00.
- Max 1 campagne ACTIEF per domein. Nieuwe campagne op dat domein ⇒ 409 "domain busy".
- Intervals zijn +3 WERKDAGEN. Weekend = geen slots. Alles buiten venster/weekend ⇒ push naar eerstvolgend geldig slot (meestal ma 08:00).
- Backlog wordt NOOIT geskipt; altijd doorrollen tot dagcap en dan naar volgende werkdag 08:00.
- Alias-rollen staan vast per flow: M1+M2=christian, M3+M4=victor. From/Reply-To voor follow-ups: From=Victor, Reply-To=Christian.
- Templates zijn hard-coded per versie/mail. Geen dynamische aanpassing buiten placeholders.
- Open items (unsub/bounce, rapport/afbeeldingen, handtekening) zijn PENDING → NIET implementeren zonder expliciete nieuwe opdracht.

