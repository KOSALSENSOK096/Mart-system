import customtkinter as ctk
from tkinter import ttk, messagebox
import pandas as pd
from tkinter import filedialog
from utils.database import Database
from utils.styles import (
    COLORS, FONTS, ICONS,
    apply_frame_style, apply_button_style,
    apply_entry_style, apply_option_menu_style,
    apply_tooltip
)
from utils.barcode_utils import BarcodeManager, create_barcode_scanner
from PIL import Image
import tkinter as tk
import barcode
from customtkinter import CTkImage
from barcode.writer import ImageWriter
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

class ProductsView(ctk.CTkFrame):
    def __init__(self, parent, db: Database):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.barcode_manager = BarcodeManager()
        self.temp_dir = tempfile.mkdtemp()  # Create temp directory for barcodes
        
        # Initialize status label first
        self.status_frame = ctk.CTkFrame(self)
        apply_frame_style(self.status_frame, 'card')
        self.status_frame.pack(fill="x", padx=20, pady=(20, 0))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=FONTS['body'],
            text_color=COLORS['text']
        )
        self.status_label.pack(pady=10)
        
        # Pack the main frame
        self.pack(fill="both", expand=True)
        
        # Create other widgets
        self.create_widgets()
        self.load_products()

    def create_widgets(self):
        # Main container with card style
        self.main_frame = ctk.CTkFrame(self)
        apply_frame_style(self.main_frame, 'card')
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Header with actions
        header_frame = ctk.CTkFrame(self.main_frame)
        apply_frame_style(header_frame)
        header_frame.pack(padx=10, pady=10, fill="x")
        
        # Title
        title = ctk.CTkLabel(
            header_frame,
            text="Products Management",
            font=FONTS['heading1'],
            text_color=COLORS['primary']
        )
        title.pack(side="left", padx=10)
        
        # Scan barcode button
        scan_btn = ctk.CTkButton(
            header_frame,
            text="Scan Barcode",
            command=self.show_scanner
        )
        apply_button_style(scan_btn, 'primary')
        scan_btn.pack(side="right", padx=5)
        
        # Add product button
        add_btn = ctk.CTkButton(
            header_frame,
            text="Add Product",
            command=self.show_product_dialog
        )
        apply_button_style(add_btn, 'secondary')
        add_btn.pack(side="right", padx=5)
        
        # Search frame
        search_frame = ctk.CTkFrame(self.main_frame)
        apply_frame_style(search_frame)
        search_frame.pack(padx=10, pady=10, fill="x")
        
        search_label = ctk.CTkLabel(
            search_frame,
            text="Search Products:",
            font=FONTS['body_bold']
        )
        search_label.pack(side="left", padx=10)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.load_products())
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Enter product name or barcode",
            font=FONTS['body'],
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", padx=10, fill="x", expand=True)
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="Search",
            command=self.search_products
        )
        apply_button_style(search_btn, 'primary')
        search_btn.pack(side="right", padx=5)
        
        # Products list frame
        list_frame = ctk.CTkFrame(self.main_frame)
        apply_frame_style(list_frame)
        list_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Create Treeview
        columns = ("ID", "Name", "Category", "Price", "Stock", "Min Stock")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_double_click)

    def load_products(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get products from database
        search_term = self.search_var.get()
        products = self.db.get_products(search_term if search_term else None)
        
        # Insert products into tree
        for product in products:
            self.tree.insert("", "end", values=(
                product['id'],
                product['name'],
                product['category_name'] or "No Category",
                f"${product['price']:.2f}",
                product['stock'],
                product['min_stock']
            ))

    def show_product_dialog(self, product=None):
        dialog = ProductDialog(self.parent, self.db, product)
        self.parent.wait_window(dialog)
        self.load_products()

    def on_double_click(self, event):
        """Handle double click on product row"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.tree.item(item)['values']
        if not values:
            return
            
        # Get full product details from database
        query = """
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s AND p.is_active = TRUE
        """
        result = self.db.execute_query(query, (values[0],))
        if result and len(result) > 0:
            self.show_product_details(result[0])
        else:
            messagebox.showerror("Error", "Product not found or inactive")

    def show_scanner(self):
        """Show barcode scanner window with enhanced UI"""
        def on_barcode_scanned(code):
            try:
                # Show loading animation in status bar
                self.update_status(f"🔍 Scanning barcode: {code}...", "info")
                
                # Query database for product
                product = self.get_product_by_barcode(code)
                
                if product:
                    self.update_status(f"✅ Found product: {product['name']}", "success")
                    # Small delay to ensure proper window management and show success message
                    self.after(800, lambda: self.show_product_details(product))
                else:
                    self.update_status("❌ Product not found", "warning")
                    # Small delay for user to read the message
                    self.after(800, lambda: self.handle_new_product(code))
                    
            except Exception as e:
                self.update_status(f"❌ Error: {str(e)}", "error")
                messagebox.showerror("Error", f"Failed to process barcode: {str(e)}")
        
        create_barcode_scanner(self.parent, on_barcode_scanned)
    
    def update_status(self, message, status_type="info"):
        """Update status message with appropriate styling"""
        if not hasattr(self, 'status_label') or not self.status_label.winfo_exists():
            return
            
        colors = {
            "info": COLORS['primary'],
            "success": COLORS['success'],
            "warning": COLORS['warning'],
            "error": COLORS['error']  # Use error color for error states
        }
        
        try:
            self.status_label.configure(
                text=message,
                text_color=colors.get(status_type, COLORS['text'])
            )
            self.status_frame.lift()  # Ensure status is visible
            
            # Clear status after delay for success/info messages
            if status_type in ['success', 'info']:
                self.after(3000, lambda: self.status_label.configure(text=""))
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
    
    def handle_new_product(self, barcode):
        """Handle new product creation from barcode with enhanced UI"""
        if messagebox.askyesno(
            "Add New Product",
            f"✨ Would you like to add a new product with barcode {barcode}?\n\n"
            "This will open the product creation form with the barcode pre-filled.",
            icon="question"
        ):
            self.show_add_product_dialog(barcode)
    
    def show_add_product_dialog(self, barcode=None):
        """Show enhanced add product dialog"""
        dialog = ProductDialog(self.parent, self.db, None)
        
        if barcode:
            # Pre-fill barcode if provided
            dialog.barcode_entry.insert(0, barcode)
            dialog.barcode_entry.configure(state="disabled")  # Lock barcode field
            
            # Show success message
            dialog.show_message(
                "✨ Barcode pre-filled automatically",
                "success"
            )
        
        self.parent.wait_window(dialog)
        self.load_products()
        
        # Show success message in main window
        if barcode:
            self.update_status("✅ New product added successfully!", "success")
    
    def get_product_by_barcode(self, barcode):
        """Query database for product by barcode"""
        try:
            query = """
                SELECT id, name, price, stock, barcode, category_id 
                FROM products 
                WHERE barcode = %s
            """
            result = self.db.execute_query(query, (barcode,))
            
            if result and len(result) > 0:
                product = result[0]  # Get first result
                return {
                    'id': product['id'],
                    'name': product['name'],
                    'price': product['price'],
                    'stock': product['stock'],
                    'barcode': product['barcode'],
                    'category_id': product['category_id']
                }
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch product: {str(e)}")
            return None
    
    def show_product_details(self, product):
        """Show product details with enhanced barcode display"""
        if not isinstance(product, dict):
            messagebox.showerror("Error", "Invalid product data")
            return
            
        details_window = ctk.CTkToplevel()
        details_window.title("✨ Product Details")
        details_window.geometry("600x800")
        details_window.grab_set()
        
        # Center window on screen
        details_window.update_idletasks()  # Update window size
        width = 600  # Window width
        height = 800  # Window height
        screen_width = details_window.winfo_screenwidth()
        screen_height = details_window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        details_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configure window
        details_window.configure(fg_color=COLORS['background'])
        
        # Main container with card style
        main_frame = ctk.CTkFrame(details_window)
        apply_frame_style(main_frame, 'card')
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Header with product name and icon
        header_frame = ctk.CTkFrame(main_frame)
        apply_frame_style(header_frame)
        header_frame.pack(padx=10, pady=10, fill="x")
        
        # Product icon
        icon_label = ctk.CTkLabel(
            header_frame,
            text="📦",
            font=("Helvetica", 48),
            text_color=COLORS['primary']
        )
        icon_label.pack(pady=(10, 0))
        
        # Product name
        name_label = ctk.CTkLabel(
            header_frame,
            text=product.get('name', 'N/A'),
            font=FONTS['heading1'],
            text_color=COLORS['text']
        )
        name_label.pack(pady=5)
        
        # Category label
        category_label = ctk.CTkLabel(
            header_frame,
            text=f"🏷️ {product.get('category_name', 'No Category')}",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        )
        category_label.pack(pady=(0, 10))
        
        # Product info in scrollable frame with card style
        info_frame = ctk.CTkScrollableFrame(main_frame)
        info_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Key metrics in a grid
        metrics_frame = ctk.CTkFrame(info_frame)
        apply_frame_style(metrics_frame, 'card')
        metrics_frame.pack(fill="x", pady=10, padx=10)
        
        # Create a grid for metrics
        grid_frame = ctk.CTkFrame(metrics_frame, fg_color="transparent")
        grid_frame.pack(pady=10, padx=10)
        
        metrics = [
            ("💰", "Price", f"${float(product.get('price', 0)):.2f}"),
            ("📦", "Stock", str(product.get('stock', 0))),
            ("📉", "Min Stock", str(product.get('min_stock', 0))),
            ("📈", "Max Stock", str(product.get('max_stock', 0)))
        ]
        
        for i, (icon, label, value) in enumerate(metrics):
            # Metric card
            metric_card = ctk.CTkFrame(grid_frame)
            apply_frame_style(metric_card, 'card')
            metric_card.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="nsew")
            
            # Icon
            ctk.CTkLabel(
                metric_card,
                text=icon,
                font=("Helvetica", 24),
                text_color=COLORS['primary']
            ).pack(pady=(10, 0))
            
            # Label
            ctk.CTkLabel(
                metric_card,
                text=label,
                font=FONTS['body'],
                text_color=COLORS['text_secondary']
            ).pack()
            
            # Value
            ctk.CTkLabel(
                metric_card,
                text=value,
                font=FONTS['heading3'],
                text_color=COLORS['text']
            ).pack(pady=(0, 10))
        
        # Description section
        if product.get('description'):
            desc_frame = ctk.CTkFrame(info_frame)
            apply_frame_style(desc_frame, 'card')
            desc_frame.pack(fill="x", pady=10, padx=10)
            
            # Description label
            desc_label = ctk.CTkLabel(
                desc_frame,
                text="📝 Description",
                font=FONTS['heading3'],
                text_color=COLORS['text']
            )
            desc_label.pack(pady=(10, 5), padx=10)
            
            desc_text = ctk.CTkTextbox(
                desc_frame,
                height=100,
                wrap="word",
                font=FONTS['body']
            )
            apply_entry_style(desc_text)
            desc_text.pack(pady=10, padx=10, fill="x")
            desc_text.insert("1.0", product.get('description', ''))
            desc_text.configure(state="disabled")
        
        # Barcode section with enhanced styling
        if product.get('barcode'):
            try:
                # Create barcode frame with special styling
                barcode_frame = ctk.CTkFrame(info_frame)
                barcode_frame.pack(pady=10, padx=10, fill="x")
                
                # Barcode header with icon
                header_frame = ctk.CTkFrame(barcode_frame, fg_color="transparent")
                header_frame.pack(fill="x", pady=(10, 5))
                
                icon_label = ctk.CTkLabel(
                    header_frame,
                    text="🔍",
                    font=("Helvetica", 32),
                    text_color=COLORS['primary']
                )
                icon_label.pack(side="left", padx=10)
                
                header = ctk.CTkLabel(
                    header_frame,
                    text="Product Barcode",
                    font=FONTS['heading2'],
                    text_color=COLORS['text']
                )
                header.pack(side="left")
                
                # Generate and display barcode
                barcode_image = self.generate_barcode(product['barcode'])
                if barcode_image:
                    # Barcode container with border
                    barcode_container = ctk.CTkFrame(barcode_frame)
                    apply_frame_style(barcode_container, 'card')
                    barcode_container.pack(pady=10, padx=20, fill="x")
                    
                    barcode_label = ctk.CTkLabel(
                        barcode_container,
                        image=barcode_image,
                        text=""
                    )
                    barcode_label.image = barcode_image
                    barcode_label.pack(pady=20)
                    
                    # Barcode number with copy button in a styled frame
                    code_frame = ctk.CTkFrame(barcode_frame)
                    apply_frame_style(code_frame)
                    code_frame.pack(pady=(0, 10), padx=20, fill="x")
                    
                    code_label = ctk.CTkLabel(
                        code_frame,
                        text=f"Code: {product['barcode']}",
                        font=FONTS['body_bold'],
                        text_color=COLORS['text']
                    )
                    code_label.pack(side="left", padx=10, pady=10)
                    
                    # Copy button with tooltip
                    copy_btn = ctk.CTkButton(
                        code_frame,
                        text="📋 Copy Code",
                        width=120,
                        height=32,
                        command=lambda: self.copy_to_clipboard(product['barcode'])
                    )
                    apply_button_style(copy_btn, 'primary')
                    apply_tooltip(copy_btn, "Copy barcode to clipboard")
                    copy_btn.pack(side="right", padx=10, pady=5)
                    
            except Exception as e:
                logger.error(f"Failed to generate barcode: {e}")
        
        # Action buttons with enhanced styling
        button_frame = ctk.CTkFrame(main_frame)
        apply_frame_style(button_frame, 'card')
        button_frame.pack(fill="x", pady=10, padx=10)
        
        # Edit button with icon and tooltip
        edit_btn = ctk.CTkButton(
            button_frame,
            text="✏️ Edit Product",
            command=lambda: self.show_edit_product(product, details_window),
            height=40
        )
        apply_button_style(edit_btn, 'primary')
        apply_tooltip(edit_btn, "Edit product details")
        edit_btn.pack(side="left", padx=10, pady=10, expand=True)
        
        # Delete button with icon and tooltip
        delete_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Delete Product",
            command=lambda: self.delete_product(product['id'], details_window),
            height=40
        )
        apply_button_style(delete_btn, 'danger')
        apply_tooltip(delete_btn, "Delete this product")
        delete_btn.pack(side="left", padx=10, pady=10, expand=True)
        
        # Close button with icon and tooltip
        close_btn = ctk.CTkButton(
            button_frame,
            text="✖️ Close",
            command=details_window.destroy,
            height=40
        )
        apply_button_style(close_btn, 'secondary')
        apply_tooltip(close_btn, "Close this window")
        close_btn.pack(side="left", padx=10, pady=10, expand=True)
        
        # Add window animations
        self.animate_window_open(details_window)
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard with feedback"""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_status("📋 Copied to clipboard!", "success")

    def add_product(self, barcode=None):
        """Show add product form"""
        # Implement add product functionality
        pass
    
    def show_edit_product(self, product, details_window):
        """Show edit product form"""
        # Implement edit product functionality
        pass
    
    def delete_product(self, product_id, details_window):
        """Delete product from database"""
        if not messagebox.askyesno("Confirm Delete", 
                                 "Are you sure you want to delete this product?"):
            return
        
        if self.db.delete_product(product_id):
            messagebox.showinfo("Success", "Product deleted successfully")
            details_window.destroy()
        else:
            messagebox.showerror("Error", "Failed to delete product")

    def search_products(self):
        """Search products by name or barcode"""
        # Implement search functionality
        pass

    def import_csv(self):
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filename:
            return
        
        try:
            df = pd.read_csv(filename)
            required_columns = ['name', 'price', 'stock', 'category_id']
            
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("Error", 
                    "CSV must contain columns: name, price, stock, category_id")
                return
            
            success_count = 0
            for _, row in df.iterrows():
                if self.db.add_product(row.to_dict()):
                    success_count += 1
            
            messagebox.showinfo("Success", 
                f"Successfully imported {success_count} products")
            self.load_products()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import CSV: {str(e)}")

    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filename:
            return
        
        try:
            products = self.db.get_products()
            df = pd.DataFrame(products)
            df.to_csv(filename, index=False)
            messagebox.showinfo("Success", "Products exported successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")

    def generate_barcode(self, barcode_data):
        """Generate a stylish barcode image"""
        try:
            if not barcode_data:
                return None

            # Create white background
            bg_color = (255, 255, 255)
            padding = 20
            
            # Create EAN13 barcode with custom options
            options = {
                'module_height': 15.0,  # Taller bars
                'module_width': 0.35,   # Thicker bars
                'quiet_zone': 6.5,      # Wider quiet zone
                'font_size': 12,        # Larger text
                'text_distance': 5,     # Text closer to bars
                'background': bg_color
            }
            
            ean = barcode.get('ean13', barcode_data, writer=ImageWriter())
            
            # Save to temp file with custom options
            filename = os.path.join(self.temp_dir, f"barcode_{barcode_data}")
            ean.save(filename, options)
            
            # Open the image
            image = Image.open(f"{filename}.png")
            
            # Create new image with padding
            new_width = image.width + (2 * padding)
            new_height = image.height + (2 * padding)
            padded_image = Image.new('RGB', (new_width, new_height), bg_color)
            
            # Paste original image in center
            x = padding
            y = padding
            padded_image.paste(image, (x, y))
            
            # Resize for display while maintaining aspect ratio
            display_width = 300
            aspect_ratio = padded_image.width / padded_image.height
            display_height = int(display_width / aspect_ratio)
            
            resized_image = padded_image.resize(
                (display_width, display_height), 
                Image.Resampling.LANCZOS
            )
            
            # Create CTkImage for both light and dark themes
            return CTkImage(
                light_image=resized_image,
                dark_image=resized_image,
                size=(display_width, display_height)
            )
            
        except Exception as e:
            logger.error(f"Barcode generation error: {e}")
            messagebox.showerror("Error", f"Failed to generate barcode: {str(e)}")
            return None

    def animate_window_open(self, window):
        """Create a smooth fade-in animation for window opening"""
        # Store initial position
        x = window.winfo_x()
        y = window.winfo_y()
        
        # Start with 0 opacity
        window.attributes('-alpha', 0.0)
        
        # Animate opacity and position
        def animate(opacity=0.0, offset=30):
            if opacity < 1.0:
                opacity += 0.1
                offset = int(offset * 0.7)  # Reduce offset each frame
                
                window.attributes('-alpha', opacity)
                window.geometry(f"+{x}+{y-offset}")  # Slide up effect
                
                window.after(20, lambda: animate(opacity, offset))
        
        # Start animation
        animate()

    def __del__(self):
        """Cleanup temporary files"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass

class ProductDialog(ctk.CTkToplevel):
    def __init__(self, parent, db: Database, product=None):
        super().__init__(parent)
        
        self.db = db
        self.product = product
        
        self.title("✏️ Edit Product" if product else "✨ Add New Product")
        self.geometry("500x700")
        
        # Center window
        self.center_window()
        
        # Make window modal
        self.grab_set()
        
        # Create widgets
        self.create_widgets()
        
        # Load product data if editing
        if product:
            self.load_product_data()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def show_message(self, message, message_type="info"):
        """Show a message in the status bar"""
        if not hasattr(self, 'message_label'):
            self.message_frame = ctk.CTkFrame(self.main_frame)
            self.message_frame.pack(fill="x", pady=(0, 10))
            
            self.message_label = ctk.CTkLabel(
                self.message_frame,
                text="",
                font=FONTS['body']
            )
            self.message_label.pack(pady=5)
        
        colors = {
            "info": COLORS['primary'],
            "success": COLORS['success'],
            "warning": COLORS['warning'],
            "error": COLORS['error']
        }
        
        self.message_label.configure(
            text=message,
            text_color=colors.get(message_type, COLORS['text'])
        )
        
        # Auto-hide success/info messages
        if message_type in ['success', 'info']:
            self.after(3000, lambda: self.message_label.configure(text=""))

    def create_widgets(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        apply_frame_style(self.main_frame, 'card')
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Title
        title = ctk.CTkLabel(
            self.main_frame,
            text="✏️ Edit Product" if self.product else "✨ Add New Product",
            font=FONTS['heading1'],
            text_color=COLORS['primary']
        )
        title.pack(pady=(10, 20))
        
        # Form fields in scrollable frame
        form_frame = ctk.CTkScrollableFrame(self.main_frame)
        form_frame.pack(fill="both", expand=True, padx=10)
        
        # Product fields with icons
        self.create_field(form_frame, "📝 Name:", "name_entry")
        self.create_field(form_frame, "💬 Description:", "desc_entry", is_multiline=True)
        self.create_field(form_frame, "💰 Price:", "price_entry")
        self.create_field(form_frame, "📦 Stock:", "stock_entry")
        self.create_field(form_frame, "📊 Min Stock:", "min_stock_entry")
        self.create_field(form_frame, "📈 Max Stock:", "max_stock_entry")
        self.create_field(form_frame, "🔢 Barcode:", "barcode_entry")
        
        # Category dropdown
        category_frame = ctk.CTkFrame(form_frame)
        category_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            category_frame,
            text="🏷️ Category:",
            font=FONTS['body_bold']
        ).pack(side="left", padx=5)
        
        categories = self.db.get_categories()
        self.category_var = ctk.StringVar()
        self.category_dropdown = ctk.CTkOptionMenu(
            category_frame,
            variable=self.category_var,
            values=[cat['name'] for cat in categories],
            width=200
        )
        apply_option_menu_style(self.category_dropdown, 'secondary')
        self.category_dropdown.pack(side="right", padx=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=20)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save",
            command=self.save_product
        )
        apply_button_style(save_btn, 'primary')
        save_btn.pack(side="left", padx=5, expand=True)
        
        if self.product:
            delete_btn = ctk.CTkButton(
                button_frame,
                text="🗑️ Delete",
                command=self.delete_product
            )
            apply_button_style(delete_btn, 'danger')
            delete_btn.pack(side="left", padx=5, expand=True)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="✖️ Cancel",
            command=self.destroy
        )
        apply_button_style(cancel_btn, 'secondary')
        cancel_btn.pack(side="left", padx=5, expand=True)

    def create_field(self, parent, label, attr_name, is_multiline=False):
        """Create a form field with consistent styling"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            frame,
            text=label,
            font=FONTS['body_bold']
        ).pack(side="left", padx=5)
        
        if is_multiline:
            widget = ctk.CTkTextbox(
                frame,
                height=100,
                wrap="word"
            )
        else:
            widget = ctk.CTkEntry(frame)
            
        apply_entry_style(widget)
        widget.pack(side="right", padx=5, fill="x", expand=True)
        setattr(self, attr_name, widget)

    def load_product_data(self):
        self.name_entry.insert(0, self.product['name'])
        self.desc_entry.insert(0, self.product.get('description', ''))
        self.price_entry.insert(0, str(self.product['price']))
        self.stock_entry.insert(0, str(self.product['stock']))
        self.min_stock_entry.insert(0, str(self.product['min_stock']))
        self.max_stock_entry.insert(0, str(self.product['max_stock']))
        self.barcode_entry.insert(0, self.product['barcode'])
        if self.product['category_name']:
            self.category_var.set(self.product['category_name'])

    def save_product(self):
        try:
            data = {
                'name': self.name_entry.get(),
                'description': self.desc_entry.get(),
                'price': float(self.price_entry.get()),
                'stock': int(self.stock_entry.get()),
                'min_stock': int(self.min_stock_entry.get()),
                'max_stock': int(self.max_stock_entry.get()),
                'category_id': next(
                    (cat['id'] for cat in self.db.get_categories() 
                     if cat['name'] == self.category_var.get()), 
                    None
                )
            }
            
            if self.product:
                success = self.db.update_product(self.product['id'], data)
                message = "Product updated successfully"
            else:
                success = self.db.add_product(data)
                message = "Product added successfully"
            
            if success:
                messagebox.showinfo("Success", message)
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to save product")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for price and stock")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def delete_product(self):
        if not messagebox.askyesno("Confirm Delete", 
                                 "Are you sure you want to delete this product?"):
            return
        
        if self.db.delete_product(self.product['id']):
            messagebox.showinfo("Success", "Product deleted successfully")
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to delete product") 