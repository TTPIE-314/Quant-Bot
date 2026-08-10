"""
============================================
🔧 UTILITY FUNCTIONS MODULE
============================================
"""
import logging
from pathlib import Path

def setup_logging(log_dir: Path, level: str = "INFO"):
    """Setup logging configuration"""
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "trading.log"),
            logging.StreamHandler()
        ]
    )

def format_currency(value: float) -> str:
    """Format value as currency"""
    return f"${value:,.2f}"

def format_pct(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.2f}%"
