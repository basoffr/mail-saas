Lovable-prompt 1 (alleen voor Leads) 



Plak dit in Lovable om het tabblad Leads te laten genereren:



Context



Bouw een React (TypeScript) frontend met Tailwind + shadcn/ui componenten. Gebruik Recharts voor grafieken (hier niet nodig), en een eenvoudige service-laag voor API calls.



Routes: /leads, /leads/import.



Gebruik nette, moderne UI: cards met rounded-2xl, zachte schaduw, voldoende padding, grid layouts, loading skeletons, toasts.



Tijdzone: Europe/Amsterdam voor alle datum/tijd rendering.



Focus van deze opdracht



Implementeer het volledige Leads tabblad: Lijst (table), Detail (drawer), Import wizard (3 stappen), bulk selectie en handover naar Campagnes, Test render modal, JSON viewer, image preview met fallback.



API (mock in service-laag met identieke shapes)



GET /leads (met query params volgens LeadsQuery) → { items: Lead\[], total }



GET /leads/:id → Lead



POST /import/leads (file) → { inserted, updated, skipped, jobId }



GET /assets/image-by-key?key=... → URL (mag fake)



GET /templates → { items: \[{id,name}] }



GET /templates/{id}/preview?lead\_id=... → { html, text, warnings?: string\[] }



Belangrijke UI-eisen



Table met kolommen: Email, Bedrijfsnaam, Domein/URL, Tags, Status, Laatst gemaild, Laatste open, Image key, Vars (badge met count).



Zoek (email/bedrijf/domein), Filters (TLD, status multi, tags, hasImage, hasVar), Sort, Paginate.



Bulk select met actie: “Aan campagne toevoegen” → navigeer naar /campaigns/new?source=leads\&ids=<comma-separated> of gebruik shared state.



Drawer met kernvelden, image preview (via imageKey; fallback), JSON viewer voor vars, knoppen Test render, Open website.



Import wizard:



Stap 1 (Upload): dropzone .xlsx/.csv, max 20MB, validaties.



Stap 2 (Mapping): dropdown per kolom → velden (email verplicht), Preview 20 rijen post-mapping. Duplicates gemarkeerd.



Stap 3 (Bevestigen/Run): samenvatting, Start import → progress view met job-status; toasts; errorlijst (download CSV).



Toasts, loading skeletons, empty states, error states.



A11y: focus-states, aria-labels, keyboard nav.



Types



Gebruik de Lead, LeadStatus, LeadsQuery definities zoals hieronder (copy/paste) en breid aan waar nodig.



Bouw een json-viewer component (read-only) en een ImagePreview component met fallback.



Voeg een useImportJobPolling(jobId) hook toe die mocked progress events emit.



Acceptance criteria



Alles uit “Belangrijke UI-eisen” en “Acceptatiecriteria (MVP)” hierboven functioneert.



Code opgesplitst in: pages/leads/, components/leads/, services/leads.ts, services/templates.ts, hooks/.



Geen backend nodig om te runnen: services kunnen met fixtures werken; wissel naar echte endpoints via env flag.


---------------------------------------------------------------------------------------------------------------------------



Lovable-prompt 2 (specifiek voor Campagnes)



Plak dit in Lovable om het tabblad Campagnes te laten genereren:



Context



Bouw React (TypeScript) met Tailwind + shadcn/ui. Gebruik Recharts voor grafiek(en).



Routes: /campaigns, /campaigns/new, /campaigns/:id. Tijdzone: Europe/Amsterdam.



Stijl: cards rounded-2xl, zachte schaduw, duidelijke grids, loading skeletons, toasts, confirms.



Focus



Implementeer: Overzicht, 4-staps Wizard (Basis → Doelgroep → Verzendregels → Review \& Start), Campagne-detail met KPI’s, grafiek “verzonden per dag”, berichtenlog, follow-up panel, en handover vanaf Leads via ?source=leads\&ids=.



API (mock service-laag met identieke shapes)



GET /campaigns → { items: Campaign\[], total }



POST /campaigns (CampaignCreatePayload) → { id }



GET /campaigns/:id → CampaignDetail



POST /campaigns/:id/pause / resume / stop → { ok: true }



(Optioneel) POST /campaigns/:id/dry-run → { byDay: {date, planned}\[] }



Gebruik LeadsQuery uit het Leads-tabblad voor filter-UI hergebruik.



