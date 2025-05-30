import customtkinter as ctk
import logging
from typing import Tuple, Optional
import time

logger = logging.getLogger(__name__)

"""
Modern and sleek styling configurations for the Mart Application.
Emphasizes cool colors and clean design elements.
"""

# Color Palette - Modern Dark Theme
COLORS = {
    # Main Colors
    'primary': '#3B82F6',      # Bright Blue
    'primary_light': '#60A5FA',
    'primary_dark': '#2563EB',
    'primary_hover': '#1D4ED8',  # Darker blue for hover
    'accent': '#7C3AED',        # Purple accent
    'accent_hover': '#6D28D9',  # Darker purple for hover
    'accent_dark': '#5B21B6',   # Even darker purple
    
    # Background Colors
    'background': '#1A1A1A',    # Dark background
    'surface': '#2D2D2D',      # Slightly lighter background
    'card': '#333333',         # Card background
    'hover': '#404040',        # Hover state
    
    # Text Colors
    'text': '#FFFFFF',         # White text
    'text_secondary': '#B3B3B3',
    'text_disabled': '#6B7280',
    'placeholder': '#808080',   # Placeholder text
    
    # Status Colors
    'success': '#34C759',      # Success green
    'warning': '#FF9500',      # Warning orange
    'error': '#FF3B30',        # Error red
    'info': '#3B82F6',         # Blue
    
    # Input and Border Colors
    'input_bg': '#2D2D2D',     # Input background
    'input_border': '#404040',
    'input_border_focus': '#3B82F6',
    'separator': '#404040',
    
    # Overlay Colors
    'overlay': 'rgba(0, 0, 0, 0.5)',
    'modal_bg': '#1E1E2E',
}

# Font Configurations - Using system fonts for better compatibility
FONTS = {
    'heading1': ('SF Pro Display', 28, 'bold'),
    'heading2': ('SF Pro Display', 24, 'bold'),
    'heading3': ('SF Pro Display', 20, 'bold'),
    'body_bold': ('SF Pro Text', 14, 'bold'),
    'body': ('SF Pro Text', 14, 'normal'),
    'small': ('SF Pro Text', 12, 'normal'),
    'tiny': ('SF Pro Text', 10, 'normal'),
}

# Enhanced Icon Set with Modern Variations
ICONS = {
    # Navigation Icons
    'dashboard': '🎯',  # More modern than 📊
    'products': '✨',   # More chic than 📦
    'sales': '💎',     # More elegant than 💰
    'users': '👤',     # More minimal than 👥
    'reports': '📱',   # More modern than 📈
    'settings': '⚙️',
    'logout': '→',    # More minimal than 🚪
    
    # Action Icons
    'add': '＋',      # More stylized plus
    'edit': '✎',      # More elegant pencil
    'delete': '×',    # More minimal than 🗑️
    'search': '⚲',    # More stylized search
    'menu': '☰',      # Hamburger menu
    'close': '×',     # Close button
    'back': '←',      # Back arrow
    'next': '→',      # Next arrow
    
    # Status Icons
    'success': '✓',   # More minimal than ✅
    'warning': '⚠',   # More minimal than ⚠️
    'error': '✕',     # More minimal than ❌
    'info': 'ℹ',      # More minimal than ℹ️
    
    # Additional Modern Icons
    'favorite': '♥',
    'share': '⤴',
    'download': '↓',
    'upload': '↑',
    'refresh': '⟳',
    'filter': '⚏',
    'sort': '⇅',
    'more': '⋮',
}

# Icon Sizes for Different Contexts
ICON_SIZES = {
    'tiny': ('Segoe UI Symbol', 14),
    'small': ('Segoe UI Symbol', 16),
    'medium': ('Segoe UI Symbol', 20),
    'large': ('Segoe UI Symbol', 24),
    'xlarge': ('Segoe UI Symbol', 32),
    'huge': ('Segoe UI Symbol', 48),
}

# Enhanced Spacing and Sizing
SPACING = {
    'xxs': 4,
    'xs': 8,
    'sm': 12,
    'md': 16,
    'lg': 24,
    'xl': 32,
    'xxl': 48
}

# Component Sizes
SIZES = {
    'button_height': 45,       # Taller buttons
    'input_height': 45,        # Matching input height
    'icon_size': 20,
    'border_radius': 8,        # Slightly rounded corners
    'card_radius': 12,         # More rounded for cards
}

