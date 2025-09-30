"""
Signature injection service - adds signature images to email templates based on alias.
"""
import re
from typing import Optional


def inject_signature(html: str, alias: str, signature_url_christian: str, signature_url_victor: str) -> str:
    """
    Inject signature image at the bottom of email template based on alias.
    
    Args:
        html: Email HTML template
        alias: Sender alias ("christian" or "victor")
        signature_url_christian: URL to Christian's signature image
        signature_url_victor: URL to Victor's signature image
    
    Returns:
        HTML with signature injected before closing </body> tag
    """
    # Determine which signature to use
    if alias.lower() == "victor":
        signature_url = signature_url_victor
        alt_text = "Victor Handtekening"
    else:  # Default to christian for m1/m2
        signature_url = signature_url_christian
        alt_text = "Christian Handtekening"
    
    # Create signature HTML
    signature_html = f'''
<div style="margin-top: 30px; margin-bottom: 20px;">
    <img src="{signature_url}" alt="{alt_text}" style="max-width: 300px; height: auto; display: block;" />
</div>
'''
    
    # Inject before closing </body> tag
    if '</body>' in html.lower():
        # Case-insensitive replacement
        return re.sub(
            r'</body>', 
            f'{signature_html}</body>', 
            html, 
            count=1, 
            flags=re.IGNORECASE
        )
    else:
        # No body tag, append to end
        return html + signature_html


def inject_signature_cid(html: str, alias: str) -> str:
    """
    Inject signature as CID (Content-ID) attachment reference.
    Used when signature is attached as embedded image in email.
    
    Args:
        html: Email HTML template
        alias: Sender alias ("christian" or "victor")
    
    Returns:
        HTML with signature CID reference
    """
    # Determine CID based on alias
    if alias.lower() == "victor":
        cid = "signature_victor"
        alt_text = "Victor Handtekening"
    else:
        cid = "signature_christian"
        alt_text = "Christian Handtekening"
    
    # Create signature HTML with CID reference
    signature_html = f'''
<div style="margin-top: 30px; margin-bottom: 20px;">
    <img src="cid:{cid}" alt="{alt_text}" style="max-width: 300px; height: auto; display: block;" />
</div>
'''
    
    # Inject before closing </body> tag
    if '</body>' in html.lower():
        return re.sub(
            r'</body>', 
            f'{signature_html}</body>', 
            html, 
            count=1, 
            flags=re.IGNORECASE
        )
    else:
        return html + signature_html


def get_signature_path_for_alias(alias: str) -> str:
    """
    Get file path for signature image based on alias.
    
    Args:
        alias: Sender alias ("christian" or "victor")
    
    Returns:
        Path to signature file
    """
    if alias.lower() == "victor":
        return "signatures/Victor Handtekening.png"
    else:
        return "signatures/Christian Handtekening.png"


def get_alias_from_mail_number(mail_number: int) -> str:
    """
    Determine alias based on mail number.
    
    Mail 1-2: Christian
    Mail 3-4: Victor
    
    Args:
        mail_number: Mail number (1-4)
    
    Returns:
        Alias name ("christian" or "victor")
    """
    if mail_number in [3, 4]:
        return "victor"
    else:
        return "christian"
