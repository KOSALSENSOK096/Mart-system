import os
import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image
from utils.database import Database
from utils.styles import (
    setup_theme,
    FONTS,
    apply_button_style,
    apply_entry_style,
    apply_frame_style,
    create_progress_bar,
    animate_progress,
    show_success_animation,
    show_status_message
)
import logging
import time
from utils.font_config import configure_fonts
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for better compatibility
import bcrypt
import platform
import socket
import uuid
import json
import threading
from typing import Dict, Any

# Configure fonts before creating any windows
configure_fonts()

# Set system encoding to UTF-8
import locale
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create receipts directory if it doesn't exist
RECEIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "receipts")
if not os.path.exists(RECEIPTS_DIR):
    try:
        os.makedirs(RECEIPTS_DIR, exist_ok=True)
        logger.info(f"Created receipts directory at {RECEIPTS_DIR}")
    except Exception as e:
        logger.error(f"Failed to create receipts directory: {e}")
        messagebox.showerror("Error", f"Failed to create receipts directory: {e}\nPlease ensure you have write permissions.")
        sys.exit(1)
elif not os.access(RECEIPTS_DIR, os.W_OK):
    logger.error("Receipts directory exists but is not writable")
    messagebox.showerror("Error", "Receipts directory exists but is not writable.\nPlease check permissions.")
    sys.exit(1)

try:
    from config import APP_NAME
except ImportError:
    APP_NAME = "Tea House Manager"  # Updated app name to match theme

# Fix DPI awareness for Windows
if os.name == 'nt':
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        logger.warning(f"Failed to set DPI awareness: {e}")

# Set up theme
setup_theme()

# Global color scheme
COLORS = {
    'background': '#0A0B0E',     # Dark background
    'surface': '#1A1B1F',        # Card background
    'glass': '#1E1F23',          # Input field background
    'hover': '#2A2B2F',          # Hover state
    'text': '#FFFFFF',           # White text
    'text_secondary': '#B0B3B8', # Secondary text
    'primary': '#7C5DFA',        # Purple accent
    'primary_dark': '#6548C7',   # Darker purple
    'primary_hover': '#5434A7',  # Purple hover
    'secondary': '#24B47E',      # Green accent
    'secondary_hover': '#1C9D6A', # Green hover
    'accent': '#7C5DFA',         # Same as primary
    'accent_hover': '#6548C7',   # Same as primary_dark
    'error': '#FF4B6E',          # Error red
    'success': '#24B47E',        # Success green
    'warning': '#FFB84D',        # Warning orange
    'input_bg': '#1E1F23',       # Input background
    'input_border': '#2A2B2F',   # Input border
    'placeholder': '#6E7175',    # Placeholder text
    'separator': '#2A2B2F',      # Separator line
    'glass_border': '#2A2B2F'    # Glass effect border
}