# Animation Durations (in milliseconds)
ANIMATIONS = {
    'fast': 150,
    'normal': 250,
    'slow': 350,
}

def adjust_color_alpha(color, alpha):
    """Adjust color's alpha/opacity by returning a lighter version of the color"""
    if color.startswith('#'):
        # Convert hex to RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # For fade out, blend with background color
        bg_r = int(COLORS['background'][1:3], 16)
        bg_g = int(COLORS['background'][3:5], 16)
        bg_b = int(COLORS['background'][5:7], 16)
        
        # Interpolate between color and background
        final_r = int(r * alpha + bg_r * (1 - alpha))
        final_g = int(g * alpha + bg_g * (1 - alpha))
        final_b = int(b * alpha + bg_b * (1 - alpha))
        
        return f'#{final_r:02x}{final_g:02x}{final_b:02x}'
    return color

def setup_theme():
    """Configure global theme settings"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Configure default styles
    style = {
        "CTkButton": {
            "corner_radius": 8,
            "border_width": 0,
            "fg_color": COLORS['primary'],
            "hover_color": COLORS['primary_hover'],
            "text_color": COLORS['text'],
            "font": FONTS['body_bold']
        },
        "CTkEntry": {
            "corner_radius": 8,
            "border_width": 1,
            "fg_color": COLORS['input_bg'],
            "border_color": COLORS['input_border'],
            "text_color": COLORS['text'],
            "placeholder_text_color": COLORS['placeholder']
        },
        "CTkFrame": {
            "corner_radius": 10,
            "border_width": 0,
            "fg_color": COLORS['surface']
        }
    }

    # Apply default styles
    for widget, properties in style.items():
        try:
            widget_class = getattr(ctk, widget)
            for prop, value in properties.items():
                setattr(widget_class, f"_default_{prop}", value)
        except Exception:
            continue

def apply_theme_settings(widget):
    """Apply base theme settings to a widget"""
    widget.configure(
        fg_color=COLORS['background'],
        text_color=COLORS['text'],
    )

def apply_button_style(button, style='primary'):
    """Apply styled configuration to a button"""
    styles = {
        'primary': {
            'fg_color': COLORS['primary'],
            'hover_color': COLORS['primary_dark'],
            'text_color': COLORS['text'],
        },
        'secondary': {
            'fg_color': COLORS['surface'],
            'hover_color': COLORS['hover'],
            'text_color': COLORS['text'],
        },
        'accent': {
            'fg_color': COLORS['accent'],
            'hover_color': COLORS['accent_dark'],
            'text_color': COLORS['text'],
        },
        'outline': {
            'fg_color': 'transparent',
            'hover_color': COLORS['hover'],
            'text_color': COLORS['text'],
            'border_color': COLORS['primary'],
            'border_width': 1,
        },
        'danger': {
            'fg_color': COLORS['error'],
            'hover_color': '#DC2626',  # Darker red
            'text_color': COLORS['text'],
        }
    }
    
    style_config = styles.get(style, styles['primary'])
    button.configure(
        height=SIZES['button_height'],
        corner_radius=SIZES['border_radius'],
        font=FONTS['body_bold'],
        **style_config
    )

def apply_entry_style(entry):
    """Apply styled configuration to an entry or textbox widget"""
    base_config = {
        'height': SIZES['input_height'],
        'corner_radius': SIZES['border_radius'],
        'fg_color': COLORS['input_bg'],
        'border_color': COLORS['input_border'],
        'text_color': COLORS['text'],
        'font': FONTS['body']
    }
    
    # Add placeholder configuration only for CTkEntry
    if isinstance(entry, ctk.CTkEntry):
        base_config.update({
            'placeholder_text_color': COLORS['placeholder']
        })
    
    entry.configure(**base_config)

def apply_frame_style(frame, style='normal'):
    """Apply styled configuration to a frame"""
    styles = {
        'normal': {
            'fg_color': COLORS['surface'],
            'corner_radius': SIZES['border_radius'],
        },
        'card': {
            'fg_color': COLORS['card'],
            'corner_radius': SIZES['card_radius'],
        },
        'transparent': {
            'fg_color': 'transparent',
            'corner_radius': 0,
        }
    }
    
    style_config = styles.get(style, styles['normal'])
    frame.configure(**style_config)

def create_progress_bar(parent, width=None, determinate=True):
    """Create a styled progress bar with container"""
    container = ctk.CTkFrame(parent, fg_color='transparent')
    
    progress_bar = ctk.CTkProgressBar(
        container,
        width=width,
        height=6,
        corner_radius=3,
        mode='determinate' if determinate else 'indeterminate',
        progress_color=COLORS['primary'],
        fg_color=COLORS['input_bg']
    )
    
    if not determinate:
        progress_bar.start()
    else:
        progress_bar.set(0)
        
    return container, progress_bar

def show_status_message(parent, message, status_type='info', duration=3000):
    """Show a styled status message that fades out"""
    colors = {
        'success': COLORS['success'],
        'error': COLORS['error'],
        'warning': COLORS['warning'],
        'info': COLORS['info']
    }
    
    icons = {
        'success': ICONS['success'],
        'error': ICONS['error'],
        'warning': ICONS['warning'],
        'info': ICONS['info']
    }
    
    frame = ctk.CTkFrame(parent)
    apply_frame_style(frame, 'card')
    frame.place(relx=0.5, rely=0.9, anchor='center')
    
    icon_label = ctk.CTkLabel(
        frame,
        text=icons.get(status_type, ICONS['info']),
        font=FONTS['body'],
        text_color=colors.get(status_type, COLORS['info'])
    )
    icon_label.pack(side='left', padx=(10, 5), pady=10)
    
    message_label = ctk.CTkLabel(
        frame,
        text=message,
        font=FONTS['body'],
        text_color=COLORS['text']
    )
    message_label.pack(side='left', padx=(5, 10), pady=10)
    
    if duration:
        parent.after(duration, frame.destroy)
    
    return frame

def animate_progress(container, progress_bar, target_value, duration=500):
    """Animate progress bar to target value"""
    if not container.winfo_exists():
        return
        
    current = progress_bar.get() * 100
    target = target_value
    steps = 20
    step_size = (target - current) / steps
    step_duration = duration / steps
    
    def update_progress(step=0):
        if not container.winfo_exists() or step >= steps:
            return
            
        new_value = current + (step_size * (step + 1))
        progress_bar.set(new_value / 100)
        container.after(int(step_duration), lambda: update_progress(step + 1))
    
    update_progress()

def show_success_animation(parent, message):
    """Show a success animation with message"""
    frame = ctk.CTkFrame(parent)
    apply_frame_style(frame, 'card')
    frame.place(relx=0.5, rely=0.5, anchor='center')
    
    success_label = ctk.CTkLabel(
        frame,
        text=ICONS['success'],
        font=('Helvetica', 48),
        text_color=COLORS['success']
    )
    success_label.pack(pady=(20, 10))
    
    message_label = ctk.CTkLabel(
        frame,
        text=message,
        font=FONTS['body_bold'],
        text_color=COLORS['text']
    )
    message_label.pack(pady=(0, 20), padx=30)
    
    def fade_out(alpha=1.0):
        if alpha <= 0:
            frame.destroy()
            return
        frame.attributes('-alpha', alpha)
        parent.after(50, lambda: fade_out(alpha - 0.1))
    
    parent.after(2000, lambda: fade_out())

def create_gradient_frame(parent):
    """Create a frame with gradient effect"""
    frame = ctk.CTkFrame(parent)
    apply_frame_style(frame, 'gradient')
    return frame

def create_card_frame(parent, title=None):
    """Create a modern card frame with optional title"""
    card = ctk.CTkFrame(parent)
    apply_frame_style(card, 'card')
    
    if title:
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=FONTS['heading3'],
            text_color=COLORS['text']
        )
        title_label.pack(pady=(10, 5), padx=10)
    
    return card

# Enhanced Animation Durations
ANIMATIONS = {
    'instant': 100,
    'quick': 200,
    'normal': 300,
    'slow': 500,
    'very_slow': 800
}

# Enhanced Shadow Effects
SHADOWS = {
    'none': {
        'offset': (0, 0),
        'blur': 0,
        'color': '#000000'
    },
    'small': {
        'offset': (2, 2),
        'blur': 4,
        'color': '#000000'
    },
    'medium': {
        'offset': (4, 4),
        'blur': 8,
        'color': '#000000'
    },
    'large': {
        'offset': (8, 8),
        'blur': 16,
        'color': '#000000'
    },
    'glow': {
        'offset': (0, 0),
        'blur': 20,
        'color': COLORS['primary']
    }
}

def apply_tooltip(widget, text):
    """Apply a modern tooltip to a widget"""
    def show_tooltip(event):
        tooltip = ctk.CTkToplevel()
        tooltip.wm_overrideredirect(True)
        
        # Position tooltip below widget
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 5
        tooltip.geometry(f"+{x}+{y}")
        
        # Create tooltip content
        label = ctk.CTkLabel(
            tooltip,
            text=text,
            font=FONTS['small'],
            fg_color=COLORS['card'],
            corner_radius=5,
            padx=10,
            pady=5
        )
        label.pack()
        
        def hide_tooltip():
            tooltip.destroy()
        
        widget.tooltip = tooltip
        widget.after(2000, hide_tooltip)  # Hide after 2 seconds
    
    def hide_tooltip(event):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip
    
    widget.bind('<Enter>', show_tooltip)
    widget.bind('<Leave>', hide_tooltip)

def create_progress_bar(parent, width=None):
    """Create a progress bar container and bar"""
    container = ctk.CTkFrame(parent)
    apply_frame_style(container, 'normal')
    
    progress = ctk.CTkProgressBar(container)
    progress.set(0)
    if width:
        progress.configure(width=width)
    
    return container, progress

def animate_progress(container, progress_bar, target_value, duration=500):
    """Animate progress bar to target value"""
    if not container.winfo_exists():
        return
        
    current = progress_bar.get()
    if current >= target_value / 100:
        return
        
    step = (target_value / 100 - current) / 10
    progress_bar.set(current + step)
    
    if current + step < target_value / 100:
        container.after(50, lambda: animate_progress(container, progress_bar, target_value))

def show_success_animation(parent, message, duration=1500):
    """Show success message with enhanced fade animation"""
    if not parent.winfo_exists():
        return
        
    success_frame = ctk.CTkFrame(parent)
    apply_frame_style(success_frame, 'glass')
    success_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    # Icon (checkmark symbol)
    icon_label = ctk.CTkLabel(
        success_frame,
        text="✓",
        font=('Helvetica', 32, 'bold'),
        text_color=COLORS['success']
    )
    icon_label.pack(padx=20, pady=(20, 5))
    
    # Message
    success_label = ctk.CTkLabel(
        success_frame,
        text=message,
        font=FONTS['heading3'],
        text_color=COLORS['success']
    )
    success_label.pack(padx=30, pady=(5, 20))
    
    def fade_out(alpha=1.0):
        if not parent.winfo_exists() or not success_frame.winfo_exists():
            return
            
        if alpha > 0:
            try:
                # Calculate faded colors
                frame_color = adjust_color_alpha(COLORS['card'], alpha)
                text_color = adjust_color_alpha(COLORS['success'], alpha)
                
                # Update colors
                success_frame.configure(fg_color=frame_color)
                icon_label.configure(text_color=text_color)
                success_label.configure(text_color=text_color)
                
                # Smoother animation with more steps
                parent.after(20, lambda: fade_out(alpha - 0.05))
            except Exception as e:
                logger.warning(f"Fade animation error: {e}")
                success_frame.destroy()
        else:
            success_frame.destroy()
    
    # Start fade out after duration
    parent.after(duration, lambda: fade_out())

def show_status_message(parent, message, status_type="info", duration=2000):
    """Show a status message with animation"""
    if not parent.winfo_exists():
        return
        
    colors = {
        "info": COLORS['primary'],
        "success": COLORS['success'],
        "error": COLORS['error'],
        "warning": COLORS['warning']
    }
    
    status_frame = ctk.CTkFrame(parent)
    apply_frame_style(status_frame, 'card')
    status_frame.place(relx=0.5, rely=0.9, anchor="center")
    
    status_label = ctk.CTkLabel(
        status_frame,
        text=message,
        font=FONTS['body'],
        text_color=colors.get(status_type, COLORS['text'])
    )
    status_label.pack(padx=20, pady=10)
    
    if duration:
        def remove_status():
            if status_frame.winfo_exists():
                status_frame.destroy()
        parent.after(duration, remove_status)
    
    return status_frame

def create_styled_icon(parent, icon_name, size='medium', color=None, hover_color=None, onclick=None):
    """Create a beautifully styled icon with hover effects"""
    if icon_name not in ICONS:
        return None
        
    icon_frame = ctk.CTkFrame(parent, fg_color='transparent')
    
    # Get icon configuration
    icon_char = ICONS[icon_name]
    icon_font = ICON_SIZES.get(size, ICON_SIZES['medium'])
    icon_color = color if color else COLORS['text']
    icon_hover = hover_color if hover_color else COLORS['primary']
    
    # Create icon label
    icon_label = ctk.CTkLabel(
        icon_frame,
        text=icon_char,
        font=icon_font,
        text_color=icon_color,
        cursor='hand2' if onclick else 'arrow'
    )
    icon_label.pack(padx=2, pady=2)
    
    # Add hover effects
    def on_enter(e):
        icon_label.configure(text_color=icon_hover)
        
    def on_leave(e):
        icon_label.configure(text_color=icon_color)
    
    if onclick:
        icon_label.bind('<Button-1>', lambda e: onclick())
        icon_label.bind('<Enter>', on_enter)
        icon_label.bind('<Leave>', on_leave)
    
    return icon_frame

def create_icon_button(parent, icon_name, text=None, command=None, style='primary', size='medium'):
    """Create a modern button with an icon and optional text"""
    button_frame = ctk.CTkFrame(parent, fg_color='transparent')
    
    # Get style configuration
    styles = {
        'primary': {
            'fg_color': COLORS['primary'],
            'hover_color': COLORS['primary_dark'],
            'text_color': COLORS['text'],
            'icon_color': COLORS['text'],
        },
        'secondary': {
            'fg_color': COLORS['surface'],
            'hover_color': COLORS['hover'],
            'text_color': COLORS['text'],
            'icon_color': COLORS['text'],
        },
        'accent': {
            'fg_color': COLORS['accent'],
            'hover_color': COLORS['accent_dark'],
            'text_color': COLORS['text'],
            'icon_color': COLORS['text'],
        },
        'outline': {
            'fg_color': 'transparent',
            'hover_color': COLORS['hover'],
            'text_color': COLORS['primary'],
            'icon_color': COLORS['primary'],
            'border_color': COLORS['primary'],
            'border_width': 1,
        },
    }
    
    style_config = styles.get(style, styles['primary'])
    
    # Create button with icon
    button = ctk.CTkButton(
        button_frame,
        text=f"{ICONS.get(icon_name, '')} {text}" if text else ICONS.get(icon_name, ''),
        command=command,
        font=ICON_SIZES.get(size, ICON_SIZES['medium']),
        **style_config
    )
    button.pack(padx=2, pady=2)
    
    return button_frame

def create_icon_with_badge(parent, icon_name, badge_text, size='medium'):
    """Create an icon with a notification badge"""
    container = ctk.CTkFrame(parent, fg_color='transparent')
    
    # Create icon
    icon_label = ctk.CTkLabel(
        container,
        text=ICONS.get(icon_name, ''),
        font=ICON_SIZES.get(size, ICON_SIZES['medium']),
        text_color=COLORS['text']
    )
    icon_label.pack(padx=2, pady=2)
    
    # Create badge
    badge = ctk.CTkLabel(
        container,
        text=str(badge_text),
        font=FONTS['tiny'],
        text_color=COLORS['text'],
        fg_color=COLORS['error'],
        corner_radius=10,
        width=16,
        height=16
    )
    badge.place(relx=0.7, rely=0.0)
    
    return container

def apply_option_menu_style(option_menu, style='primary'):
    """Apply styled configuration to an option menu"""
    styles = {
        'primary': {
            'fg_color': COLORS['primary'],
            'button_color': COLORS['primary_dark'],
            'button_hover_color': COLORS['primary_hover'],
            'text_color': COLORS['text'],
        },
        'secondary': {
            'fg_color': COLORS['surface'],
            'button_color': COLORS['hover'],
            'button_hover_color': COLORS['card'],
            'text_color': COLORS['text'],
        }
    }
    
    style_config = styles.get(style, styles['primary'])
    option_menu.configure(
        height=SIZES['button_height'],
        corner_radius=SIZES['border_radius'],
        font=FONTS['body'],
        dropdown_font=FONTS['body'],
        **style_config
    ) 