-- Make campaigns.template_id nullable
-- Templates are handled at message level, not campaign level

-- Drop foreign key constraint
ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS fk_campaigns_template;

-- Make template_id nullable
ALTER TABLE campaigns ALTER COLUMN template_id DROP NOT NULL;

-- Re-add foreign key constraint but allow NULL
ALTER TABLE campaigns ADD CONSTRAINT fk_campaigns_template 
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE RESTRICT;

-- Verify the change
SELECT column_name, is_nullable, data_type 
FROM information_schema.columns 
WHERE table_name = 'campaigns' AND column_name = 'template_id';
