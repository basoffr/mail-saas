-- ============================================================================
-- SUPABASE TEMPLATES SEED - MAIL DASHBOARD
-- ============================================================================
-- Project: Mail SaaS Platform
-- Total Templates: 16 (v1m1 through v4m4)
-- Usage: Run AFTER supabase_schema.sql deployment
-- Source: Extracted from backend/app/core/templates_store.py
-- ============================================================================

-- Clear existing templates (if re-running)
DELETE FROM templates;

-- ============================================================================
-- VERSION 1: punthelder-vindbaarheid.nl
-- ============================================================================

-- Template: v1m1 (Mail 1, Christian)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v1m1',
    'V1 Mail 1 - Gratis SEO-analyse',
    'Gratis SEO-analyse voor {{lead.company}}',
    'Hallo,

Ik ben Christian van Punthelder Marketing en help bedrijven zoals {{lead.company}} om beter gevonden te worden in Google.

Uw website {{lead.url}} heeft potentieel, maar er zijn waarschijnlijk nog kansen om hoger te scoren voor belangrijke zoektermen zoals "{{vars.keyword}}".

Momenteel staat u op positie {{vars.google_rank}} voor deze term. Met de juiste aanpassingen kunnen we dit flink verbeteren.

Ik bied u een gratis SEO-analyse aan waarin ik precies laat zien:
- Waar u nu staat ten opzichte van concurrenten
- Welke quick wins er mogelijk zijn
- Een concrete actieplan voor de komende maanden

{{image.cid ''dashboard''}}

Heeft u interesse in een korte kennismaking? Ik kan volgende week een analyse voor u maken.

Met vriendelijke groet,
Christian
Punthelder Marketing
christian@punthelder.nl
06-12345678',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v1m2 (Mail 2, Christian)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v1m2',
    'V1 Mail 2 - Follow-up SEO-kansen',
    'Follow-up: SEO-kansen voor {{lead.company}}',
    'Hallo,

Een paar dagen geleden stuurde ik u een mail over SEO-mogelijkheden voor {{lead.company}}.

Ik begrijp dat u het druk heeft, maar wilde u nog even attenderen op de kansen die ik zie voor uw website {{lead.url}}.

Specifiek voor de zoekterm "{{vars.keyword}}" (waar u nu op positie {{vars.google_rank}} staat) zie ik concrete verbetermogelijkheden die relatief snel resultaat kunnen opleveren.

De gratis analyse die ik aanbied geeft u inzicht in:
✓ Uw huidige SEO-score
✓ Wat uw directe concurrenten anders doen  
✓ 3-5 concrete actiepunten voor snelle resultaten

{{image.cid ''dashboard''}}

Zal ik deze week een analyse voor u maken? Het kost u niets en u bent nergens toe verplicht.

Met vriendelijke groet,
Christian
Punthelder Marketing',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v1m3 (Mail 3, Victor)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v1m3',
    'V1 Mail 3 - Laatste kans (Victor)',
    'Laatste kans: gratis SEO-analyse {{lead.company}}',
    'Hallo,

Victor hier van Punthelder Marketing. Christian heeft me gevraagd om contact met u op te nemen over de SEO-analyse voor {{lead.company}}.

Ik zie dat u nog niet heeft gereageerd op zijn aanbod voor een gratis analyse van {{lead.url}}. Dat is jammer, want er liggen echt kansen voor u.

Voor "{{vars.keyword}}" staat u nu op positie {{vars.google_rank}}. Met een paar gerichte aanpassingen kunnen we dit flink verbeteren.

{{image.cid ''dashboard''}}

Dit is mijn laatste mail hierover. Als u interesse heeft, laat het me dan deze week weten.

Anders neem ik aan dat het nu niet het juiste moment is en hoor ik graag van u als dat verandert.

Met vriendelijke groet,
Victor
Punthelder Marketing
victor@punthelder.nl',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v1m4 (Mail 4, Victor)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v1m4',
    'V1 Mail 4 - Afscheid (Victor)',
    'Afscheid van {{lead.company}} - Victor',
    'Hallo,

Victor hier. Dit is mijn laatste mail over de SEO-mogelijkheden voor {{lead.company}}.

Ik respecteer dat u op dit moment geen interesse heeft in een SEO-analyse voor {{lead.url}}.

Mocht u in de toekomst toch willen weten hoe u beter kunt scoren voor termen zoals "{{vars.keyword}}", dan kunt u altijd contact opnemen.

{{image.cid ''dashboard''}}

Ik wens u veel succes met uw bedrijf.

Met vriendelijke groet,
Victor
Punthelder Marketing',
    '["lead.company", "lead.url", "vars.keyword", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- ============================================================================
-- VERSION 2: punthelder-marketing.nl
-- ============================================================================

-- Template: v2m1 (Mail 1, Christian)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v2m1',
    'V2 Mail 1 - Vindbaarheid verbeteren',
    'Vindbaarheid verbeteren voor {{lead.company}}?',
    'Hallo,

Christian van Punthelder Vindbaarheid. Ik help bedrijven zoals {{lead.company}} om beter vindbaar te worden online.

