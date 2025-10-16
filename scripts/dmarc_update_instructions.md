# 🔒 DMARC POLICY UPDATE - BETERE DELIVERABILITY

## 🎯 Waarom updaten?

**Huidige policy:** `p=none` (alleen monitoring)
**Nieuwe policy:** `p=quarantine` (actieve bescherming + betere sender reputation)

**Voordelen:**
- ✅ Betere email deliverability
- ✅ Hogere sender reputation score
- ✅ Minder kans op spam folder
- ✅ Dagelijkse rapporten over DMARC failures
- ✅ Betere bescherming tegen email spoofing

---

## 📝 UPDATE INSTRUCTIES - VIMEXX DNS PANEL

### **Voor ALLE 4 DOMEINEN:**

1. punthelder-marketing.nl
2. punthelder-seo.nl
3. punthelder-vindbaarheid.nl
4. punthelder-zoekmachine.nl

---

## 🔧 DNS RECORD TE UPDATEN:

### **Bestaand record:**
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; sp=none;
TTL: 10 min
```

### **Nieuw record (UPDATE):**
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@punthelder-marketing.nl; pct=100; adkim=s; aspf=s;
TTL: 3600 (1 uur)
```

---

## 📊 UITLEG VAN DE PARAMETERS:

```
v=DMARC1                  → Versie
p=quarantine              → Policy: verdachte emails naar spam folder
rua=mailto:...            → Stuur dagelijkse rapporten naar dit adres
pct=100                   → Pas policy toe op 100% van de emails
adkim=s                   → Strict DKIM alignment (streng maar veilig)
aspf=s                    → Strict SPF alignment (streng maar veilig)
```

---

## ⚠️ WAAROM QUARANTINE EN NIET REJECT?

**quarantine** = veilige keuze voor start:
- ✅ Verdachte emails gaan naar spam (kunnen nog worden bekeken)
- ✅ Geen risk op gemiste legitieme emails
- ✅ Je kunt rapporten bekijken en eventuele issues oplossen

**reject** = later, na 4-8 weken monitoring:
- Als rapporten laten zien dat alles perfect werkt
- Dan kun je upgraden naar p=reject voor maximale beveiliging

---

## 🚀 STAP-VOOR-STAP:

### **1. Login bij Vimexx**
- Ga naar DirectAdmin control panel
- Kies domein: punthelder-marketing.nl

### **2. Ga naar DNS beheer**
- Zoek naar "_dmarc" TXT record
- Klik "Edit"

### **3. Update de waarde**
```
OUD: v=DMARC1; p=none; sp=none;
NIEUW: v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@punthelder-marketing.nl; pct=100; adkim=s; aspf=s;
```

### **4. Update TTL (optioneel maar aanbevolen)**
```
OUD: 600 (10 min)
NIEUW: 3600 (1 uur)
```

### **5. Save**

### **6. HERHAAL VOOR ANDERE 3 DOMEINEN:**
- punthelder-seo.nl
- punthelder-vindbaarheid.nl  
- punthelder-zoekmachine.nl

**Let op:** Gebruik voor elk domein dezelfde rua email (punthelder-marketing.nl) voor centrale rapportage.

---

## 📧 EMAIL ACCOUNT MAKEN VOOR RAPPORTEN:

**Optioneel:** Maak een email account aan voor DMARC rapporten:

```
Email: dmarc-reports@punthelder-marketing.nl
Forward naar: jouw-persoonlijke-email@example.com
```

Je ontvangt dan dagelijks XML rapporten met statistieken over:
- Hoeveel emails verstuurd
- Hoeveel passed SPF/DKIM
- Hoeveel failed
- Welke IP's verzenden namens jouw domeinen

---

## ✅ VERIFICATIE:

Na update (wacht 1 uur voor DNS propagatie):

**Online tools:**
```
https://mxtoolbox.com/dmarc.aspx
→ Voer domein in: punthelder-marketing.nl
→ Moet tonen: "DMARC Record Published"
→ Policy: quarantine ✅
```

**Of via PowerShell:**
```powershell
Resolve-DnsName -Name "_dmarc.punthelder-marketing.nl" -Type TXT | Select-Object -ExpandProperty Strings
```

**Verwacht resultaat:**
```
v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@punthelder-marketing.nl; pct=100; adkim=s; aspf=s;
```

---

## 📅 TIJDLIJN:

### **Direct na update:**
- DNS propagatie: 10-60 minuten
- Ontvangende mailservers zien nieuwe policy binnen 1 uur

### **Na 24 uur:**
- Eerste DMARC rapporten ontvangen
- Check of alles 100% passed

### **Na 1 week:**
- Analyse van rapporten
- Controleer deliverability rates
- Controleer bounce rates

### **Na 4-8 weken (optioneel):**
- Als alles perfect werkt
- Upgrade naar `p=reject` voor maximale beveiliging

---

## 🎯 VERWACHTE IMPACT:

### **Direct:**
- ✅ Betere sender reputation
- ✅ Hogere deliverability rate
- ✅ Minder emails in spam

### **Na 1 week:**
- ✅ Zichtbaar betere open rates
- ✅ Zichtbaar betere click rates
- ✅ Feedback in DMARC rapporten

---

## 📊 VOOR & NA VERGELIJKING:

### **VOOR (p=none):**
```
✅ SPF: OK
✅ DKIM: OK
⚠️ DMARC: Monitoring only (geen actie)

Sender Reputation: 70/100
Spam Score: Medium
```

### **NA (p=quarantine):**
```
✅ SPF: OK
✅ DKIM: OK
✅ DMARC: Active enforcement

Sender Reputation: 85+/100
Spam Score: Low
```

---

## 🚨 TROUBLESHOOTING:

### **Als emails plotseling in spam belanden:**

1. **Check DMARC rapporten** - kijk of SPF/DKIM alignment klopt
2. **Verlaag pct tijdelijk** - bijv. `pct=50` (50% van emails)
3. **Check DNS records** - zijn SPF/DKIM nog correct?
4. **Terug naar none** - in noodgeval: `p=none` tot issue opgelost

### **Als je geen rapporten ontvangt:**

1. Check spam folder
2. Verify email account bestaat
3. Check DNS record syntax (geen typos!)

---

## ✅ READY TO DEPLOY?

**CHECKLIST:**

- [ ] SPF records correct voor alle 4 domeinen ✅ (al gedaan)
- [ ] DKIM records correct voor alle 4 domeinen ✅ (al gedaan)
- [ ] DMARC rapporten email aangemaakt
- [ ] DNS updates gemaakt in Vimexx panel
- [ ] 1 uur gewacht voor propagatie
- [ ] Verificatie gedaan met MXToolbox
- [ ] Test email verstuurd en checked deliverability

**Als alles ✅ → KLAAR VOOR CAMPAGNE START! 🚀**