class RegisterForm(ctk.CTkFrame):
    def __init__(self, parent, on_register=None, on_cancel=None):
        super().__init__(parent)
        self.parent = parent
        self.on_register = on_register
        self.on_cancel = on_cancel
        self.db = Database()
        
        # Initialize validation states
        self.username_valid = False
        self.password_valid = False
        self.passwords_match = False
        
        # Minimum requirements
        self.MIN_USERNAME_LENGTH = 3
        self.MIN_PASSWORD_LENGTH = 8
        
        # Configure frame styling
        self.configure(
            fg_color=COLORS['surface'],
            border_width=1,
            border_color=COLORS['glass'],
            corner_radius=15
        )
        
        # Configure grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create scrollable frame for form content
        self.form_frame = ctk.CTkScrollableFrame(self)
        self.form_frame.configure(
            fg_color='transparent',
            corner_radius=10
        )
        self.form_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        
        # Configure form frame grid
        self.form_frame.grid_columnconfigure(0, weight=1)
        
        self.create_form_fields()
        
    def create_form_field(self, label_text, entry_attr, icon, show=None):
        """Create a form field with grid layout"""
        frame = ctk.CTkFrame(
            self.form_frame,
            fg_color=COLORS['glass'],
            corner_radius=8
        )
        frame.grid_columnconfigure(1, weight=1)
        
        # Icon
        icon_label = ctk.CTkLabel(
            frame,
            text=icon,
            font=("Segoe UI Emoji", 20),
            text_color=COLORS['primary']
        )
        icon_label.grid(row=0, column=0, padx=15, pady=12)
        
        # Entry field
        entry = ctk.CTkEntry(
            frame,
            placeholder_text=f"Enter {label_text.lower()}",
            show=show,
            height=45,
            font=("Segoe UI", 14),
            fg_color="transparent",
            border_width=0,
            placeholder_text_color=COLORS['placeholder'],
            text_color=COLORS['text']
        )
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 15))
        
        # Store entry widget reference
        setattr(self, entry_attr, entry)
        
        # Validation indicator
        validation_label = ctk.CTkLabel(
            frame,
            text="",
            font=("Segoe UI", 16),
            text_color=COLORS['text']
        )
        validation_label.grid(row=0, column=2, padx=10)
        
        # Store validation label reference
        setattr(self, f"{entry_attr}_validation", validation_label)
        
        return frame

    def create_form_fields(self):
        """Create form fields with grid layout"""
        current_row = 0
        
        # Username field
        username_frame = self.create_form_field("Username", "username_entry", "👤")
        username_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 15))
        self.username_entry.bind('<KeyRelease>', lambda e: self.validate_username())
        current_row += 1
        
        # Password field
        password_frame = self.create_form_field("Password", "password_entry", "🔒", show="•")
        password_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 5))
        self.password_entry.bind('<KeyRelease>', lambda e: self.validate_password())
        current_row += 1
        
        # Password requirements
        self.password_req_label = ctk.CTkLabel(
            self.form_frame,
            text="Password must be at least 8 characters",
            font=("Segoe UI", 12),
            text_color=COLORS['warning']
        )
        self.password_req_label.grid(row=current_row, column=0, sticky="w", pady=(0, 15))
        current_row += 1
        
        # Confirm Password field
        confirm_frame = self.create_form_field("Confirm Password", "confirm_password_entry", "🔒", show="•")
        confirm_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 20))
        self.confirm_password_entry.bind('<KeyRelease>', lambda e: self.validate_passwords_match())
        current_row += 1
        
        # Account Type selection
        role_frame = ctk.CTkFrame(
            self.form_frame,
            fg_color=COLORS['glass'],
            corner_radius=8
        )
        role_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 30))
        role_frame.grid_columnconfigure(1, weight=1)
        
        role_icon = ctk.CTkLabel(
            role_frame,
            text="👥",
            font=("Segoe UI Emoji", 20),
            text_color=COLORS['primary']
        )
        role_icon.grid(row=0, column=0, padx=15, pady=12)
        
        ctk.CTkLabel(
            role_frame,
            text="Account Type",
            font=("Segoe UI", 14),
            text_color=COLORS['text']
        ).grid(row=0, column=1, sticky="w")
        
        self.role_var = ctk.StringVar(value="staff")
        self.role_menu = ctk.CTkOptionMenu(
            role_frame,
            values=["staff", "admin"],
            variable=self.role_var,
            font=("Segoe UI", 13),
            fg_color=COLORS['primary'],
            button_color=COLORS['primary'],
            button_hover_color=COLORS['primary_hover'],
            dropdown_font=("Segoe UI", 13),
            corner_radius=8,
            width=120
        )
        self.role_menu.grid(row=0, column=2, padx=15, pady=8)
        current_row += 1
        
        # Create Account button
        self.register_btn = ctk.CTkButton(
            self.form_frame,
            text="Create Account",
            command=self.register,
            height=45,
            font=("Segoe UI", 15, "bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            corner_radius=8
        )
        self.register_btn.grid(row=current_row, column=0, sticky="ew", pady=(0, 15))
        current_row += 1
        
        # Back to Login button
        back_btn = ctk.CTkButton(
            self.form_frame,
            text="Back to Login",
            command=self.on_cancel if self.on_cancel else self.master.destroy,
            height=45,
            font=("Segoe UI", 15, "bold"),
            fg_color="transparent",
            hover_color=COLORS['glass'],
            border_color=COLORS['glass'],
            border_width=1,
            text_color=COLORS['text'],
            corner_radius=8
        )
        back_btn.grid(row=current_row, column=0, sticky="ew")
        current_row += 1
        
        # Status message
        self.status_label = ctk.CTkLabel(
            self.form_frame,
            text="",
            font=("Segoe UI", 13),
            text_color=COLORS['text']
        )
        self.status_label.grid(row=current_row, column=0, pady=10)

    def validate_username(self):
        """Validate username as user types"""
        username = self.username_entry.get().strip()
        validation_label = getattr(self, "username_entry_validation")
        
        if len(username) < self.MIN_USERNAME_LENGTH:
            validation_label.configure(text="❌", text_color=COLORS['error'])
            self.username_valid = False
            self.show_status(f"Username must be at least {self.MIN_USERNAME_LENGTH} characters", "warning")
        else:
            # Check if username exists
            query = "SELECT id FROM users WHERE username = %s"
            if self.db.execute_query(query, (username,)):
                validation_label.configure(text="❌", text_color=COLORS['error'])
                self.username_valid = False
                self.show_status("Username already exists", "error")
            else:
                validation_label.configure(text="✓", text_color=COLORS['success'])
                self.username_valid = True
                self.show_status("")
        
        self.update_register_button()
        
    def validate_password(self):
        """Validate password as user types"""
        password = self.password_entry.get()
        validation_label = getattr(self, "password_entry_validation")
        
        if len(password) < self.MIN_PASSWORD_LENGTH:
            validation_label.configure(text="❌", text_color=COLORS['error'])
            self.password_req_label.configure(text_color=COLORS['error'])
            self.password_valid = False
            self.show_status(f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters", "warning")
        else:
            validation_label.configure(text="✓", text_color=COLORS['success'])
            self.password_req_label.configure(text_color=COLORS['success'])
            self.password_valid = True
            self.show_status("")
        
        self.validate_passwords_match()
        self.update_register_button()
        
    def validate_passwords_match(self):
        """Validate that passwords match"""
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        validation_label = getattr(self, "confirm_password_entry_validation")
        
        if not confirm_password:
            validation_label.configure(text="")
            self.passwords_match = False
        elif password != confirm_password:
            validation_label.configure(text="❌", text_color=COLORS['error'])
            self.passwords_match = False
        else:
            validation_label.configure(text="✓", text_color=COLORS['success'])
            self.passwords_match = True
        
        self.update_register_button()
        
    def update_register_button(self):
        """Update register button state based on validation"""
        if self.username_valid and self.password_valid and self.passwords_match:
            self.register_btn.configure(state="normal")
        else:
            self.register_btn.configure(state="disabled")
            
    def show_status(self, message, status_type="info"):
        """Show status message with appropriate styling"""
        colors = {
            "info": COLORS['primary'],
            "success": COLORS['success'],
            "error": COLORS['error'],
            "warning": COLORS['warning']
        }
        self.status_label.configure(
            text=message,
            text_color=colors.get(status_type, COLORS['text'])
        )
        
    def register(self):
        """Handle registration with progress indication"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        role = self.role_var.get()
        
        if not self.username_valid or not self.password_valid or not self.passwords_match:
            self.show_status("Please fix validation errors before registering", "error")
            return
        
        # Show registration progress
        progress_frame = ctk.CTkFrame(self.form_frame, fg_color='transparent')
        progress_frame.grid(row=99, column=0, sticky="ew", pady=10)  # Use grid instead of pack
        
        progress_bar = ctk.CTkProgressBar(progress_frame)
        progress_bar.configure(
            mode="determinate",
            determinate_speed=0.5,
            height=6,
            corner_radius=3,
            fg_color=COLORS['glass'],
            progress_color=COLORS['primary']
        )
        progress_bar.grid(row=0, column=0, sticky="ew", padx=2)  # Use grid instead of pack
        progress_bar.set(0)
        
        # Start progress animation
        self.animate_progress(progress_frame, progress_bar, 33)
        
        try:
            # Final check if username exists
            query = "SELECT id FROM users WHERE username = %s"
            if self.db.execute_query(query, (username,)):
                self.show_status("Username already exists", "error")
                progress_frame.destroy()
                return
            
            # Update progress
            self.animate_progress(progress_frame, progress_bar, 66)
            
            # Create user with retry
            success = False
            for attempt in range(3):  # Try up to 3 times
                if self.db.create_user(username, password, role):
                    success = True
                    break
                time.sleep(0.5)  # Wait before retry
            
            if success:
                # Complete progress
                self.animate_progress(progress_frame, progress_bar, 100)
                
                # Show success message
                success_frame = ctk.CTkFrame(self.form_frame, fg_color='transparent')
                success_frame.grid(row=100, column=0, sticky="ew", pady=10)  # Use grid instead of pack
                
                success_label = ctk.CTkLabel(
                    success_frame,
                    text="✨ Account created successfully!",
                    font=("Segoe UI", 14),
                    text_color=COLORS['success']
                )
                success_label.grid(row=0, column=0, pady=5)  # Use grid instead of pack
                
                # Call the success callback if provided
                if self.on_register:
                    self.after(1000, lambda: self.on_register(username, role))
                else:
                    self.after(1000, self.master.destroy)
            else:
                self.show_status("Failed to create account. Please try again.", "error")
                progress_frame.destroy()
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            self.show_status(f"Registration error: {str(e)}", "error")
            progress_frame.destroy()

    def animate_progress(self, frame, progress_bar, target_value):
        """Animate progress bar to target value"""
        current = progress_bar.get() * 100
        if current < target_value:
            progress_bar.set(current / 100 + 0.01)
            self.after(20, lambda: self.animate_progress(frame, progress_bar, target_value))
        elif target_value >= 100:
            frame.after(500, frame.destroy)  # Clean up progress bar after completion

class RegisterWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configure window
        width, height = WindowManager.REGISTER_SIZE
        WindowManager.setup_window(
            self,
            f"{APP_NAME} - Create Account",
            width,
            height,
            resizable=(False, False)  # Make window fixed size
        )
        
        # Configure grid weights for resizing
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Configure window background and style
        self.configure(fg_color=COLORS['background'])
        
        # Create main container with grid
        self.main_container = ctk.CTkFrame(self)
        self.main_container.configure(fg_color=COLORS['background'])
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure main container grid
        self.main_container.grid_rowconfigure(0, weight=0)  # Header doesn't expand
        self.main_container.grid_rowconfigure(1, weight=1)  # Form takes remaining space
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Add decorative header
        self.create_header()
        
        # Create registration form with enhanced styling
        self.register_form = RegisterForm(
            self.main_container,
            on_register=self.on_register_success,
            on_cancel=self.destroy
        )
        self.register_form.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Make window modal
        self.grab_set()
        
        # Focus username field
        self.register_form.username_entry.focus_set()
        
        # Center window on screen
        self.center_window()
        
        # Add window animation
        self.animate_window()

    def center_window(self):
        """Center window on screen"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.winfo_width()) // 2
        y = (screen_height - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def create_header(self):
        """Create decorative header for the registration window"""
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.configure(
            fg_color=COLORS['surface'],
            border_width=1,
            border_color=COLORS['glass_border'],
            corner_radius=15
        )
        header_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        
        # Configure header frame grid
        header_frame.grid_rowconfigure((0, 1, 2, 3), weight=0)
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Tea table themed icon container
        icon_container = ctk.CTkFrame(
            header_frame,
            fg_color=COLORS['primary'],
            width=80,
            height=80,
            corner_radius=40
        )
        icon_container.grid(row=0, column=0, pady=(25, 15))
        
        # Tea pot icon with elegant frame
        icon_frame = ctk.CTkFrame(
            icon_container,
            fg_color=COLORS['background'],
            width=60,
            height=60,
            corner_radius=30
        )
        icon_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        icon_label = ctk.CTkLabel(
            icon_frame,
            text="🫖",
            font=("Segoe UI Emoji", 30),
            text_color=COLORS['text']
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Decorative tea cups
        cups_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        cups_frame.grid(row=1, column=0, pady=(0, 12))
        
        # Configure cups frame grid
        cups_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Tea cup arrangement
        tea_items = [
            ("☕", COLORS['secondary']),
            ("🍵", COLORS['primary']),
            ("☕", COLORS['secondary'])
        ]
        
        for i, (emoji, color) in enumerate(tea_items):
            ctk.CTkLabel(
                cups_frame,
                text=emoji,
                font=("Segoe UI Emoji", 20),
                text_color=color
            ).grid(row=0, column=i, padx=4)
        
        # Welcome text with tea theme
        title = ctk.CTkLabel(
            header_frame,
            text="Join Our Tea House",
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS['text']
        )
        title.grid(row=2, column=0, pady=(0, 5))
        
        subtitle = ctk.CTkLabel(
            header_frame,
            text="Create your account to start your tea journey",
            font=("Segoe UI", 13),
            text_color=COLORS['text_secondary']
        )
        subtitle.grid(row=3, column=0, pady=(0, 20))

    def animate_window(self):
        """Create a smooth fade-in animation"""
        self.attributes('-alpha', 0.0)
        
        def fade_in(alpha=0.0):
            alpha += 0.1
            if alpha <= 1.0:
                self.attributes('-alpha', alpha)
                self.after(20, lambda: fade_in(alpha))
        
        fade_in()
        
    def on_register_success(self, username, role):
        """Handle successful registration with animation"""
        def fade_out():
            alpha = float(self.attributes('-alpha'))
            if alpha > 0:
                alpha -= 0.1
                self.attributes('-alpha', alpha)
                self.after(20, fade_out)
            else:
                self.destroy()
        
        fade_out()

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize variables
        self.status_label = None
        self.loading_overlay = None
        self.animation_running = False
        self.loading_labels = []
        self.loading_text = None
        
        # Set up theme
        setup_theme()
        
        # Configure window
        width, height = WindowManager.LOGIN_SIZE
        WindowManager.setup_window(
            self,
            f"{APP_NAME} - Login",
            width,
            height,
            resizable=(False, False)
        )
        
        # Configure grid weights for resizing
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create main container with grid
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.configure(fg_color=COLORS['background'])
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Initialize database connection
        try:
            self.db = Database()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            messagebox.showerror("Error", f"Failed to connect to database: {e}")
            self.destroy()
            return
        
        # Create UI elements
        self.create_ui()
        
        # Bind enter key to login
        self.bind('<Return>', lambda e: self.login())
        
        # Focus username entry
        self.username_entry.focus_set()

    def cleanup_animations(self):
        """Clean up any running animations"""
        self.animation_running = False
        if hasattr(self, 'loading_overlay') and self.loading_overlay is not None:
            try:
                self.loading_overlay.destroy()
            except Exception:
                pass
        self.loading_overlay = None
        self.loading_labels = []
        self.loading_text = None

    def set_inputs_state(self, state):
        """Enable or disable input fields"""
        try:
            self.username_entry.configure(state=state)
            self.password_entry.configure(state=state)
            self.login_btn.configure(state=state)
        except Exception as e:
            logger.error(f"Error setting input state: {e}")

    def process_login_async(self, username, password):
        """Process login asynchronously"""
        try:
            # Simulate network delay for better UX
            time.sleep(1.5)
            
            # Get user from database
            query = "SELECT * FROM users WHERE username = %s"
            result = self.db.execute_query(query, (username,))
            
            if not result:
                self.after(0, lambda: self.handle_login_error(
                    "Invalid username or password\nPlease check your credentials and try again"
                ))
                return
            
            user = result[0]
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                # Record successful login
                self.record_login_attempt(user['id'], True, "Login successful")
                
                # Update last login
                self.db.execute_query(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user['id'],)
                )
                
                # Show success on main thread
                self.after(0, lambda: self.handle_login_success(user, username))
            else:
                self.after(0, lambda: self.handle_login_error(
                    "Incorrect password\nPlease check your password and try again"
                ))
                self.record_login_attempt(user['id'], False, "Invalid password")
            
        except Exception as e:
            logger.error(f"Login processing error: {e}")
            self.after(0, lambda: self.handle_login_error(f"Login failed: {str(e)}"))

    def animate_loading(self, index=0):
        """Animate the loading icons"""
        if not self.animation_running or not self.loading_labels:
            return
            
        try:
            for i, label in enumerate(self.loading_labels):
                if not label.winfo_exists():
                    return
                size = 24 if i != index else 28
                color = COLORS['text_secondary'] if i != index else COLORS['primary']
                label.configure(font=("Segoe UI Emoji", size), text_color=color)
            
            if self.animation_running:
                next_index = (index + 1) % len(self.loading_labels) if self.loading_labels else 0
                self.after(300, lambda: self.animate_loading(next_index))
                
        except Exception as e:
            logger.error(f"Error in loading icon animation: {e}")

    def animate_dots(self, count=0):
        """Animate the loading dots"""
        if not self.animation_running or not self.loading_text:
            return
            
        try:
            if self.loading_text.winfo_exists():
                dots = "." * (count % 4)
                self.loading_text.configure(text=f"Brewing your session{dots}")
                
                if self.animation_running:
                    self.after(500, lambda: self.animate_dots(count + 1))
                    
        except Exception as e:
            logger.error(f"Error in dots animation: {e}")

    def shake_form(self):
        """Shake animation for form validation"""
        try:
            original_x = self.main_frame.winfo_x()
            shake_distance = 10
            shake_speed = 50
            
            def shake(times=6, distance=shake_distance):
                if times > 0:
                    new_x = original_x + (distance if times % 2 == 0 else -distance)
                    self.main_frame.place(x=new_x)
                    distance = int(distance * 0.8)  # Reduce shake distance each time
                    self.after(shake_speed, lambda: shake(times - 1, distance))
                else:
                    self.main_frame.place(x=original_x)
            
            shake()
            
        except Exception as e:
            logger.error(f"Error in shake animation: {e}")

    def highlight_fields_error(self):
        """Highlight input fields in error state"""
        try:
            # Create a lighter version of the error color for better visibility
            error_color = COLORS['error']  # Use error color for error state
            
            def flash_error(times=3):
                if times > 0:
                    self.username_entry.configure(fg_color=COLORS['glass'])
                    self.password_entry.configure(fg_color=COLORS['glass'])
                    self.after(200, lambda: remove_error(times))
                else:
                    self.username_entry.configure(fg_color=error_color)
                    self.password_entry.configure(fg_color=error_color)
            
            def remove_error(times):
                self.username_entry.configure(fg_color=error_color)
                self.password_entry.configure(fg_color=error_color)
                self.after(200, lambda: flash_error(times - 1))
            
            flash_error()
            
        except Exception as e:
            logger.error(f"Error in field highlighting: {e}")
            # Ensure fields return to normal state
            try:
                self.username_entry.configure(fg_color=COLORS['glass'])
                self.password_entry.configure(fg_color=COLORS['glass'])
            except:
                pass

    def show_validation_message(self, message, status_type="info"):
        """Show validation message with animation"""
        try:
            if self.status_label:
                self.status_label.destroy()
            
            self.status_label = ctk.CTkLabel(
                self.status_frame,
                text="",
                font=("Segoe UI", 13),
                text_color=COLORS[status_type]
            )
            self.status_label.grid(row=0, column=0, pady=10)
            
            def type_message(index=0):
                if not self.status_label.winfo_exists():
                    return
                self.status_label.configure(text=message[:index])
                if index < len(message):
                    self.after(20, lambda: type_message(index + 1))
            
            type_message()
            
        except Exception as e:
            logger.error(f"Error showing validation message: {e}")

    def record_login_attempt(self, user_id, status, message):
        """Record login attempt with enhanced tracking"""
        try:
            # Get system info
            os_info = f"{platform.system()} {platform.release()}"
            browser_info = f"Python {platform.python_version()}"
            ip_address = socket.gethostbyname(socket.gethostname())
            
            # Get device info
            device_info = {
                "machine": platform.machine(),
                "processor": platform.processor(),
                "node": platform.node(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "device_id": str(uuid.getnode())
            }
            
            # Create session ID
            session_id = str(uuid.uuid4())
            
            # Get location (in a real app, you might want to use a geolocation service)
            location = "Local"
            
            # Insert login record
            query = """
                INSERT INTO login_history (
                    user_id, ip_address, device_info, browser_info,
                    location, os_info, session_id, status,
                    status_message, login_type
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            self.db.execute_query(query, (
                user_id,
                ip_address,
                json.dumps(device_info),
                browser_info,
                location,
                os_info,
                session_id,
                status,
                message,
                'password'
            ))
            
        except Exception as e:
            logger.error(f"Failed to record login attempt: {e}")

    def create_ui(self):
        """Create the login UI elements"""
        # Configure main frame grid
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create login container with adjusted size
        login_container = ctk.CTkFrame(self.main_frame)
        login_container.configure(
            fg_color=COLORS['surface'],
            border_width=1,
            border_color=COLORS['glass_border'],
            corner_radius=20
        )
        login_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure login container grid
        login_container.grid_rowconfigure((0, 1, 2, 3, 4), weight=0)
        login_container.grid_columnconfigure(0, weight=1)
        
        # Create icon frame with adjusted size
        icon_frame = ctk.CTkFrame(
            login_container,
            fg_color=COLORS['primary'],
            width=80,
            height=80,
            corner_radius=40
        )
        icon_frame.grid(row=0, column=0, pady=(50, 20))
        
        # Inner icon frame
        inner_frame = ctk.CTkFrame(
            icon_frame,
            fg_color=COLORS['background'],
            width=60,
            height=60,
            corner_radius=30
        )
        inner_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Teapot icon
        teapot_label = ctk.CTkLabel(
            inner_frame,
            text="🫖",
            font=("Segoe UI Emoji", 30),
            text_color=COLORS['text']
        )
        teapot_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Welcome text with adjusted font sizes
        title = ctk.CTkLabel(
            login_container,
            text="Welcome to Tea Time",
            font=("Segoe UI", 28, "bold"),
            text_color=COLORS['text']
        )
        title.grid(row=1, column=0, pady=(0, 5))
        
        subtitle = ctk.CTkLabel(
            login_container,
            text="Your perfect tea house awaits",
            font=("Segoe UI", 14),
            text_color=COLORS['text_secondary']
        )
        subtitle.grid(row=2, column=0, pady=(0, 40))
        
        # Form frame with adjusted padding
        form_frame = ctk.CTkFrame(login_container, fg_color="transparent")
        form_frame.grid(row=3, column=0, padx=40, sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)
        
        # Username field with adjusted size
        username_frame = ctk.CTkFrame(form_frame, fg_color=COLORS['glass'], corner_radius=8)
        username_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        username_frame.grid_columnconfigure(1, weight=1)
        
        username_icon = ctk.CTkLabel(
            username_frame,
            text="👤",
            font=("Segoe UI Emoji", 20),
            text_color=COLORS['primary']
        )
        username_icon.grid(row=0, column=0, padx=15, pady=12)
        
        self.username_entry = ctk.CTkEntry(
            username_frame,
            placeholder_text="Enter your username",
            height=45,
            font=("Segoe UI", 14),
            fg_color="transparent",
            border_width=0,
            placeholder_text_color=COLORS['placeholder'],
            text_color=COLORS['text']
        )
        self.username_entry.grid(row=0, column=1, sticky="ew", padx=(0, 15))
        
        # Password field with adjusted size
        password_frame = ctk.CTkFrame(form_frame, fg_color=COLORS['glass'], corner_radius=8)
        password_frame.grid(row=1, column=0, sticky="ew", pady=(0, 25))
        password_frame.grid_columnconfigure(1, weight=1)
        
        password_icon = ctk.CTkLabel(
            password_frame,
            text="🔒",
            font=("Segoe UI Emoji", 20),
            text_color=COLORS['primary']
        )
        password_icon.grid(row=0, column=0, padx=15, pady=12)
        
        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Enter your password",
            show="•",
            height=45,
            font=("Segoe UI", 14),
            fg_color="transparent",
            border_width=0,
            placeholder_text_color=COLORS['placeholder'],
            text_color=COLORS['text']
        )
        self.password_entry.grid(row=0, column=1, sticky="ew", padx=(0, 15))
        
        # Sign In button with adjusted size
        self.login_btn = ctk.CTkButton(
            form_frame,
            text="Sign In",
            command=self.login,
            height=45,
            font=("Segoe UI", 15, "bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            corner_radius=8
        )
        self.login_btn.grid(row=2, column=0, sticky="ew", pady=(0, 30))
        
        # Register section with adjusted styling
        register_frame = ctk.CTkFrame(login_container)
        register_frame.configure(
            fg_color=COLORS['glass'],
            corner_radius=15
        )
        register_frame.grid(row=4, column=0, padx=40, pady=(0, 40), sticky="ew")
        register_frame.grid_columnconfigure(0, weight=1)
        
        reg_title = ctk.CTkLabel(
            register_frame,
            text="New to Our Tea House?",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS['text']
        )
        reg_title.grid(row=0, column=0, pady=(20, 5))
        
        reg_subtitle = ctk.CTkLabel(
            register_frame,
            text="Join us to start your tea journey",
            font=("Segoe UI", 13),
            text_color=COLORS['text_secondary']
        )
        reg_subtitle.grid(row=1, column=0, pady=(0, 15))
        
        # Create New Account button with adjusted size
        register_btn = ctk.CTkButton(
            register_frame,
            text="Create New Account",
            command=self.show_register,
            height=45,
            font=("Segoe UI", 15, "bold"),
            fg_color=COLORS['secondary'],
            hover_color=COLORS['secondary_hover'],
            corner_radius=8
        )
        register_btn.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="ew")
        
        # Status frame
        self.status_frame = ctk.CTkFrame(login_container)
        self.status_frame.configure(
            fg_color="transparent",
            corner_radius=10
        )
        self.status_frame.grid(row=5, column=0, sticky="ew", pady=10)
        self.status_frame.grid_columnconfigure(0, weight=1)

    def show_register(self):
        """Show registration window"""
        def on_register_success(username, role):
            """Handle successful registration"""
            # Pre-fill username in login form
            self.username_entry.delete(0, 'end')
            self.username_entry.insert(0, username)
            self.password_entry.focus()
            
            # Show welcome message
            self.show_validation_message(f"✨ Welcome {username}! Please sign in.", "success")
        
        register_window = RegisterWindow(self)
        register_window.register_form.on_register = on_register_success
        register_window.grab_set()

    def login(self):
        """Handle login with enhanced loading animation and validation"""
        # Clean up any existing animations
        self.cleanup_animations()
        
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            if not username and not password:
                self.show_validation_message("Please enter your username and password", "warning")
            elif not username:
                self.show_validation_message("Please enter your username", "warning")
            else:
                self.show_validation_message("Please enter your password", "warning")
            self.shake_form()
            return
        
        # Disable inputs during login
        self.set_inputs_state("disabled")
        
        try:
            # Create semi-transparent overlay
            self.loading_overlay = ctk.CTkFrame(self.main_frame)
            self.loading_overlay.configure(fg_color="black")
            self.loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            # Set transparency (0.9 = 90% transparent)
            try:
                self.loading_overlay.attributes('-alpha', 0.1)
            except:
                pass  # Fallback if transparency not supported
            
            # Loading animation container with glass effect
            loading_frame = ctk.CTkFrame(self.loading_overlay)
            loading_frame.configure(
                fg_color=COLORS['glass'],
                border_width=1,
                border_color=COLORS['glass_border'],
                corner_radius=15
            )
            loading_frame.place(relx=0.5, rely=0.5, anchor="center")
            
            # Start animations
            self.animation_running = True
            self.start_loading_animation(loading_frame)
            
            # Process login in a separate thread
            threading.Thread(
                target=self.process_login_async,
                args=(username, password),
                daemon=True
            ).start()
            
        except Exception as e:
            logger.error(f"Failed to start login process: {e}")
            self.cleanup_animations()
            self.set_inputs_state("normal")
            self.show_validation_message(f"Login failed: {str(e)}", "error")

    def start_loading_animation(self, loading_frame):
        """Start the loading animation sequence"""
        if not self.animation_running:
            return
            
        try:
            # Tea cup loading animation with glow effect
            loading_icons = ["🫖", "☕", "🍵"]
            self.loading_labels = []
            
            icon_frame = ctk.CTkFrame(loading_frame, fg_color="transparent")
            icon_frame.grid(row=0, column=0, padx=30, pady=(20, 0))
            
            for i, icon in enumerate(loading_icons):
                label = ctk.CTkLabel(
                    icon_frame,
                    text=icon,
                    font=("Segoe UI Emoji", 24),
                    text_color=COLORS['primary']
                )
                label.grid(row=0, column=i, padx=10)
                self.loading_labels.append(label)
            
            # Loading message with typing animation
            self.loading_text = ctk.CTkLabel(
                loading_frame,
                text="Brewing your session",
                font=("Segoe UI", 14),
                text_color=COLORS['text']
            )
            self.loading_text.grid(row=1, column=0, pady=(15, 20))
            
            # Start animations
            self.animate_loading()
            self.animate_dots()
            
        except Exception as e:
            logger.error(f"Error in loading animation: {e}")
            self.cleanup_animations()

    def handle_login_success(self, user: Dict[str, Any], username: str):
        """Handle successful login on main thread"""
        if not self.animation_running:
            return
            
        try:
            # Show success animation
            if self.loading_overlay and self.loading_overlay.winfo_exists():
                for widget in self.loading_overlay.winfo_children():
                    widget.destroy()
                
                # Success container
                success_frame = ctk.CTkFrame(self.loading_overlay)
                success_frame.configure(
                    fg_color=COLORS['glass'],
                    border_width=1,
                    border_color=COLORS['glass_border'],
                    corner_radius=15
                )
                success_frame.place(relx=0.5, rely=0.5, anchor="center")
                
                # Success icon with glow effect
                icon_container = ctk.CTkFrame(
                    success_frame,
                    fg_color="transparent",
                    width=80,
                    height=80
                )
                icon_container.grid(row=0, column=0, padx=30, pady=(20, 15))
                icon_container.grid_propagate(False)
                
                # Outer glow
                glow_outer = ctk.CTkFrame(
                    icon_container,
                    fg_color=COLORS['success'],
                    corner_radius=40,
                    width=70,
                    height=70
                )
                glow_outer.place(relx=0.5, rely=0.5, anchor="center")
                
                # Inner glow
                glow_inner = ctk.CTkFrame(
                    glow_outer,
                    fg_color=COLORS['glass'],
                    corner_radius=35,
                    width=60,
                    height=60
                )
                glow_inner.place(relx=0.5, rely=0.5, anchor="center")
                
                # Success icon
                success_icon = ctk.CTkLabel(
                    glow_inner,
                    text="✨",
                    font=("Segoe UI Emoji", 30),
                    text_color=COLORS['success']
                )
                success_icon.place(relx=0.5, rely=0.5, anchor="center")
                
                # Welcome message
                welcome_text = ctk.CTkLabel(
                    success_frame,
                    text=f"Welcome back, {username}!",
                    font=("Segoe UI", 16, "bold"),
                    text_color=COLORS['success']
                )
                welcome_text.grid(row=1, column=0, padx=30, pady=(0, 20))
                
                # Fade out overlay
                def fade_out(alpha=1.0):
                    if not self.loading_overlay.winfo_exists():
                        return
                    if alpha <= 0:
                        self.cleanup_animations()
                        self.switch_to_main(user)
                    else:
                        try:
                            self.loading_overlay.attributes('-alpha', alpha)
                        except:
                            pass
                        self.after(50, lambda: fade_out(alpha - 0.1))
                
                self.after(1000, lambda: fade_out())
                
        except Exception as e:
            logger.error(f"Error showing success animation: {e}")
            self.cleanup_animations()

    def handle_login_error(self, message: str):
        """Handle login error on main thread"""
        try:
            # Fade out overlay
            def fade_out(alpha=1.0):
                if not self.loading_overlay.winfo_exists():
                    return
                if alpha <= 0:
                    self.cleanup_animations()
                    self.set_inputs_state("normal")
                    self.show_validation_message(message, "error")
                    self.shake_form()
                    self.highlight_fields_error()
                else:
                    try:
                        self.loading_overlay.attributes('-alpha', alpha)
                    except:
                        pass
                    self.after(20, lambda: fade_out(alpha - 0.1))
            
            fade_out()
            
        except Exception as e:
            logger.error(f"Error handling login error: {e}")
            self.cleanup_animations()
            self.set_inputs_state("normal")

    def switch_to_main(self, user):
        """Switch to main application"""
        self.withdraw()
        app = MainApplication(user)
        app.mainloop()
        self.destroy()

class MainApplication(ctk.CTk):
    def __init__(self, user):
        super().__init__()
        
        self.user = user
        self.db = Database()
        
        # Configure window
        width, height = WindowManager.MAIN_SIZE
        WindowManager.setup_window(
            self,
            APP_NAME,
            width,
            height,
            resizable=(True, True)
        )
        
        # Configure grid weights for resizing
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)  # Column 1 will expand
        
        # Create main container with grid
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)  # Content area will expand
        
        # Create sidebar with grid
        self.create_sidebar()
        
        # Create main content area with grid
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Configure content frame grid weights
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Show dashboard by default
        self.show_dashboard()

    def create_sidebar(self):
        """Create sidebar with fixed width"""
        sidebar = ctk.CTkFrame(self.main_container, width=200)
        sidebar.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        sidebar.grid_propagate(False)  # Prevent sidebar from resizing
        
        # User info
        user_frame = ctk.CTkFrame(sidebar)
        user_frame.pack(fill="x", padx=5, pady=5)
        
        username_label = ctk.CTkLabel(user_frame, text=f"User: {self.user['username']}")
        username_label.pack(pady=5)
        
        role_label = ctk.CTkLabel(user_frame, text=f"Role: {self.user['role']}")
        role_label.pack(pady=5)
        
        # Navigation buttons
        ctk.CTkButton(sidebar, text="Dashboard", command=self.show_dashboard).pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(sidebar, text="Products", command=self.show_products).pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(sidebar, text="Sales", command=self.show_sales).pack(fill="x", padx=5, pady=5)
        
        if self.user['role'] == 'admin':
            ctk.CTkButton(sidebar, text="Users", command=self.show_users).pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(sidebar, text="Reports", command=self.show_reports).pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(sidebar, text="Settings", command=self.show_settings).pack(fill="x", padx=5, pady=5)
        
        # Logout button at bottom
        ctk.CTkButton(sidebar, text="Logout", command=self.logout).pack(fill="x", padx=5, pady=5, side="bottom")

    def clear_content(self):
        """Clear all widgets in content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        # Dashboard implementation will be in a separate file
        from views.dashboard import DashboardView
        DashboardView(self.content_frame, self.db)

    def show_products(self):
        self.clear_content()
        from views.products import ProductsView
        ProductsView(self.content_frame, self.db)

    def show_sales(self):
        self.clear_content()
        from views.sales import SalesView
        SalesView(self.content_frame, self.db)

    def show_users(self):
        if self.user['role'] != 'admin':
            messagebox.showerror("Error", "Access denied")
            return
        self.clear_content()
        from views.users import UsersView
        UsersView(self.content_frame, self.db)

    def show_reports(self):
        self.clear_content()
        from views.reports import ReportsView
        ReportsView(self.content_frame, self.db)

    def show_settings(self):
        self.clear_content()
        from views.settings import SettingsView
        SettingsView(self.content_frame, self.db)

    def logout(self):
        self.destroy()
        login = LoginWindow()
        login.mainloop()

    def animate_window_open(self, window):
        """Create a smooth fade-in animation for window opening"""
        try:
            # Store initial position
            x = window.winfo_x()
            y = window.winfo_y()
            
            # Start with 0 opacity
            window.attributes('-alpha', 0.0)
            
            def animate(opacity=0.0, offset=30):
                try:
                    if not window.winfo_exists():
                        return
                        
                    if opacity < 1.0:
                        opacity += 0.1
                        offset = int(offset * 0.7)  # Reduce offset each frame
                        
                        window.attributes('-alpha', opacity)
                        window.geometry(f"+{x}+{y-offset}")  # Slide up effect
                        
                        window.after(20, lambda: animate(opacity, offset))
                except Exception as e:
                    logger.warning(f"Animation frame failed: {e}")
            
            # Start animation
            animate()
            
        except Exception as e:
            logger.warning(f"Window animation failed: {e}")
            # Ensure window is visible even if animation fails
            try:
                window.attributes('-alpha', 1.0)
            except:
                pass

    def create_splash_screen(self):
        """Create and show splash screen"""
        splash = ctk.CTkToplevel()
        splash.title("Tea House Manager")
        splash.geometry("400x300")
        
        # Center splash screen
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 300) // 2
        splash.geometry(f"400x300+{x}+{y}")
        
        # Configure splash screen
        splash.configure(fg_color=COLORS['background'])
        splash.overrideredirect(True)  # Remove window decorations
        
        try:
            # Make splash screen appear on top
            splash.attributes('-topmost', True)
            
            # Remove from taskbar on Windows
            if os.name == 'nt':
                splash.attributes('-toolwindow', True)
        except Exception as e:
            logger.warning(f"Failed to set window attributes: {e}")
        
        # Create main container with elegant styling
        content_frame = ctk.CTkFrame(splash)
        content_frame.configure(
            fg_color=COLORS['surface'],
            border_width=1,
            border_color=COLORS['glass_border'],
            corner_radius=15
        )
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tea table themed icon with glowing effect
        icon_frame = ctk.CTkFrame(
            content_frame,
            fg_color=COLORS['primary'],
            corner_radius=40,
            width=80,
            height=80
        )
        icon_frame.pack(pady=(30, 15))
        
        # Inner glow
        inner_frame = ctk.CTkFrame(
            icon_frame,
            fg_color=COLORS['primary_dark'],
            corner_radius=35,
            width=70,
            height=70
        )
        inner_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Tea pot icon
        icon_label = ctk.CTkLabel(
            inner_frame,
            text="🫖",
            font=("Segoe UI Emoji", 35),
            text_color=COLORS['text']
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Decorative elements
        decor_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        decor_frame.pack(pady=5)
        
        # Tea cups decoration
        tea_items = [
            ("☕", COLORS['secondary']),
            ("🍵", COLORS['primary']),
            ("☕", COLORS['secondary'])
        ]
        
        for emoji, color in tea_items:
            ctk.CTkLabel(
                decor_frame,
                text=emoji,
                font=("Segoe UI Emoji", 20),
                text_color=color
            ).pack(side="left", padx=5)
        
        # App name with elegant styling
        title_label = ctk.CTkLabel(
            content_frame,
            text=APP_NAME,
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS['text']
        )
        title_label.pack(pady=(15, 5))
        
        subtitle_label = ctk.CTkLabel(
            content_frame,
            text="Your Perfect Tea House Management Solution",
            font=("Segoe UI", 12),
            text_color=COLORS['text_secondary']
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Progress bar with elegant styling
        progress_container = ctk.CTkFrame(
            content_frame,
            fg_color='transparent',
            corner_radius=10
        )
        progress_container.pack(pady=10, padx=30, fill="x")
        
        progress_bar = ctk.CTkProgressBar(progress_container)
        progress_bar.configure(
            mode="determinate",
            determinate_speed=0.5,
            height=6,
            corner_radius=3,
            fg_color=COLORS['glass'],
            progress_color=COLORS['primary']
        )
        progress_bar.pack(fill="x", padx=2)
        progress_bar.set(0)
        
        # Status message with elegant styling
        status_label = ctk.CTkLabel(
            content_frame,
            text="Preparing your tea house...",
            font=("Segoe UI", 12),
            text_color=COLORS['text_secondary']
        )
        status_label.pack(pady=10)
        
        return splash, progress_bar, status_label

    def cleanup(self):
        """Clean up resources before exit"""
        try:
            if hasattr(self, 'db'):
                self.db.disconnect()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

class WindowManager:
    """Handles window dimensions and positioning"""
    
    # Window size constants
    LOGIN_SIZE = (450, 650)      # Adjusted login window size to match image
    REGISTER_SIZE = (450, 650)   # Adjusted registration window size
    MAIN_SIZE = (1200, 700)      # Main window size
    SPLASH_SIZE = (400, 300)     # Splash screen size
    
    # Minimum window sizes
    MIN_MAIN_WIDTH = 800
    MIN_MAIN_HEIGHT = 500
    
    # Use global color scheme
    COLORS = COLORS
    
    @staticmethod
    def center_window(window, width, height):
        """Center a window on the screen"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    @staticmethod
    def setup_window(window, title, width, height, resizable=(True, True)):
        """Set up window properties"""
        window.title(title)
        WindowManager.center_window(window, width, height)
        window.resizable(resizable[0], resizable[1])
        
        # Set minimum size for main window
        if isinstance(window, MainApplication):
            window.minsize(WindowManager.MIN_MAIN_WIDTH, WindowManager.MIN_MAIN_HEIGHT)
        
        window.configure(fg_color=WindowManager.COLORS['background'])
        
        # Add window state tracking
        if resizable[0] and resizable[1]:
            window._last_valid_size = (width, height)
            
            def on_resize(event):
                """Track window size changes"""
                if event.width >= WindowManager.MIN_MAIN_WIDTH and event.height >= WindowManager.MIN_MAIN_HEIGHT:
                    window._last_valid_size = (event.width, event.height)
            
            window.bind('<Configure>', on_resize)

class Application:
    def __init__(self):
        # Initialize root window for DPI calculations
        self._root = tk.Tk()
        self._root.withdraw()
        
        try:
            # Set up theme and scaling
            self.setup_application()
            
            # Initialize database
            self.db = Database()
            
            # Ensure database is initialized
            self.ensure_database_setup()
            
            # Start application
            self.start_application()
            
        finally:
            # Clean up root window
            if hasattr(self, '_root'):
                self._root.destroy()
    
    def setup_application(self):
        """Configure application settings"""
        try:
            # Set appearance mode and theme
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            
            # Fix DPI scaling for Windows
            if os.name == 'nt':
                try:
                    from ctypes import windll
                    windll.shcore.SetProcessDpiAwareness(1)
                except Exception as e:
                    logger.warning(f"Failed to set DPI awareness: {e}")
            
            # Calculate scaling based on screen properties
            dpi = self._root.winfo_fpixels('1i') / 72.0
            screen_height = self._root.winfo_screenheight()
            
            # Set widget scaling based on DPI
            widget_scaling = dpi / (96.0 / 72.0)
            ctk.set_widget_scaling(widget_scaling)
            
            # Set window scaling based on screen height
            window_scaling = 1.0
            if screen_height > 2000:  # 4K displays
                window_scaling = 2.0
            elif screen_height > 1400:  # QHD displays
                window_scaling = 1.5
            
            ctk.set_window_scaling(window_scaling)
            
        except Exception as e:
            logger.warning(f"Failed to setup application: {e}")
            # Use default scaling if setup fails
            ctk.set_widget_scaling(1.0)
            ctk.set_window_scaling(1.0)
    
    def ensure_database_setup(self):
        """Ensure database is properly set up"""
        try:
            # Test connection
            if not self.db.test_connection():
                raise Exception("Could not connect to database")
            
            # Ensure tables exist by checking users table
            result = self.db.execute_query("SHOW TABLES LIKE 'users'")
            if not result:
                # Initialize database schema
                from setup import initialize_database
                if not initialize_database():
                    raise Exception("Failed to initialize database schema")
            
            # Ensure admin user exists
            if not self.db.ensure_admin_exists():
                raise Exception("Failed to create admin user")
                
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            self.show_error(str(e))
            sys.exit(1)
    
    def create_splash_screen(self):
        """Create and show splash screen"""
        splash = ctk.CTkToplevel()
        splash.title("Tea House Manager")
        splash.geometry("400x300")
        
        # Center splash screen
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 300) // 2
        splash.geometry(f"400x300+{x}+{y}")
        
        # Configure splash screen
        splash.configure(fg_color=COLORS['background'])
        splash.overrideredirect(True)  # Remove window decorations
        
        try:
            # Make splash screen appear on top
            splash.attributes('-topmost', True)
            
            # Remove from taskbar on Windows
            if os.name == 'nt':
                splash.attributes('-toolwindow', True)
        except Exception as e:
            logger.warning(f"Failed to set window attributes: {e}")
        
        # Create main container with elegant styling
        content_frame = ctk.CTkFrame(splash)
        content_frame.configure(
            fg_color=COLORS['surface'],
            border_width=1,
            border_color=COLORS['glass_border'],
            corner_radius=15
        )
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tea table themed icon with glowing effect
        icon_frame = ctk.CTkFrame(
            content_frame,
            fg_color=COLORS['primary'],
            corner_radius=40,
            width=80,
            height=80
        )
        icon_frame.pack(pady=(30, 15))
        
        # Inner glow
        inner_frame = ctk.CTkFrame(
            icon_frame,
            fg_color=COLORS['primary_dark'],
            corner_radius=35,
            width=70,
            height=70
        )
        inner_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Tea pot icon
        icon_label = ctk.CTkLabel(
            inner_frame,
            text="🫖",
            font=("Segoe UI Emoji", 35),
            text_color=COLORS['text']
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Decorative elements
        decor_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        decor_frame.pack(pady=5)
        
        # Tea cups decoration
        tea_items = [
            ("☕", COLORS['secondary']),
            ("🍵", COLORS['primary']),
            ("☕", COLORS['secondary'])
        ]
        
        for emoji, color in tea_items:
            ctk.CTkLabel(
                decor_frame,
                text=emoji,
                font=("Segoe UI Emoji", 20),
                text_color=color
            ).pack(side="left", padx=5)
        
        # App name with elegant styling
        title_label = ctk.CTkLabel(
            content_frame,
            text=APP_NAME,
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS['text']
        )
        title_label.pack(pady=(15, 5))
        
        subtitle_label = ctk.CTkLabel(
            content_frame,
            text="Your Perfect Tea House Management Solution",
            font=("Segoe UI", 12),
            text_color=COLORS['text_secondary']
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Progress bar with elegant styling
        progress_container = ctk.CTkFrame(
            content_frame,
            fg_color='transparent',
            corner_radius=10
        )
        progress_container.pack(pady=10, padx=30, fill="x")
        
        progress_bar = ctk.CTkProgressBar(progress_container)
        progress_bar.configure(
            mode="determinate",
            determinate_speed=0.5,
            height=6,
            corner_radius=3,
            fg_color=COLORS['glass'],
            progress_color=COLORS['primary']
        )
        progress_bar.pack(fill="x", padx=2)
        progress_bar.set(0)
        
        # Status message with elegant styling
        status_label = ctk.CTkLabel(
            content_frame,
            text="Preparing your tea house...",
            font=("Segoe UI", 12),
            text_color=COLORS['text_secondary']
        )
        status_label.pack(pady=10)
        
        return splash, progress_bar, status_label
    
    def start_application(self):
        """Start the application with splash screen"""
        try:
            # Create and configure the main root window
            self.root = ctk.CTk()
            self.root.withdraw()
            
            # Create splash screen as child of root
            splash, progress_bar, status_label = self.create_splash_screen()
            splash.transient(self.root)  # Make splash screen transient to root
            
            def update_progress(percent, message):
                """Update progress bar and status safely"""
                try:
                    if splash.winfo_exists():
                        progress_bar.set(percent / 100)
                        status_label.configure(text=message)
                        splash.update_idletasks()
                except Exception:
                    pass
            
            def show_login():
                """Show login window safely"""
                try:
                    if not splash.winfo_exists():
                        return
                    
                    # Create login window
                    login_window = LoginWindow()
                    
                    def on_login_close():
                        """Handle login window close"""
                        login_window.destroy()
                        self.root.quit()
                    
                    # Set up close handler
                    login_window.protocol("WM_DELETE_WINDOW", on_login_close)
                    
                    # Clean up splash screen
                    splash.destroy()
                    
                    # Show login window
                    login_window.deiconify()
                    login_window.focus_force()
                    
                except Exception as e:
                    logger.error(f"Failed to show login window: {e}")
                    self.show_error(str(e))
                    if splash.winfo_exists():
                        splash.destroy()
                    self.root.quit()
            
            # Initialize components with progress
            update_progress(20, "Preparing your tea house...")
            self.root.update_idletasks()
            
            # Test database connection
            update_progress(40, "Connecting to database...")
            self.root.update_idletasks()
            if not self.db.test_connection():
                raise Exception("Could not connect to database")
            
            # Load configuration
            update_progress(60, "Loading settings...")
            self.root.update_idletasks()
            
            # Initialize UI
            update_progress(80, "Setting up your tea house...")
            self.root.update_idletasks()
            
            # Complete startup
            update_progress(100, "Welcome to your tea house!")
            self.root.update_idletasks()
            
            # Schedule login window creation
            self.root.after(1000, show_login)
            
            # Start main event loop
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            self.show_error(str(e))
            
        finally:
            # Ensure cleanup
            self.cleanup()

    def show_error(self, message):
        """Show error message with enhanced styling"""
        error_window = ctk.CTk()
        error_window.withdraw()
        
        # Create main container
        error_container = ctk.CTkFrame(error_window)
        error_container.configure(fg_color=COLORS['surface'])
        error_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Configure grid weights
        error_window.grid_rowconfigure(0, weight=1)
        error_window.grid_columnconfigure(0, weight=1)
        error_container.grid_rowconfigure(0, weight=1)
        error_container.grid_columnconfigure(0, weight=1)
        
        error_msg = (
            f"Failed to start application: {message}\n\n"
            "Please check:\n"
            "1. Database connection settings\n"
            "2. Required tables exist\n"
            "3. MySQL service is running"
        )
        
        # Create error message label
        error_label = ctk.CTkLabel(
            error_container,
            text=error_msg,
            font=("Segoe UI", 12),
            text_color=COLORS['error'],
            justify="left",
            wraplength=300
        )
        error_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Show window
        error_window.deiconify()
        error_window.mainloop()

if __name__ == "__main__":
    try:
        # Set up theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Fix DPI awareness for Windows
        if os.name == 'nt':
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception as e:
                logger.warning(f"Failed to set DPI awareness: {e}")
        
        # Initialize database
        db = Database()
        if not db.test_connection():
            raise Exception("Could not connect to database")
            
        # Ensure database is set up
        result = db.execute_query("SHOW TABLES LIKE 'users'")
        if not result:
            # Initialize database schema
            from setup import initialize_database
            if not initialize_database():
                raise Exception("Failed to initialize database schema")
        
        # Ensure admin user exists
        if not db.ensure_admin_exists():
            raise Exception("Failed to create admin user")
        
        # Create and show login window
        login_window = LoginWindow()
        login_window.mainloop()
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")
        sys.exit(1) 