Uw website {{lead.url}} heeft potentieel, maar ik zie kansen om de vindbaarheid te verbeteren voor belangrijke zoektermen zoals "{{vars.keyword}}".

Momenteel staat u op positie {{vars.google_rank}} voor deze term. Er is ruimte voor verbetering.

Ik bied u een gratis vindbaarheidsanalyse aan:
- Huidige positie vs concurrenten
- Concrete verbeterpunten
- Stappenplan voor betere vindbaarheid

{{image.cid ''dashboard''}}

Interesse in een gratis analyse? Ik kan deze week voor u aan de slag.

Met vriendelijke groet,
Christian
Punthelder Vindbaarheid',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v2m2 (Mail 2, Christian)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v2m2',
    'V2 Mail 2 - Nog steeds interesse',
    'Nog steeds interesse in betere vindbaarheid?',
    'Hallo,

Christian hier van Punthelder Vindbaarheid. Ik stuurde u eerder een mail over vindbaarheid voor {{lead.company}}.

Voor {{lead.url}} zie ik nog steeds concrete kansen, vooral voor "{{vars.keyword}}" waar u nu op positie {{vars.google_rank}} staat.

De gratis analyse die ik aanbied laat precies zien:
✓ Waar u nu staat
✓ Wat er beter kan
✓ Hoe u meer bezoekers kunt krijgen

{{image.cid ''dashboard''}}

Zal ik deze week een analyse maken? Het is gratis en vrijblijvend.

Met vriendelijke groet,
Christian',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v2m3 (Mail 3, Victor)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v2m3',
    'V2 Mail 3 - Laatste kans (Victor)',
    'Victor hier - laatste kans vindbaarheidsanalyse',
    'Hallo,

Victor van Punthelder Vindbaarheid. Christian vroeg me contact met u op te nemen over {{lead.company}}.

U heeft nog niet gereageerd op het aanbod voor een gratis vindbaarheidsanalyse van {{lead.url}}.

Voor "{{vars.keyword}}" staat u op positie {{vars.google_rank}}. Dat kan echt beter.

{{image.cid ''dashboard''}}

Dit is mijn laatste mail hierover. Interesse? Laat het me deze week weten.

Met vriendelijke groet,
Victor',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v2m4 (Mail 4, Victor)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v2m4',
    'V2 Mail 4 - Afscheid (Victor)',
    'Afscheid - Victor van Punthelder Vindbaarheid',
    'Hallo,

Victor hier. Laatste mail over vindbaarheid voor {{lead.company}}.

Ik begrijp dat u nu geen interesse heeft in verbetering van {{lead.url}}.

Mocht dat in de toekomst veranderen, vooral voor termen zoals "{{vars.keyword}}", dan hoor ik graag van u.

{{image.cid ''dashboard''}}

Succes gewenst!

Victor
Punthelder Vindbaarheid',
    '["lead.company", "lead.url", "vars.keyword", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- ============================================================================
-- VERSION 3: punthelder-seo.nl
-- ============================================================================

-- Template: v3m1 (Mail 1, Christian)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v3m1',
    'V3 Mail 1 - SEO-audit gratis',
    'SEO-audit voor {{lead.company}} - gratis',
    'Hallo,

Christian van Punthelder SEO. Ik help bedrijven zoals {{lead.company}} met zoekmachine-optimalisatie.

Uw website {{lead.url}} kan waarschijnlijk beter presteren in Google, vooral voor zoektermen zoals "{{vars.keyword}}".

U staat nu op positie {{vars.google_rank}} voor deze term. Met de juiste SEO-aanpak kunnen we dit verbeteren.

Ik bied u een gratis SEO-audit aan:
- Technische SEO-analyse
- Content optimalisatie tips
- Linkbuilding mogelijkheden

{{image.cid ''dashboard''}}

Interesse? Ik kan deze week een audit voor u uitvoeren.

Met vriendelijke groet,
Christian
Punthelder SEO',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v3m2 (Mail 2, Christian)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v3m2',
    'V3 Mail 2 - Follow-up SEO-audit',
    'Follow-up SEO-audit {{lead.company}}',
    'Hallo,

Christian van Punthelder SEO. Ik stuurde u eerder een mail over een gratis SEO-audit voor {{lead.company}}.

Voor {{lead.url}} zie ik nog steeds SEO-kansen, vooral voor "{{vars.keyword}}" (positie {{vars.google_rank}}).

De gratis audit bevat:
✓ Technische SEO-check
✓ Content analyse
✓ Concurrentie vergelijking

{{image.cid ''dashboard''}}

Zal ik deze week een audit maken? Volledig gratis.

Met vriendelijke groet,
Christian',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v3m3 (Mail 3, Victor)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v3m3',
    'V3 Mail 3 - Laatste kans (Victor)',
    'Victor - laatste kans SEO-audit',
    'Hallo,

Victor van Punthelder SEO. Christian vroeg me u te benaderen over {{lead.company}}.

U heeft nog niet gereageerd op de gratis SEO-audit voor {{lead.url}}.