UI-eisen



Overzicht: tafel met Naam, Status, Template, Doelgroep (#), Verzonden, Opens, Startdatum; acties Bekijken/Pauzeren|Hervatten/Stoppen/Dupliceren.



Wizard:



Stap 1: Naam, Template (dropdown), Startmoment (nu/gepland datetime), Follow-up (toggle + days + “bijlage indien beschikbaar”).



Stap 2: Keuze Filter (filtercomponent van Leads, live preview count) of Statische selectie (support ?source=leads\&ids= en eigen selector modal). Dedupe: suppress/bounced (toggle), contacted last N days (default 14), one-per-domain (toggle).



Stap 3: Domeinen (checkbox list), Throttle \& Venster als read-only badges, Retry policy read-only.



Stap 4: Review + Warnings (var-gaps, ontbrekende afbeeldingen), knoppen Dry-run en Start.



Detail: header-acties (pauze/resume/stop), KPI-tegels, grafiek “verzonden per dag” (Recharts), tabel “Berichten” met Resend (alleen bij failed) en “Bekijk render”, Follow-up panel met counts.



Belangrijke UX



Validatie per stap met disabled Volgende/Start bij fouten.



Confirms: stop \& resend. Toasts bij alle mutaties.



Polling van detaildata (mocked) met exponential backoff.



Alle tijden renderen in Europe/Amsterdam; labels “ma–vr 08:00–17:00”.



Types



Gebruik de Campaign, CampaignCreatePayload, CampaignMessage, CampaignDetail, CampaignStatus, MessageStatus definities zoals hierboven.



Structuur



Code in pages/campaigns/, components/campaigns/, services/campaigns.ts, hooks/.



Re-use filter UI uit Leads.



Fixtures + env-flag om te schakelen naar echte endpoints later.



Acceptance



Voldoet aan de UI-eisen + Acceptatiecriteria (MVP) hierboven.



-------------------------------------------------------------------------------------------------------------------------------------



Lovable-prompt 3 (specifiek voor Templates)



Plak dit in Lovable om het tabblad Templates te genereren:



Context



Bouw React (TypeScript) met Tailwind + shadcn/ui.



Routes: /templates, /templates/:id.



Tijdzone: Europe/Amsterdam.



Stijl: cards met rounded-2xl, zachte schaduw, grid layout, loading skeletons, toasts, modals/drawers, tabs.



Template content is read-only in MVP, maar volledig zichtbaar.



Focus



Implementeer Templates: Lijst, Detail (view-only), Preview (HTML \& plaintext), Variabelen-schema, Testsends, en Afbeeldingen-overzicht (CID vs statisch) + warnings.



API (mock service-laag met identieke shapes)



GET /templates → { items: Template\[], total? }



GET /templates/:id → Template



GET /templates/:id/preview?lead\_id=... → { html, text, warnings?: string\[] }



POST /templates/:id/testsend { to, leadId? } → { ok: true }



Types



Gebruik deze definities en breid aan waar zinvol:



interface Template { id:string; name:string; subject:string; bodyHtml:string; updatedAt:string; assets?:Array<{key:string; type:'static'|'cid'}>; }

interface TemplateVarItem { key:string; required:boolean; source:'lead'|'vars'|'campaign'|'image'; example?:string; }

interface TemplatePreviewResponse { html:string; text:string; warnings?:string\[]; }

interface TestsendPayload { to:string; leadId?:string|null; }





UI-eisen



Lijst: Naam, Onderwerp, Laatst gewijzigd, Acties Preview / Variabelen / Testsend / Bekijken; zoek (naam/onderwerp), sort (Laatst gewijzigd).



Detail (view-only): Subject + Body viewer met variabel-highlight; Helper-hints (default/upper/lower/if); Afbeeldingen-blok met CID (per-lead) \& statisch; Preview-pane met test lead selector, Render, tabs HTML/Plain, Warnings.



Preview modal (quick): test lead select, HTML/Plain, warnings; link “Open in detail”.



Variabelen modal: tabel (Key, Bron, Required, Voorbeeld) + zoek/filter.



Testsend modal: “Naar e-mail” (required), “Test lead” (optional) → Versturen, toasts.



Gedrag \& validatie



Render zonder test lead mag, maar toon warnings als variabelen niet resolven.



{{image.cid 'hero'}}: gebruik placeholder 1×1 bij ontbreken + warning.



Email-validatie in Testsends; loading/disabled states; toasts bij success/error.



Cache laatste preview per (templateId, leadId).



Structuur



Code in pages/templates/, components/templates/, services/templates.ts.



Reusable: JsonViewer, HtmlViewer, PreviewModal, VarsModal, TestsendModal, ImageSlotsCard.



Fixtures + env-flag om later naar echte endpoints te schakelen.



Acceptance



Alles werkt conform “UI-eisen” en “Acceptatiecriteria (MVP)” hierboven.



-----------------------------------------------------------------------------------------------------------------------------------



Lovable-prompt 4 (specifiek voor Rapporten)



Plak dit in Lovable om het tabblad Rapporten te genereren:



Context



Bouw React (TypeScript) met Tailwind + shadcn/ui.



Routes: /reports, /reports/upload, /reports/bulk.



Stijl: moderne cards (rounded-2xl), duidelijke grids, loading skeletons, toasts, modals.



Focus



Implementeer Rapporten: Overzicht (filters + acties), Single upload met optionele binding aan lead/campagne, en Bulk ZIP met twee modes (by\_image\_key / by\_email) inclusief mapping preview en resultaatrapport.



API (mock service-laag met identieke shapes)



GET /reports (ReportsQuery) → { items: ReportItem\[], total }



POST /reports/upload (file + optional { lead\_id|campaign\_id }) → ReportItem



POST /reports/bulk?mode=by\_image\_key|by\_email (zip) → BulkUploadResult



POST /reports/bind { report\_id, lead\_id|campaign\_id } → { ok:true }



POST /reports/unbind { report\_id } → { ok:true }



GET /reports/:id/download → URL/binary



Types



type ReportFileType = 'pdf'|'xlsx'|'png'|'jpg'|'jpeg';

interface ReportItem { id:string; filename:string; type:ReportFileType; sizeBytes:number; uploadedAt:string; boundTo?:{kind:'lead'|'campaign'; id:string; label?:string}|null; storagePath?:string; checksum?:string; meta?:Record<string,unknown>; }

interface ReportsQuery { page:number; pageSize:number; types?:ReportFileType\[]; boundFilter?:'all'|'bound'|'unbound'; boundKind?:'lead'|'campaign'; boundId?:string; search?:string; dateFrom?:string; dateTo?:string; }

interface BulkMapRow { fileName:string; baseKey:string; target?:{kind:'lead'|'image\_key'|'campaign'; id?:string; email?:string}; status:'matched'|'unmatched'|'ambiguous'; reason?:string; }

interface BulkUploadResult { total:number; uploaded:number; failed:number; mappings:Array<{ fileName:string; to?:{kind:'lead'|'image\_key'|'campaign'; id?:string}; status:'ok'|'failed'; error?:string }>; }





UI-eisen



Overzicht: filters (type, bound/unbound, kind, zoek, datum), tabel met Bestandsnaam/Type/Grootte/Gekoppeld aan/Upload-datum/Acties; rij-acties Bekijken, Download, Koppelen/ontkoppelen; top-action Upload (Single/Bulk).



Single upload: dropzone (pdf/xlsx/png/jpg/jpeg, max 10MB), Koppelen aan (Lead | Campagne | Geen), selector met autocomplete; Uploaden + toasts.



Bulk ZIP: stap 1 (upload .zip, max 100MB, kies mode), stap 2 (mapping preview met counters en status per file, handmatige fix voor ambiguous), stap 3 (Bevestigen \& Uploaden met progress en BulkUploadResult + Download rapport CSV).



Viewer: img lightbox; pdf iframe fallback; xlsx alleen download.



Gedrag \& validatie



Client valideert type/size; toont duidelijke errors.



Bestandsnaam-matching is case-insensitive, extensie wordt gestript.



Ambiguous gevallen tonen keuze-UI of waarschuwing; unmatched worden niet geüpload in stap 3.



Toons toasts en loading/disabled states bij elke mutatie.



Structuur



Code in pages/reports/, components/reports/, services/reports.ts.



Reusable: FileDropzone, BindModal, BulkMappingTable, ResultReport, PdfViewer, ImageLightbox.



Fixtures + env-flag om later echte endpoints te gebruiken.



Acceptance



Voldoet aan alle UI-eisen + Acceptatiecriteria (MVP) hierboven.



---------------------------------------------------------------------------------------------------------------------------------



Lovable-prompt 5 (specifiek voor Statistieken)



Plak dit in Lovable om het tabblad Statistieken te genereren:



Context



Bouw React (TypeScript) met Tailwind + shadcn/ui. Gebruik Recharts voor grafieken.



Route: /stats. Tijdzone: Europe/Amsterdam.



Stijl: KPI-cards, grafieken, tabellen, exportknoppen.



Focus



Implementeer Statistieken:



Globale KPI’s (totalSent, openRate, bounces).



Grafieken: “Verstuurd per dag” en “Opens per dag”.



Tabel per domein (domain, sent, openRate, bounces).



Tabel per campagne (id, name, sent, openRate, bounces) met link naar /campaigns/:id.



Export CSV knoppen.



API (mock service-laag)



GET /stats/summary → StatsSummary



GET /stats/export?scope=... → CSV



Types



interface GlobalStats { totalSent:number; openRate:number; bounces:number; }

interface DomainStats { domain:string; sent:number; openRate:number; bounces:number; }

interface CampaignStats { id:string; name:string; sent:number; openRate:number; bounces:number; }

interface TimelinePoint { date:string; sent:number; opens:number; }

interface StatsSummary { global:GlobalStats; domains:DomainStats\[]; campaigns:CampaignStats\[]; timeline:TimelinePoint\[]; }





UI-eisen



Globaal: 3 KPI-cards + 2 grafieken (verstuurd per dag, opens per dag).



Per domein: tabel, sorteerbaar, filterbaar.



Per campagne: tabel, sorteerbaar, zoek op naam; naam klikbaar.



Export: CSV downloadknop bovenaan; optioneel per rij.



States: loading skeletons, empty, error.



Structuur



Code in pages/stats/, components/stats/, services/stats.ts.



Reusable: KpiCard, TimelineChart, DomainTable, CampaignTable.



Fixtures + env-flag voor echte endpoints later.



Acceptance



Alles functioneert conform UI-eisen en Acceptatiecriteria (MVP).



---------------------------------------------------------------------------------------------------------------------------------



Lovable-prompt 6 (specifiek voor Instellingen)



Plak dit in Lovable om het tabblad Instellingen te genereren:



Context



Bouw React (TypeScript) met Tailwind + shadcn/ui.



Route: /settings. Tijdzone: Europe/Amsterdam.



Stijl: cards (rounded-2xl), badges, toggles, duidelijke secties.



Focus



Implementeer Instellingen met 2 secties:



Verzendinstellingen: timezone (read-only), verzendvenster (read-only), throttle (read-only), domeinen (read-only lijst), unsubscribe-tekst (bewerkbaar), unsubscribe-URL (read-only, kopieerbaar), tracking pixel toggle (bewerkbaar).



E-mail infrastructuur: huidig kanaal (badge), toekomstige providers (disabled toggle), DNS-checklist (SPF/DKIM/DMARC badges).



API (mock service-laag)



GET /settings → Settings



POST /settings (partial update) → { ok:true }



Types



interface Settings {

&nbsp; timezone:string;

&nbsp; window:{days:string\[]; from:string; to:string};

&nbsp; throttle:{emailsPer:number; minutes:number};

&nbsp; domains:string\[];

&nbsp; unsubscribeText:string;

&nbsp; unsubscribeUrl:string;

&nbsp; trackingPixelEnabled:boolean;

&nbsp; emailInfra:{ current:'SMTP'; provider:'Postmark'|'SES'|null; providerEnabled:boolean; dns:{spf:boolean;dkim:boolean;dmarc:boolean}; };

}





UI-eisen



Verzendinstellingen card: badges voor read-only velden; editable input voor unsubscribe-tekst; read-only URL met copy button; toggle voor tracking pixel; save knop (disabled tot wijziging); toasts bij save.



E-mail infrastructuur card: badges voor huidig kanaal; disabled toggles voor toekomstige providers met tooltip; DNS-checklist badges (OK/NOK).



Loading skeletons, empty/error states.



Structuur



Code in pages/settings/, components/settings/, services/settings.ts.



Reusable: Badge, CopyField, DnsChecklist, SettingsCard.



Fixtures + env-flag voor backend switch.



Acceptance



