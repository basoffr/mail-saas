from pathlib import Path
from typing import Optional, Dict
from loguru import logger


class AssetResolver:
    """
    Resolves assets based on domain and type.
    Implements per-domain fixed filename convention from implementation plan.
    """
    
    # Domain to root-key mapping (hard-coded as per plan)
    DOMAIN_MAPPING = {
        "punthelder-marketing.nl": "running_nl",
        "punthelder-vindbaarheid.nl": "cycle_nl",
        # Add more domains as needed
    }
    
    def __init__(self, assets_dir: str = "assets"):
        self.assets_dir = Path(assets_dir)
    
    def get_report_path(self, domain: str) -> Optional[Path]:
        """Get report path for domain. Returns None if not found."""
        root_key = self.DOMAIN_MAPPING.get(domain)
        if not root_key:
            logger.warning(f"No root key mapping for domain: {domain}")
            return None
        
        report_path = self.assets_dir / f"{root_key}_report.pdf"
        if report_path.exists():
            return report_path
        
        logger.debug(f"Report not found: {report_path}")
        return None
    
    def get_dashboard_image_path(self, domain: str) -> Optional[Path]:
        """Get dashboard image path for domain. Returns None if not found."""
        root_key = self.DOMAIN_MAPPING.get(domain)
        if not root_key:
            logger.warning(f"No root key mapping for domain: {domain}")
            return None
        
        image_path = self.assets_dir / f"{root_key}_picture.png"
        if image_path.exists():
            return image_path
        
        logger.debug(f"Dashboard image not found: {image_path}")
        return None
    
    def get_signature_path(self, alias: str) -> Optional[Path]:
        """Get signature path for alias (christian/victor)."""
        if alias.lower() not in ["christian", "victor"]:
            logger.warning(f"Unknown alias for signature: {alias}")
            return None
        
        signature_path = self.assets_dir / "signatures" / f"{alias.lower()}.png"
        if signature_path.exists():
            return signature_path
        
        logger.warning(f"Signature not found: {signature_path}")
        return None
    
    def has_report(self, domain: str) -> bool:
        """Check if report exists for domain."""
        return self.get_report_path(domain) is not None
    
    def has_dashboard_image(self, domain: str) -> bool:
        """Check if dashboard image exists for domain."""
        return self.get_dashboard_image_path(domain) is not None


# Global instance
asset_resolver = AssetResolver()