Voor "{{vars.keyword}}" staat u op positie {{vars.google_rank}}. Daar valt winst te behalen.

{{image.cid ''dashboard''}}

Laatste kans voor de gratis audit. Interesse? Laat het me weten.

Met vriendelijke groet,
Victor',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v3m4 (Mail 4, Victor)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v3m4',
    'V3 Mail 4 - Afscheid (Victor)',
    'Afscheid SEO-audit - Victor',
    'Hallo,

Victor hier. Laatste mail over SEO voor {{lead.company}}.

Ik respecteer dat u geen interesse heeft in SEO-verbetering voor {{lead.url}}.

Mocht u later toch willen weten hoe u beter kunt scoren voor "{{vars.keyword}}", dan kunt u contact opnemen.

{{image.cid ''dashboard''}}

Veel succes!

Victor
Punthelder SEO',
    '["lead.company", "lead.url", "vars.keyword", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- ============================================================================
-- VERSION 4: punthelder-zoekmachine.nl
-- ============================================================================

-- Template: v4m1 (Mail 1, Christian)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v4m1',
    'V4 Mail 1 - Zoekmachine optimalisatie',
    'Zoekmachine optimalisatie voor {{lead.company}}',
    'Hallo,

Christian van Punthelder Zoekmachine. Ik help bedrijven zoals {{lead.company}} om beter gevonden te worden.

Uw website {{lead.url}} heeft potentieel, maar ik zie kansen voor zoekmachine optimalisatie, vooral voor "{{vars.keyword}}".

Momenteel staat u op positie {{vars.google_rank}} voor deze term. Er is ruimte voor verbetering.

Ik bied u een gratis zoekmachine-analyse aan:
- Huidige positie analyse
- Optimalisatie mogelijkheden  
- Concrete actieplan

{{image.cid ''dashboard''}}

Interesse in een gratis analyse? Ik kan deze week voor u aan de slag.

Met vriendelijke groet,
Christian
Punthelder Zoekmachine',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v4m2 (Mail 2, Christian)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v4m2',
    'V4 Mail 2 - Follow-up optimalisatie',
    'Follow-up zoekmachine optimalisatie',
    'Hallo,

Christian hier van Punthelder Zoekmachine. Ik stuurde u eerder een mail over optimalisatie voor {{lead.company}}.

Voor {{lead.url}} zie ik nog steeds concrete kansen, vooral voor "{{vars.keyword}}" waar u nu op positie {{vars.google_rank}} staat.

De gratis analyse laat zien:
✓ Waar u nu staat
✓ Wat er beter kan
✓ Hoe u meer bezoekers krijgt

{{image.cid ''dashboard''}}

Zal ik deze week een analyse maken? Het is gratis en vrijblijvend.

Met vriendelijke groet,
Christian',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v4m3 (Mail 3, Victor)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v4m3',
    'V4 Mail 3 - Laatste kans (Victor)',
    'Victor - laatste kans zoekmachine analyse',
    'Hallo,

Victor van Punthelder Zoekmachine. Christian vroeg me contact met u op te nemen over {{lead.company}}.

U heeft nog niet gereageerd op het aanbod voor een gratis zoekmachine-analyse van {{lead.url}}.

Voor "{{vars.keyword}}" staat u op positie {{vars.google_rank}}. Dat kan echt beter.

{{image.cid ''dashboard''}}

Dit is mijn laatste mail hierover. Interesse? Laat het me deze week weten.

Met vriendelijke groet,
Victor',
    '["lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- Template: v4m4 (Mail 4, Victor)
INSERT INTO templates (id, name, subject_template, body_template, required_vars, assets, updated_at)
VALUES (
    'v4m4',
    'V4 Mail 4 - Afscheid (Victor)',
    'Afscheid - Victor van Punthelder Zoekmachine',
    'Hallo,

Victor hier. Laatste mail over zoekmachine optimalisatie voor {{lead.company}}.

Ik begrijp dat u nu geen interesse heeft in verbetering van {{lead.url}}.

Mocht dat in de toekomst veranderen, vooral voor termen zoals "{{vars.keyword}}", dan hoor ik graag van u.

{{image.cid ''dashboard''}}

Succes gewenst!

Victor
Punthelder Zoekmachine',
    '["lead.company", "lead.url", "vars.keyword", "image.cid"]'::jsonb,
    '{"dashboard": true}'::jsonb,
    NOW()
);

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================

-- Verify all 16 templates are inserted
SELECT 
    id,
    name,
    SUBSTRING(subject_template, 1, 50) as subject_preview,
    array_length(required_vars, 1) as var_count,
    updated_at
FROM templates
ORDER BY id;

-- ============================================================================
-- SEED COMPLETE
-- ============================================================================
-- Total templates seeded: 16
-- Version 1 (vindbaarheid): v1m1, v1m2, v1m3, v1m4
-- Version 2 (marketing): v2m1, v2m2, v2m3, v2m4
-- Version 3 (seo): v3m1, v3m2, v3m3, v3m4
-- Version 4 (zoekmachine): v4m1, v4m2, v4m3, v4m4
-- ============================================================================
