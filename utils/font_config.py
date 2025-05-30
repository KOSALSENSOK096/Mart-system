import os
import platform
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

def get_system_fonts() -> Dict[str, str]:
    """Get system-specific font mappings"""
    system = platform.system()
    
    if system == "Windows":
        return {
            'display': 'Segoe UI',
            'text': 'Segoe UI',
            'emoji': 'Segoe UI Emoji'
        }
    elif system == "Darwin":  # macOS
        return {
            'display': 'SF Pro Display',
            'text': 'SF Pro Text',
            'emoji': 'Apple Color Emoji'
        }
    else:  # Linux and others
        return {
            'display': 'Ubuntu',
            'text': 'Ubuntu',
            'emoji': 'Noto Color Emoji'
        }

def configure_fonts() -> None:
    """Configure font settings for the application"""
    try:
        # Get system-specific fonts
        fonts = get_system_fonts()
        
        # Update font configurations
        from utils.styles import FONTS
        
        font_mapping = {
            'heading1': (fonts['display'], 28, 'bold'),
            'heading2': (fonts['display'], 24, 'bold'),
            'heading3': (fonts['display'], 20, 'bold'),
            'body_bold': (fonts['text'], 14, 'bold'),
            'body': (fonts['text'], 14, 'normal'),
            'small': (fonts['text'], 12, 'normal'),
            'tiny': (fonts['text'], 10, 'normal')
        }
        
        # Update font configurations
        for key, value in font_mapping.items():
            FONTS[key] = value
            
        logger.info("Font configuration completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to configure fonts: {e}")
        # Fall back to system default fonts
        fallback_font = "TkDefaultFont"
        
        font_mapping = {
            'heading1': (fallback_font, 28, 'bold'),
            'heading2': (fallback_font, 24, 'bold'),
            'heading3': (fallback_font, 20, 'bold'),
            'body_bold': (fallback_font, 14, 'bold'),
            'body': (fallback_font, 14, 'normal'),
            'small': (fallback_font, 12, 'normal'),
            'tiny': (fallback_font, 10, 'normal')
        }
        
        # Update font configurations with fallback
        from utils.styles import FONTS
        for key, value in font_mapping.items():
            FONTS[key] = value 