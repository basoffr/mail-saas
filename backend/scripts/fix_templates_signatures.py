"""
Script to remove all text between "Met vriendelijke groet," and end of template.
Only keep "Met vriendelijke groet," - the signature image will be injected by signature_injector.py
"""
import re

def fix_template_body(body: str) -> str:
    """Remove everything after 'Met vriendelijke groet,' including name, company, email."""
    # Find "Met vriendelijke groet," and keep only that line
    # Remove everything after it
    pattern = r'(Met vriendelijke groet,).*'
    replacement = r'\1'
    
    # Use DOTALL flag to match newlines
    fixed = re.sub(pattern, replacement, body, flags=re.DOTALL)
    
    return fixed

# Read the templates_store.py file
file_path = r"c:\Users\basof\OneDrive\Documenten\Punthelder\Mail dashboard\backend\app\core\templates_store.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all template bodies between body="""..."""
# This is complex because of nested quotes, so let's use a different approach
# Replace each template body section

# Pattern to find template body definitions
pattern = r'(body="""[^"]*?)(Met vriendelijke groet,)([^"]*?)(""")'

def replacer(match):
    prefix = match.group(1)  # Everything before "Met vriendelijke groet,"
    groet = match.group(2)   # "Met vriendelijke groet,"
    after = match.group(3)   # Everything after (to remove)
    suffix = match.group(4)  # Closing """
    
    # Return without the text after "Met vriendelijke groet,"
    return f'{prefix}{groet}{suffix}'

fixed_content = re.sub(pattern, replacer, content, flags=re.DOTALL)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Templates fixed! All text after 'Met vriendelijke groet,' removed.")
print("Signature images will be injected automatically by signature_injector.py")
