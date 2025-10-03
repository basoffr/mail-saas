# ⚙️ Prompt voor Windsurf – Implementatieplan opstellen

Gebruik de resultaten uit `HUIDIGE_STAND_ANALYSE.md` (root) en de vereisten uit `checklist_windsurf.md` (root).  

## 🎯 Opdracht
Stel een **concreet implementatieplan** op waarmee de ontbrekende onderdelen uit de analyse worden toegevoegd aan het project.  

### Scope van dit plan:
1. **Variabelen per lead**
   - Service bouwen die alle unieke variabelen uit alle templates aggregeert.  
   - “X/Y compleetheid badge” in leads tabel.  
   - Detail drawer: lijst met alle template variabelen + status (✅/❌).  

2. **Rapporten**
   - `has_report` indicator toevoegen aan lead model.  
   - Rapport-kolom in leads tabel.  
   - Rapport-sectie in lead drawer (naam, status, fallback bij ontbreken).  
   - Bulk upload: unmatched/ambiguous feedback tonen in UI.  
   - Optioneel: root_domain matching toevoegen als extra bulk mode.  

3. **Afbeeldingen**
   - `has_image` indicator toevoegen aan lead model.  
   - Image-kolom in leads tabel.  
   - Image-sectie in lead drawer (preview met fallback).  
   - Bulk upload: feedback unmatched/ambiguous.  

4. **Campagne selectie**
   - `list_name` veld toevoegen aan lead model + API + import flow.  
   - “List” filter toevoegen in campagne wizard.  
   - “Complete leads only” filter toevoegen (alle vars + rapport + image aanwezig).  

### 🎨 Output
- Lever een **.md bestand** op met een **stapsgewijs implementatieplan**:  
  - Backend aanpassingen (models, services, API).  
  - Frontend aanpassingen (tabelkolommen, drawer-secties, filters, indicators).  
  - Database migraties (nieuwe velden, relaties).  
  - Testing & validatie (hoe dek je dit af).  
  - Prioriteiten + fasering (wat eerst, wat kan later).  

⚠️ Belangrijk: werk **concreet en volledig**, zodat er geen ruimte is voor eigen interpretatie.  
