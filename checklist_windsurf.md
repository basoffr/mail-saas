# 📋 Checklist – Variabelen, Rapporten & Afbeeldingen in Leads  

Dit document beschrijft de wijzigingen die doorgevoerd moeten worden in het dashboard en de database, zodat alle variabelen, rapporten en afbeeldingen volledig inzichtelijk zijn per lead.  

---

## 1. Variabelen per Lead
Elke lead moet een **volledig overzicht tonen van alle variabelen die in alle templates gebruikt worden**.  
- Dit betekent dat niet alleen de variabelen die bij die specifieke lead aanwezig zijn zichtbaar zijn, maar ook de variabelen die ontbreken.  
- Voorbeeld: als er 3 templates bestaan en deze gebruiken in totaal 12 unieke variabelen, dan moet in de lead-view zichtbaar zijn welke van die 12 gevuld zijn en welke niet.  
- De bestaande `vars` property blijft de bron, maar wordt uitgebreid met logica die bepaalt of de lead “compleet” is voor alle templates.  
- In de tabel kan dit weergegeven worden als een badge (bijvoorbeeld “8/12”), en in de drawer/detail-weergave als een lijst met markeringen (“✅ gevuld” of “❌ ontbreekt”).  

---

## 2. Rapporten en Afbeeldingen koppelen
Leads moeten duidelijk aangeven of er een rapport en/of afbeelding gekoppeld is.  
- **Koppeling via bulk upload (ZIP)**:  
  - Rapporten koppelen we op basis van bestandsnaam = `root_domain` of `email`.  
  - Afbeeldingen koppelen we op basis van `image_key`.  
- Tijdens upload worden bestanden automatisch gematcht. Als er geen match gevonden wordt of er meerdere opties zijn, moet dit zichtbaar gemaakt worden als “unmatched” of “ambiguous”, zodat de gebruiker dit kan corrigeren.  
- Zodra een bestand is gekoppeld, moet dit terug te zien zijn in de lead.  

**In de UI tonen we dit als indicatoren:**  
- `has_report` → bijvoorbeeld een 📄 icoon of een ✅/❌.  
- `has_image` → bijvoorbeeld een 🖼️ icoon of een ✅/❌.  
- In de drawer moet de daadwerkelijke gekoppelde afbeelding zichtbaar zijn (met fallback bij ontbreken) en de naam/status van het rapport.  

---

## 3. Dashboard Aanpassingen
De volgende wijzigingen moeten in de UI worden doorgevoerd:  
1. **Leads-tabel**:  
   - Kolom “Vars”: toon een badge met “X/Y” waarbij X = aantal gevulde variabelen en Y = totaal aantal benodigde variabelen over alle templates.  
   - Kolom “Image”: toon indicator of er een afbeelding gekoppeld is.  
   - Kolom “Report”: toon indicator of er een rapport gekoppeld is.  

2. **Lead-detail drawer**:  
   - Sectie “Variabelen”: lijst met alle variabelen die door templates worden gebruikt, met markering per variabele of deze aanwezig is of ontbreekt.  
   - Sectie “Afbeelding”: toon preview (met fallback indien ontbreekt).  
   - Sectie “Rapport”: toon status + naam of bestandsinformatie van gekoppeld rapport.  

---

## 4. Campagne Selectie
Bij het aanmaken van een campagne (wizard, stap 2 – doelgroep):  
- Er moet een extra filter toegevoegd worden: **“List”**. Dit filtert leads op het veld `list_name`.  
- Leads kunnen ook gefilterd worden op “compleetheid”: bijvoorbeeld alleen leads waarbij alle benodigde variabelen, een rapport en een afbeelding aanwezig zijn. Dit voorkomt dat onvolledige leads in een campagne terechtkomen.  

---

👉 Dit document is zo concreet mogelijk geschreven. Windsurf hoeft hier niets bij te interpreteren:  
- Ze weten exact dat het om alle templates en alle variabelen gaat.  
- Ze weten dat rapporten en afbeeldingen via ZIP bulk gekoppeld worden met bestandsnaam als sleutel.  
- Ze weten welke velden en indicatoren in de UI getoond moeten worden.  
