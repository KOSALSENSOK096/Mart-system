import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
import customtkinter as ctk
from datetime import datetime
import os
import time
from .styles import COLORS, FONTS, apply_button_style, apply_frame_style, apply_entry_style

class BarcodeManager:
    def __init__(self):
        self.barcode_dir = "barcode_images"
        os.makedirs(self.barcode_dir, exist_ok=True)
        
    def generate_barcode(self, product_code, product_name=None):
        """Generate a barcode image for a product with enhanced styling"""
        try:
            # Create Code128 barcode with custom options for better visuals
            options = {
                'module_height': 15.0,     # Taller bars
                'module_width': 0.3,       # Thicker bars
                'quiet_zone': 6.0,         # Wider quiet zone
                'font_size': 12,           # Larger text
                'text_distance': 5.0,      # Space between bars and text
                'background': 'white',
                'foreground': 'black',
                'write_text': True,
                'text': f"{product_code}"  # Add text below barcode
            }
            code128 = barcode.get('code128', product_code, writer=ImageWriter())
            for key, value in options.items():
                setattr(code128.writer, key, value)
            
            # Generate filename using product code and name
            filename = f"{product_code}"
            if product_name:
                clean_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_'))
                filename = f"{product_code}_{clean_name}"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_filename = os.path.join(self.barcode_dir, f"{filename}_{timestamp}")
            
            return code128.save(full_filename)
        except Exception as e:
            raise Exception(f"Failed to generate barcode: {str(e)}")

class BarcodeScannerWindow(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        
        self.title("🔍 Barcode Entry")
        self.geometry("600x400")
        
        # Center window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 400) // 2
        self.geometry(f"600x400+{x}+{y}")
        
        # Configure window background
        self.configure(fg_color=COLORS['background'])
        
        self.callback = callback
        self.parent = parent
        self.setup_ui()
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
        
        # Wait for window to be ready
        self.update_idletasks()
        
    def setup_ui(self):
        # Main container with gradient effect
        self.main_frame = ctk.CTkFrame(self)
        apply_frame_style(self.main_frame, 'card')
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Modern header with gradient
        header_frame = ctk.CTkFrame(self.main_frame)
        apply_frame_style(header_frame, 'card')
        header_frame.pack(padx=10, pady=10, fill="x")
        
        # Title with icon
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(pady=10)
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="🔍 Quick Barcode Entry",
            font=FONTS['heading1'],
            text_color=COLORS['text']
        )
        self.title_label.pack()
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="✨ Enter barcode manually ✨",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        )
        subtitle.pack()
        
        # Modern input section
        input_frame = ctk.CTkFrame(self.main_frame)
        apply_frame_style(input_frame, 'card')
        input_frame.pack(padx=10, pady=10, fill="x")
        
        # Modern entry field
        self.entry = ctk.CTkEntry(
            input_frame,
            font=FONTS['body'],
            placeholder_text="✨ Type barcode here...",
            height=45,
            border_width=2
        )
        apply_entry_style(self.entry)
        self.entry.pack(padx=20, pady=20, fill="x")
        self.entry.bind("<Return>", self.on_manual_entry)
        
        # Submit button
        self.submit_btn = ctk.CTkButton(
            input_frame,
            text="✅ Submit Barcode",
            command=self.on_manual_entry,
            width=200,
            height=45,
            corner_radius=10
        )
        apply_button_style(self.submit_btn, 'primary')
        self.submit_btn.pack(pady=10)
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(self.main_frame)
        apply_frame_style(self.status_frame, 'card')
        self.status_frame.pack(padx=10, pady=10, fill="x")
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="⌨️ Ready for input",
            font=FONTS['body_bold'],
            text_color=COLORS['text_secondary']
        )
        self.status_label.pack(pady=10)
        
        # Close button
        self.close_btn = ctk.CTkButton(
            self.main_frame,
            text="✖️ Close",
            command=self.close_window,
            width=200,
            height=45,
            corner_radius=10
        )
        apply_button_style(self.close_btn, 'outline')
        self.close_btn.pack(pady=10)
        
        # Focus entry
        self.entry.focus_set()
    
    def on_manual_entry(self, event=None):
        code = self.entry.get().strip()
        if code:
            # Visual feedback
            apply_entry_style(self.entry)
            self.status_label.configure(
                text=f"✅ Processed: {code}",
                text_color=COLORS['success']
            )
            
            # Process the code
            self.callback(code)
            
            # Clear entry
            self.entry.delete(0, "end")
            
            # Reset visual feedback after delay
            def reset_feedback():
                apply_entry_style(self.entry)
                self.status_label.configure(
                    text="⌨️ Ready for input",
                    text_color=COLORS['text_secondary']
                )
            
            self.after(2000, reset_feedback)
            
            # Focus entry again
            self.entry.focus_set()
    
    def close_window(self):
        self.destroy()

def create_barcode_scanner(parent, callback):
    """Create and show a barcode scanner window"""
    scanner = BarcodeScannerWindow(parent, callback)
    scanner.grab_set()  # Make window modal
    return scanner 