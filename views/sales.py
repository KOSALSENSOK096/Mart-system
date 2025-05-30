import customtkinter as ctk
from tkinter import ttk, messagebox
from utils.database import Database
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
import os
import logging
from PIL import Image
import json
from decimal import Decimal
import threading
import time
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import webbrowser
import tkinter as tk
import decimal

logger = logging.getLogger(__name__)

# Color constants
COLORS = {
    'primary': "#2B60DE",      # Royal Blue
    'primary_hover': "#1E4BB8", 
    'secondary': "#F0F8FF",    # Light Blue
    'secondary_hover': "#E1EBFF",
    'accent': "#FF6B6B",       # Coral
    'accent_hover': "#FF4B4B",
    'success': "#4CAF50",      # Green
    'success_hover': "#45a049",
    'warning': "#FFA500",      # Orange
    'warning_hover': "#FF8C00",
    'error': "#FF4B4B",        # Error Red
    'error_hover': "#FF3333",
    'text': "#333333",         # Dark Gray
    'text_secondary': "#666666",
    'surface': "#FFFFFF",      # White
    'glass': "#F8F9FA",       # Light Gray
    'hover': "#E9ECEF",       # Hover Gray
    'placeholder': "#999999"   # Placeholder Gray
}

class SalesView(ctk.CTkFrame):
    """Enhanced sales view with modern UI and animations"""
    
    def __init__(self, parent, db: Database):
        super().__init__(parent)
        
        self.parent = parent
        self.db = db
        self.cart = []
        self.recent_sales = []
        self.hotkeys_enabled = True
        self.discount_amount = Decimal('0.00')
        
        # Initialize animation states
        self.loading_animation = False
        self.animation_frame = 0
        self.animation_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.loading_labels = []
        
        # Create UI
        self.create_widgets()
        self.setup_hotkeys()
        
        # Load saved cart
        self.load_saved_cart()
        
        # Start animations
        self.start_animations()
        
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            # Cancel any pending callbacks
            if hasattr(self, '_datetime_after_id'):
                self.parent.after_cancel(self._datetime_after_id)
            
            # Cancel any animations
            if hasattr(self, 'animation_after_id'):
                self.parent.after_cancel(self.animation_after_id)
            
            # Stop loading animation
            self.loading_animation = False
            if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
                self.loading_label.configure(text="")
            
            # Save cart before closing
            if hasattr(self, 'cart') and self.cart:
                self.save_cart()
                
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
            
    def setup_styles(self):
        """Configure custom styles for widgets"""
        try:
            style = ttk.Style()
            
            # Configure Treeview style
            style.configure(
                "Treeview",
                background=COLORS['surface'],
                foreground=COLORS['text'],
                fieldbackground=COLORS['surface'],
                borderwidth=0,
                font=("Segoe UI", 11)
            )
            
            style.configure(
                "Treeview.Heading",
                background=COLORS['primary'],
                foreground="white",
                relief="flat",
                font=("Segoe UI", 11, "bold")
            )
            
            style.map(
                "Treeview",
                background=[("selected", COLORS['primary'])],
                foreground=[("selected", "white")]
            )
            
            # Configure other styles as needed
            
        except Exception as e:
            logger.error(f"Error setting up styles: {e}")
            raise
            
    def create_widgets(self):
        """Create and configure all widgets with enhanced layout and error handling"""
        try:
            # Configure main grid weights
            self.grid_columnconfigure(1, weight=1)  # Right side expands
            self.grid_rowconfigure(0, weight=1)     # Full height
            
            # Create main frames with proper styling
            self.left_frame = ctk.CTkFrame(self)
            self.left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.left_frame.grid_columnconfigure(0, weight=1)  # Single column expands
            
            self.right_frame = ctk.CTkFrame(self)
            self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
            self.right_frame.grid_columnconfigure(0, weight=1)  # Single column expands
            
            # Create loading label
            self.loading_label = ctk.CTkLabel(
                self.left_frame,
                text="",
                font=("Segoe UI", 13),
                text_color=COLORS['primary']
            )
            self.loading_label.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            
            # Create sections in order
            self.create_header_section()      # Title and date/time
            self.create_barcode_section()     # Barcode scanning
            self.create_search_section()      # Search and filters
            self.create_products_section()    # Product list
            self.create_cart_section()        # Shopping cart
            self.create_totals_section()      # Cart totals
            self.create_actions_section()     # Checkout buttons
            
            # Initialize data and start animations
            self.initialize_data()
            self.start_animations()
            
        except Exception as e:
            logger.error(f"Error creating sales interface: {e}")
            self.show_error("Failed to create sales interface")
            raise  # Re-raise to show full error
            
    def create_header_section(self):
        """Create header section with title and date/time"""
        try:
            # Header frame with glass effect
            self.header_frame = ctk.CTkFrame(
                self.left_frame,
                fg_color=COLORS['glass'],
                corner_radius=10
            )
            self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            self.header_frame.grid_columnconfigure(0, weight=1)
            
            # Title with icon
            title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
            title_frame.grid(row=0, column=0, sticky="ew", pady=10)
            title_frame.grid_columnconfigure(1, weight=1)
            
            # Sales icon
            icon_label = ctk.CTkLabel(
                title_frame,
                text="🛍️",
                font=("Segoe UI Emoji", 24),
                text_color=COLORS['primary']
            )
            icon_label.grid(row=0, column=0, padx=10)
            
            # Title text
            title_label = ctk.CTkLabel(
                title_frame,
                text="Sales Register",
                font=("Segoe UI", 20, "bold"),
                text_color=COLORS['text']
            )
            title_label.grid(row=0, column=1, sticky="w")
            
            # Date and time with auto-update
            self.datetime_label = ctk.CTkLabel(
                self.header_frame,
                text="",
                font=("Segoe UI", 13),
                text_color=COLORS['text_secondary']
            )
            self.datetime_label.grid(row=1, column=0, sticky="e", padx=10, pady=(0, 5))
            
            # Stats label
            self.stats_label = ctk.CTkLabel(
                self.header_frame,
                text="Today: $0.00 (0 items)",
                font=("Segoe UI", 13),
                text_color=COLORS['text_secondary']
            )
            self.stats_label.grid(row=2, column=0, sticky="e", padx=10, pady=(0, 10))
            
            # Start datetime update
            self.update_datetime()
            
        except Exception as e:
            logger.error(f"Error creating header section: {e}")
            raise
            
    def create_search_section(self):
        """Create search and filter section"""
        try:
            # Search frame with glass effect
            search_frame = ctk.CTkFrame(
                self.left_frame,
                fg_color=COLORS['glass'],
                corner_radius=10
            )
            search_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
            search_frame.grid_columnconfigure(1, weight=1)
            
            # Search icon
            search_icon = ctk.CTkLabel(
                search_frame,
                text="🔍",
                font=("Segoe UI Emoji", 20),
                text_color=COLORS['primary']
            )
            search_icon.grid(row=0, column=0, padx=10, pady=8)
            
            # Search entry
            self.search_var = tk.StringVar()
            self.search_entry = ctk.CTkEntry(
                search_frame,
                textvariable=self.search_var,
                placeholder_text="Search products...",
                height=35,
                font=("Segoe UI", 13),
                fg_color="transparent",
                border_width=0
            )
            self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
            
            # Category filter
            self.category_var = tk.StringVar(value="All Categories")
            self.category_menu = ctk.CTkOptionMenu(
                search_frame,
                variable=self.category_var,
                values=["All Categories"],
                width=150,
                height=35,
                font=("Segoe UI", 13),
                fg_color=COLORS['primary'],
                button_color=COLORS['primary'],
                button_hover_color=COLORS['primary_hover'],
                command=self.filter_by_category
            )
            self.category_menu.grid(row=0, column=2, padx=10, pady=8)
            
            # Sort options
            self.sort_var = tk.StringVar(value="Name ↑")
            self.sort_menu = ctk.CTkOptionMenu(
                search_frame,
                variable=self.sort_var,
                values=["Name ↑", "Name ↓", "Price ↑", "Price ↓"],
                width=120,
                height=35,
                font=("Segoe UI", 13),
                fg_color=COLORS['secondary'],
                button_color=COLORS['secondary'],
                button_hover_color=COLORS['secondary_hover'],
                command=self.sort_products
            )
            self.sort_menu.grid(row=0, column=3, padx=10, pady=8)
            
            # Bind search events
            self.search_var.trace('w', lambda *args: self.load_products())
            
        except Exception as e:
            logger.error(f"Error creating search section: {e}")
            raise
            
    def create_products_section(self):
        """Create products list section"""
        try:
            # Products frame
            products_frame = ctk.CTkFrame(self.left_frame)
            products_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
            products_frame.grid_rowconfigure(1, weight=1)
            products_frame.grid_columnconfigure(0, weight=1)
            
            # Products header
            header_frame = ctk.CTkFrame(products_frame, fg_color="transparent")
            header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
            header_frame.grid_columnconfigure(1, weight=1)
            
            # Products count
            self.product_count_label = ctk.CTkLabel(
                header_frame,
                text="0 products found",
                font=("Segoe UI", 13),
                text_color=COLORS['text_secondary']
            )
            self.product_count_label.grid(row=0, column=0, sticky="w")
            
            # Create Treeview with scrollbar
            tree_frame = ctk.CTkFrame(products_frame, fg_color="transparent")
            tree_frame.grid(row=1, column=0, sticky="nsew")
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # Configure Treeview style
            style = ttk.Style()
            style.configure(
                "Custom.Treeview",
                background=COLORS['surface'],
                foreground=COLORS['text'],
                fieldbackground=COLORS['surface'],
                borderwidth=0,
                font=("Segoe UI", 11)
            )
            
            # Create Treeview
            self.products_tree = ttk.Treeview(
                tree_frame,
                style="Custom.Treeview",
                columns=("id", "name", "category", "price", "stock"),
                show="headings",
                selectmode="browse"
            )
            
            # Configure columns
            self.products_tree.heading("id", text="ID", command=lambda: self.sort_by_column("id"))
            self.products_tree.heading("name", text="Product Name", command=lambda: self.sort_by_column("name"))
            self.products_tree.heading("category", text="Category", command=lambda: self.sort_by_column("category"))
            self.products_tree.heading("price", text="Price", command=lambda: self.sort_by_column("price"))
            self.products_tree.heading("stock", text="Stock", command=lambda: self.sort_by_column("stock"))
            
            self.products_tree.column("id", width=80, anchor="w")
            self.products_tree.column("name", width=250, anchor="w")
            self.products_tree.column("category", width=150, anchor="w")
            self.products_tree.column("price", width=100, anchor="e")
            self.products_tree.column("stock", width=100, anchor="e")
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.products_tree.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            self.products_tree.configure(yscrollcommand=scrollbar.set)
            
            # Grid the Treeview
            self.products_tree.grid(row=0, column=0, sticky="nsew")
            
            # Bind double-click to add to cart
            self.products_tree.bind('<Double-1>', self.add_to_cart)
            
        except Exception as e:
            logger.error(f"Error creating products section: {e}")
            raise
            
    def create_cart_section(self):
        """Create shopping cart section"""
        try:
            # Cart frame with glass effect
            cart_frame = ctk.CTkFrame(
                self.right_frame,
                fg_color=COLORS['glass'],
                corner_radius=10
            )
            cart_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
            cart_frame.grid_rowconfigure(1, weight=1)
            cart_frame.grid_columnconfigure(0, weight=1)
            
            # Cart header
            header_frame = ctk.CTkFrame(cart_frame, fg_color="transparent")
            header_frame.grid(row=0, column=0, sticky="ew", pady=5)
            header_frame.grid_columnconfigure(1, weight=1)
            
            # Cart icon and title
            icon_label = ctk.CTkLabel(
                header_frame,
                text="🛒",
                font=("Segoe UI Emoji", 24),
                text_color=COLORS['primary']
            )
            icon_label.grid(row=0, column=0, padx=10)
            
            self.cart_title = ctk.CTkLabel(
                header_frame,
                text="Shopping Cart (0 items)",
                font=("Segoe UI", 16, "bold"),
                text_color=COLORS['text']
            )
            self.cart_title.grid(row=0, column=1, sticky="w")
            
            # Cart items treeview
            tree_frame = ctk.CTkFrame(cart_frame, fg_color="transparent")
            tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # Configure cart treeview style
            style = ttk.Style()
            style.configure(
                "Cart.Treeview",
                background=COLORS['surface'],
                foreground=COLORS['text'],
                fieldbackground=COLORS['surface'],
                borderwidth=0,
                font=("Segoe UI", 11)
            )
            
            # Create cart treeview
            self.cart_tree = ttk.Treeview(
                tree_frame,
                style="Cart.Treeview",
                columns=("id", "name", "price", "qty", "total"),
                show="headings",
                selectmode="browse",
                height=8
            )
            
            # Configure columns
            self.cart_tree.heading("id", text="ID")
            self.cart_tree.heading("name", text="Product")
            self.cart_tree.heading("price", text="Price")
            self.cart_tree.heading("qty", text="Qty")
            self.cart_tree.heading("total", text="Total")
            
            self.cart_tree.column("id", width=50, anchor="w")
            self.cart_tree.column("name", width=200, anchor="w")
            self.cart_tree.column("price", width=80, anchor="e")
            self.cart_tree.column("qty", width=60, anchor="e")
            self.cart_tree.column("total", width=100, anchor="e")
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.cart_tree.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            self.cart_tree.configure(yscrollcommand=scrollbar.set)
            
            # Grid the treeview
            self.cart_tree.grid(row=0, column=0, sticky="nsew")
            
            # Bind events
            self.cart_tree.bind("<Delete>", self.remove_from_cart)
            self.cart_tree.bind("<Double-1>", self.edit_cart_item)
            
        except Exception as e:
            logger.error(f"Error creating cart section: {e}")
            raise
            
    def create_totals_section(self):
        """Create cart totals section"""
        try:
            # Totals frame with glass effect
            totals_frame = ctk.CTkFrame(
                self.right_frame,
                fg_color=COLORS['glass'],
                corner_radius=10
            )
            totals_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
            totals_frame.grid_columnconfigure(1, weight=1)
            
            # Subtotal
            ctk.CTkLabel(
                totals_frame,
                text="Subtotal:",
                font=("Segoe UI", 13),
                text_color=COLORS['text_secondary']
            ).grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            self.subtotal_label = ctk.CTkLabel(
                totals_frame,
                text="$0.00",
                font=("Segoe UI", 13, "bold"),
                text_color=COLORS['text']
            )
            self.subtotal_label.grid(row=0, column=1, sticky="e", padx=10)
            
            # Tax
            ctk.CTkLabel(
                totals_frame,
                text="Tax (10%):",
                font=("Segoe UI", 13),
                text_color=COLORS['text_secondary']
            ).grid(row=1, column=0, sticky="w", padx=10, pady=5)
            
            self.tax_label = ctk.CTkLabel(
                totals_frame,
                text="$0.00",
                font=("Segoe UI", 13, "bold"),
                text_color=COLORS['text']
            )
            self.tax_label.grid(row=1, column=1, sticky="e", padx=10)
            
            # Discount
            ctk.CTkLabel(
                totals_frame,
                text="Discount:",
                font=("Segoe UI", 13),
                text_color=COLORS['text_secondary']
            ).grid(row=2, column=0, sticky="w", padx=10, pady=5)
            
            self.discount_label = ctk.CTkLabel(
                totals_frame,
                text="-$0.00",
                font=("Segoe UI", 13, "bold"),
                text_color=COLORS['success']
            )
            self.discount_label.grid(row=2, column=1, sticky="e", padx=10)
            
            # Separator
            separator = ttk.Separator(totals_frame, orient="horizontal")
            separator.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
            
            # Total
            ctk.CTkLabel(
                totals_frame,
                text="Total:",
                font=("Segoe UI", 16, "bold"),
                text_color=COLORS['text']
            ).grid(row=4, column=0, sticky="w", padx=10, pady=10)
            
            self.total_label = ctk.CTkLabel(
                totals_frame,
                text="$0.00",
                font=("Segoe UI", 20, "bold"),
                text_color=COLORS['primary']
            )
            self.total_label.grid(row=4, column=1, sticky="e", padx=10)
            
        except Exception as e:
            logger.error(f"Error creating totals section: {e}")
            raise
            
    def create_actions_section(self):
        """Create action buttons section"""
        try:
            # Actions frame with glass effect
            actions_frame = ctk.CTkFrame(
                self.right_frame,
                fg_color=COLORS['glass'],
                corner_radius=10
            )
            actions_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
            actions_frame.grid_columnconfigure((0, 1), weight=1)
            
            # Top row - Discount and Clear
            discount_btn = ctk.CTkButton(
                actions_frame,
                text="Apply Discount",
                compound="left",
                command=self.apply_discount,
                font=("Segoe UI", 13),
                height=40,
                fg_color=COLORS['warning'],
                hover_color=COLORS['warning_hover']
            )
            discount_btn.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
            
            clear_btn = ctk.CTkButton(
                actions_frame,
                text="Clear Cart",
                compound="left",
                command=self.clear_cart,
                font=("Segoe UI", 13),
                height=40,
                fg_color=COLORS['error'],
                hover_color=COLORS['error_hover']
            )
            clear_btn.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            
            # Bottom row - Save and Checkout
            save_btn = ctk.CTkButton(
                actions_frame,
                text="Save Cart",
                compound="left",
                command=self.save_cart,
                font=("Segoe UI", 13),
                height=40,
                fg_color=COLORS['secondary'],
                hover_color=COLORS['secondary_hover']
            )
            save_btn.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
            
            # Checkout button
            self.checkout_btn = ctk.CTkButton(
                actions_frame,
                text="Checkout",
                compound="left",
                command=self.checkout,
                font=("Segoe UI", 13, "bold"),
                height=40,
                fg_color=COLORS['success'],
                hover_color=COLORS['success_hover']
            )
            self.checkout_btn.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
            
            # Recent sales section
            recent_frame = ctk.CTkFrame(
                self.right_frame,
                fg_color=COLORS['glass'],
                corner_radius=10
            )
            recent_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
            recent_frame.grid_columnconfigure(0, weight=1)
            
            # Recent sales header
            header_frame = ctk.CTkFrame(recent_frame, fg_color="transparent")
            header_frame.grid(row=0, column=0, sticky="ew", pady=5)
            header_frame.grid_columnconfigure(1, weight=1)
            
            # Recent sales icon and title
            icon_label = ctk.CTkLabel(
                header_frame,
                text="📊",
                font=("Segoe UI Emoji", 20),
                text_color=COLORS['primary']
            )
            icon_label.grid(row=0, column=0, padx=10)
            
            title_label = ctk.CTkLabel(
                header_frame,
                text="Recent Sales",
                font=("Segoe UI", 14, "bold"),
                text_color=COLORS['text']
            )
            title_label.grid(row=0, column=1, sticky="w")
            
            # Toggle button
            self.toggle_btn = ctk.CTkButton(
                header_frame,
                text="▼",  # Use text symbol instead of image
                width=30,
                height=30,
                command=self.toggle_recent_sales,
                fg_color="transparent",
                hover_color=COLORS['hover']
            )
            self.toggle_btn.grid(row=0, column=2, padx=10)
            
            # Recent sales content
            self.recent_content = ctk.CTkFrame(recent_frame, fg_color="transparent")
            self.recent_content.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
            self.recent_content.grid_columnconfigure(0, weight=1)
            
            # Recent sales list
            style = ttk.Style()
            style.configure(
                "Recent.Treeview",
                background=COLORS['surface'],
                foreground=COLORS['text'],
                fieldbackground=COLORS['surface'],
                borderwidth=0,
                font=("Segoe UI", 11)
            )
            
            self.recent_list = ttk.Treeview(
                self.recent_content,
                style="Recent.Treeview",
                columns=("time", "items", "total"),
                show="headings",
                height=3
            )
            
            self.recent_list.heading("time", text="Time")
            self.recent_list.heading("items", text="Items")
            self.recent_list.heading("total", text="Total")
            
            self.recent_list.column("time", width=100)
            self.recent_list.column("items", width=100)
            self.recent_list.column("total", width=100)
            
            self.recent_list.grid(row=0, column=0, sticky="ew")
            
            # Initially hide recent sales
            self.recent_content.grid_remove()
            
        except Exception as e:
            logger.error(f"Error creating actions section: {e}")
            raise
            
    def load_icon(self, name):
        """Load icon image"""
        try:
            # Define icon paths
            icons = {
                "discount": "🏷️",
                "trash": "🗑️",
                "save": "💾",
                "checkout": "💳",
                "chevron-down": "⌄",
                "chevron-up": "⌃"
            }
            
            # Return icon text (can be replaced with actual image loading)
            return icons.get(name, "")
            
        except Exception as e:
            logger.error(f"Error loading icon {name}: {e}")
            return ""
            
    def toggle_recent_sales(self):
        """Toggle recent sales visibility"""
        try:
            if self.recent_content.winfo_viewable():
                # Hide content
                self.recent_content.grid_remove()
                self.toggle_btn.configure(text="▲")
            else:
                # Show content
                self.recent_content.grid()
                self.toggle_btn.configure(text="▼")
                
                # Update recent sales list
                self.update_recent_sales()
                
        except Exception as e:
            logger.error(f"Error toggling recent sales: {e}")
            
    def update_recent_sales(self):
        """Update recent sales list with animation"""
        try:
            # Clear existing items
            for item in self.recent_list.get_children():
                self.recent_list.delete(item)
            
            # Add recent sales with fade-in animation
            def add_items(sales, index=0):
                if index < len(sales):
                    sale = sales[index]
                    self.recent_list.insert("", "end", values=(
                        sale['time'],
                        f"{sale['items']} items",
                        f"${sale['total']:.2f}"
                    ))
                    self.after(100, lambda: add_items(sales, index + 1))
            
            add_items(self.recent_sales)
            
        except Exception as e:
            logger.error(f"Error updating recent sales: {e}")
            
    def initialize_data(self):
        """Initialize data and load products"""
        try:
            # Initialize cart
            self.cart = []
            
            # Load initial products
            self.load_products()
            
            # Update statistics
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"Error initializing data: {e}")
            self.show_error("Failed to initialize sales data")
            
    def update_datetime(self):
        """Update the datetime display"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.datetime_label.configure(text=current_time)
            # Use a unique identifier for the after callback
            self._datetime_after_id = self.parent.after(1000, self.update_datetime)
        except Exception as e:
            logger.error(f"Failed to update datetime: {e}")

    def filter_by_category(self, category):
        """Filter products by category with enhanced error handling"""
        try:
            # Reset search field to ensure clean filtering
            self.search_var.set("")
            
            # Load products with category filter
            self.load_products()
            
        except Exception as e:
            logger.error(f"Error filtering by category: {e}")
            self.show_error("Failed to filter products by category")
            
    def load_products(self):
        """Load and display products with enhanced error handling and empty state handling"""
        try:
            # Show loading animation
            self.loading_animation = True
            self.loading_label.configure(text="Loading products...")
            
            # Clear existing items
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            # Get products from database with retry mechanism
            max_retries = 3
            products = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    search_term = self.search_var.get().strip() if self.search_var.get() else None
                    category = self.category_var.get()
                    
                    # Get products with proper error handling
                    products = self.db.get_products_with_optional_search(search_term)
                    break  # If we get here, the query was successful
                        
                except Exception as e:
                    last_error = e
                    logger.error(f"Product loading attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(0.5)  # Wait before retry
                        continue
                    raise
            
            # Initialize empty products list if None
            if products is None:
                products = []
            
            # Ensure products is a list
            if not isinstance(products, list):
                products = list(products) if products else []
            
            # Filter by category if selected and not "All Categories"
            if category and category != "All Categories" and products:
                products = [p for p in products if p.get('category_name') == category]
            
            # Get unique categories from products
            categories = sorted(set(p.get('category_name', '') for p in products if p.get('category_name')))
            
            # Update category menu with available categories
            try:
                self.update_category_menu(["All Categories"] + categories)
            except Exception as e:
                logger.error(f"Error updating category menu: {e}")
                self.update_category_menu(["All Categories"])  # Fallback to default
            
            # Sort products if sort option is selected
            try:
                sort_option = self.sort_var.get()
                if products:
                    reverse = "↓" in sort_option
                    if "Name" in sort_option:
                        products.sort(key=lambda x: str(x.get('name', '')).lower(), reverse=reverse)
                    elif "Price" in sort_option:
                        products.sort(key=lambda x: float(x.get('price', 0)), reverse=reverse)
            except Exception as e:
                logger.error(f"Error sorting products: {e}")
            
            # Insert products into tree with enhanced status indicators
            if products:
                for product in products:
                    try:
                        # Ensure all required fields have default values
                        product_id = product.get('id', 'N/A')
                        name = product.get('name', 'Unknown Product')
                        category = product.get('category_name', 'Uncategorized')
                        
                        # Handle potential invalid price/stock values
                        try:
                            price = float(product.get('price', 0))
                        except (ValueError, TypeError):
                            price = 0.0
                            
                        try:
                            stock = int(product.get('stock', 0))
                        except (ValueError, TypeError):
                            stock = 0
                        
                        # Enhanced stock status indicators with tooltips
                        if stock > 20:
                            stock_status = "✅ In Stock"
                        elif stock > 10:
                            stock_status = "✅ Limited"
                        elif stock > 0:
                            stock_status = "⚠️ Low Stock"
                        else:
                            stock_status = "❌ Out of Stock"
                        
                        self.products_tree.insert("", "end", values=(
                            product_id,
                            f"{name} ({stock_status})",
                            category,
                            f"${price:.2f}",
                            stock
                        ))
                    except Exception as e:
                        logger.error(f"Error inserting product {product.get('id', 'unknown')}: {e}")
                        continue
                
                # Show success message with product count
                self.show_success(
                    f"✨ Successfully loaded {len(products)} products\n"
                    f"Categories: {len(categories)}\n"
                    f"Search term: {search_term if search_term else 'All'}"
                )
            else:
                # If no products found, show friendly message
                self.products_tree.insert("", "end", values=(
                    "",
                    "No products found" if search_term else "Product catalog is empty",
                    "Try different search" if search_term else "Add products to get started",
                    "",
                    ""
                ))
            
            # Update product count with animation
            count_text = f"{len(products)} products found"
            if search_term:
                count_text += f" for '{search_term}'"
            if category and category != "All Categories":
                count_text += f" in {category}"
            self.product_count_label.configure(text=count_text)
            
            # Update statistics to show latest data
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"Failed to load products: {e}")
            self.show_error(
                "❌ Failed to load products\n\n"
                f"Error: {str(e)}\n\n"
                "Please try again or contact support if the problem persists."
            )
            # Show error state in tree
            self.products_tree.insert("", "end", values=(
                "",
                "⚠️ Error loading products",
                "Please try again",
                "",
                ""
            ))
            self.product_count_label.configure(text="Error loading products")
            
        finally:
            # Stop loading animation
            self.loading_animation = False
            self.loading_label.configure(text="")

    def update_category_menu(self, categories=None):
        """Update category menu with enhanced error handling"""
        try:
            # Initialize with default categories if none provided
            if categories is None:
                categories = ["All Categories"]
            elif not isinstance(categories, list):
                categories = list(categories)
            
            # Ensure "All Categories" is always first
            if "All Categories" not in categories:
                categories.insert(0, "All Categories")
            
            # Remove duplicates while preserving order
            seen = set()
            categories = [x for x in categories if not (x in seen or seen.add(x))]
            
            # Update menu
            self.category_var.set("All Categories")  # Reset to default
            self.category_menu.configure(values=categories)
            
            # Update category count label if it exists
            if hasattr(self, 'category_count_label'):
                category_count = len(categories) - 1  # Subtract "All Categories"
                self.category_count_label.configure(
                    text=f"{category_count} {'category' if category_count == 1 else 'categories'}"
                )
                
        except Exception as e:
            logger.error(f"Error updating category menu: {e}")
            # Set safe default values
            self.category_var.set("All Categories")
            self.category_menu.configure(values=["All Categories"])
            if hasattr(self, 'category_count_label'):
                self.category_count_label.configure(text="0 categories")

    def add_to_cart(self, event):
        """Add selected product to cart with enhanced validation"""
        try:
            selection = self.products_tree.selection()
            if not selection:
                self.show_error("Please select a product first")
                return
            
            item = self.products_tree.item(selection[0])
            product_id = item['values'][0]
            
            # Get fresh product details from database
            product = next((p for p in self.db.get_products_with_optional_search(None) 
                          if p['id'] == product_id), None)
            if not product:
                self.show_error("Product not found or no longer available")
                return
            
            # Validate stock
            if product['stock'] <= 0:
                self.show_error(f"Sorry, {product['name']} is out of stock")
                return
            
            # Ask for quantity with modern dialog
            dialog = QuantityDialog(self.parent, product['stock'], product['name'])
            self.parent.wait_window(dialog)
            
            if dialog.quantity:
                try:
                    # Check if product already in cart
                    cart_item = next((item for item in self.cart 
                                    if item['id'] == product_id), None)
                    
                    if cart_item:
                        # Validate combined quantity
                        new_quantity = cart_item['quantity'] + dialog.quantity
                        if new_quantity > product['stock']:
                            self.show_error(
                                f"Cannot add {dialog.quantity} more units of {product['name']}\n"
                                f"Current in cart: {cart_item['quantity']}\n"
                                f"Available stock: {product['stock']}"
                            )
                            return
                        
                        # Update existing cart item
                        cart_item['quantity'] = new_quantity
                        self.show_success(
                            f"Updated {product['name']} quantity to {new_quantity}"
                        )
                    else:
                        # Add new item to cart
                        self.cart.append({
                            'id': product['id'],
                            'name': product['name'],
                            'price': product['price'],
                            'quantity': dialog.quantity
                        })
                        self.show_success(
                            f"Added {dialog.quantity} x {product['name']} to cart"
                        )
                    
                    # Update display
                    self.update_cart_display()
                    
                    # Save cart automatically
                    self.save_cart()
                    
                except Exception as e:
                    logger.error(f"Error updating cart: {e}")
                    self.show_error(f"Failed to update cart: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            self.show_error(f"Failed to add item to cart: {str(e)}")

    def remove_from_cart(self, event):
        """Remove selected item from cart"""
        selection = self.cart_tree.selection()
        if not selection:
            return
        
        item = self.cart_tree.item(selection[0])
        product_id = item['values'][0]
        
        # Confirm removal
        if messagebox.askyesno("Confirm Remove", 
                             "Are you sure you want to remove this item from the cart?"):
            # Remove from cart
            self.cart = [item for item in self.cart if item['id'] != product_id]
            self.update_cart_display()

    def update_cart_display(self, discount=None):
        """Update cart display with enhanced animations and error handling"""
        try:
            # Clear cart tree with animation
            def clear_items():
                items = self.cart_tree.get_children()
                if items:
                    self.cart_tree.delete(items[0])
                    self.parent.after(50, clear_items)
                else:
                    update_display()
            
            def update_display():
                try:
                    # Calculate totals with error handling
                    subtotal = Decimal('0.00')
                    total_items = 0
                    
                    for item in self.cart:
                        try:
                            # Convert values to Decimal for precise calculation
                            price = Decimal(str(item['price']))
                            quantity = int(item['quantity'])
                            item_total = price * quantity
                            
                            subtotal += item_total
                            total_items += quantity
                            
                            # Format values for display
                            price_str = f"${price:.2f}"
                            qty_str = str(quantity)
                            total_str = f"${item_total:.2f}"
                            
                            self.cart_tree.insert("", "end", values=(
                                item['id'],
                                item['name'],
                                price_str,
                                qty_str,
                                total_str
                            ))
                        except (ValueError, TypeError, KeyError, decimal.InvalidOperation) as e:
                            logger.error(f"Error processing cart item: {e}")
                            continue
                    
                    # Calculate tax and total
                    tax_rate = Decimal('0.10')
                    tax = subtotal * tax_rate
                    
                    # Apply discount if any
                    if discount:
                        try:
                            discount_amount = Decimal(str(discount))
                            if discount_amount > subtotal:
                                discount_amount = subtotal
                        except (ValueError, decimal.InvalidOperation):
                            discount_amount = Decimal('0.00')
                    else:
                        discount_amount = Decimal('0.00')
                    
                    total = subtotal + tax - discount_amount
                    
                    # Update labels with formatted values
                    self.subtotal_label.configure(text=f"${subtotal:.2f}")
                    self.tax_label.configure(text=f"${tax:.2f}")
                    self.discount_label.configure(text=f"-${discount_amount:.2f}")
                    self.total_label.configure(text=f"${total:.2f}")
                    
                    # Update item count
                    if total_items == 0:
                        self.cart_tree.insert("", "end", values=(
                            "",
                            "Cart is empty",
                            "",
                            "",
                            ""
                        ))
                    
                except Exception as e:
                    logger.error(f"Error updating cart display: {e}")
                    self.show_error("Failed to update cart display")
            
            # Start the clear animation
            clear_items()
            
        except Exception as e:
            logger.error(f"Critical error in cart update: {e}")
            self.show_error("Failed to update cart")

    def clear_cart(self):
        """Clear all items from cart"""
        if not self.cart:
            return
            
        if messagebox.askyesno("Confirm Clear Cart", 
                             "Are you sure you want to clear the entire cart?"):
            self.cart = []
            self.update_cart_display()

    def checkout(self):
        """Process checkout with enhanced validation and error handling"""
        if not self.cart:
            self.show_error("Cart is empty")
            return
        
        try:
            # Calculate totals
            subtotal = sum(item['price'] * item['quantity'] for item in self.cart)
            tax = subtotal * 0.10
            total = subtotal + tax - self.discount_amount
            
            # Validate stock availability before proceeding
            unavailable_items = []
            for item in self.cart:
                product = next((p for p in self.db.get_products_with_optional_search(None) 
                              if p['id'] == item['id']), None)
                if not product:
                    unavailable_items.append(f"{item['name']} is no longer available")
                elif product['stock'] < item['quantity']:
                    unavailable_items.append(
                        f"Insufficient stock for {item['name']}. "
                        f"Requested: {item['quantity']}, Available: {product['stock']}"
                    )
            
            if unavailable_items:
                self.show_error(
                    "Cannot complete checkout:\n\n" + "\n".join(unavailable_items)
                )
                return
            
            # Prepare detailed summary with enhanced formatting
            summary = "🧾 Order Summary:\n\n"
            
            # Items with emojis
            for item in self.cart:
                item_total = item['price'] * item['quantity']
                summary += f"📦 {item['quantity']}x {item['name']}\n"
                summary += f"    ${item['price']:.2f} each = ${item_total:.2f}\n"
            
            # Totals with clear formatting
            summary += "\n💰 Payment Details:\n"
            summary += f"Subtotal: ${subtotal:.2f}\n"
            summary += f"Tax (10%): ${tax:.2f}\n"
            
            if self.discount_amount > 0:
                summary += f"Discount: -${self.discount_amount:.2f}\n"
            
            summary += f"\n💵 Total: ${total:.2f}\n\n"
            summary += "Would you like to complete this transaction?"
            
            # Show confirmation dialog
            if not messagebox.askyesno("Confirm Checkout", summary):
                return
            
            # Process sale with retry mechanism
            max_retries = 3
            sale_id = None
            
            for attempt in range(max_retries):
                try:
                    # Show processing animation
                    self.loading_animation = True
                    self.loading_label.configure(text="Processing transaction...")
                    
                    # Process sale
                    sale_id = self.db.add_sale(
                        user_id=1,  # TODO: Get actual user ID
                        items=[{
                            'product_id': item['id'],
                            'quantity': item['quantity'],
                            'price': item['price']
                        } for item in self.cart],
                        total=total,
                        discount=self.discount_amount
                    )
                    
                    if sale_id:
                        break
                    
                except Exception as e:
                    logger.error(f"Checkout attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Wait before retry
                    else:
                        raise
            
            if not sale_id:
                raise ValueError("Failed to process sale after multiple attempts")
            
            # Generate receipt
            receipt_path = self.generate_receipt(sale_id)
            
            # Show success message with receipt options
            if messagebox.askyesno(
                "✅ Success", 
                "Transaction completed successfully!\n\n"
                "Would you like to print the receipt?"
            ):
                self.print_receipt()
            
            # Add to recent sales with animation
            self.recent_sales.insert(0, {
                'time': datetime.now().strftime("%H:%M:%S"),
                'items': sum(item['quantity'] for item in self.cart),
                'total': total
            })
            
            # Keep only last 10 sales
            self.recent_sales = self.recent_sales[:10]
            
            # Update displays
            self.update_recent_sales()
            self.cart = []
            self.update_cart_display()
            self.load_products()  # Refresh product list
            self.update_statistics()
            
            # Clean up saved cart
            if os.path.exists("saved_cart.json"):
                try:
                    os.remove("saved_cart.json")
                except Exception as e:
                    logger.warning(f"Failed to remove saved cart: {e}")
            
            # Show final success message with animation
            self.show_success(
                "✨ Transaction completed successfully!\n"
                f"Sale ID: {sale_id}\n"
                f"Total Amount: ${total:.2f}"
            )
            
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Checkout validation error: {e}")
            self.show_error(f"Validation Error: {str(e)}")
            
        except Exception as e:
            # Handle other errors
            logger.error(f"Checkout failed: {e}")
            self.show_error(
                "❌ Checkout failed. Please try again.\n\n"
                f"Error: {str(e)}"
            )
            
        finally:
            # Always stop loading animation
            self.loading_animation = False
            self.loading_label.configure(text="")

    def generate_receipt(self, sale_id):
        """Generate a beautiful receipt with custom styling"""
        try:
            # Get sale data
            sale_data = {
                'receipt_number': str(sale_id),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'items': self.cart,
                'subtotal': sum(item['price'] * item['quantity'] for item in self.cart),
                'tax': sum(item['price'] * item['quantity'] for item in self.cart) * 0.10,
                'discount': self.discount_amount,
                'total': sum(item['price'] * item['quantity'] for item in self.cart) * 1.1 - self.discount_amount
            }
            
            # Create receipt directory if not exists
            receipt_dir = "receipts"
            if not os.path.exists(receipt_dir):
                os.makedirs(receipt_dir)
            
            # Generate filename
            filename = f"receipt_{sale_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(receipt_dir, filename)
            
            # Create PDF
            doc = SimpleDocTemplate(filepath, pagesize=letter,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Styles
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Center', alignment=1))
            
            # Content
            story = []
            
            # Header
            story.append(Paragraph("Smart POS System", styles['Title']))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"Receipt #{sale_data['receipt_number']}", styles['Center']))
            story.append(Paragraph(f"Date: {sale_data['date']}", styles['Center']))
            story.append(Spacer(1, 20))
            
            # Items table
            items_data = [['Item', 'Qty', 'Price', 'Total']]
            for item in sale_data['items']:
                items_data.append([
                    item['name'],
                    str(item['quantity']),
                    f"${item['price']:.2f}",
                    f"${item['price'] * item['quantity']:.2f}"
                ])
            
            table = Table(items_data, colWidths=[220, 70, 100, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Summary
            summary_style = ParagraphStyle(
                'Summary',
                parent=styles['Normal'],
                fontSize=12,
                alignment=2,
                spaceAfter=6
            )
            
            story.append(Paragraph(f"Subtotal: ${sale_data['subtotal']:.2f}", summary_style))
            story.append(Paragraph(f"Tax (10%): ${sale_data['tax']:.2f}", summary_style))
            if sale_data['discount'] > 0:
                story.append(Paragraph(f"Discount: -${sale_data['discount']:.2f}", summary_style))
            story.append(Paragraph(f"Total: ${sale_data['total']:.2f}", 
                                ParagraphStyle('Total', parent=summary_style, fontSize=14, bold=True)))
            
            # Footer
            story.append(Spacer(1, 30))
            story.append(Paragraph("Thank you for your business!", styles['Center']))
            story.append(Paragraph("Please come again!", styles['Center']))
            
            # Build PDF
            doc.build(story)
            
            return filepath
                
        except Exception as e:
            logger.error(f"Failed to generate receipt: {e}")
            raise

    def print_receipt(self):
        """Print the last generated receipt"""
        receipt_dir = "receipts"
        if not os.path.exists(receipt_dir):
            messagebox.showinfo("Info", "No receipts found")
            return
            
        # Get most recent receipt
        receipts = sorted([f for f in os.listdir(receipt_dir) if f.startswith("receipt_")],
                         reverse=True)
        
        if not receipts:
            messagebox.showinfo("Info", "No receipts found")
            return
            
        filepath = os.path.join(receipt_dir, receipts[0])
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(filepath, "print")
            else:  # Linux/Mac
                os.system(f'lpr "{filepath}"')
            
            messagebox.showinfo("Success", "Receipt sent to printer")
        except Exception as e:
            logger.error(f"Failed to print receipt: {e}")
            messagebox.showerror("Error", f"Failed to print receipt: {str(e)}")

    def sort_products(self, option):
        """Sort products based on selected option"""
        items = [(self.products_tree.item(item)["values"], item) 
                for item in self.products_tree.get_children("")]
        
        reverse = "↓" in option
        if "Name" in option:
            items.sort(key=lambda x: x[0][1], reverse=reverse)
        elif "Price" in option:
            items.sort(key=lambda x: float(x[0][3].replace("$", "")), reverse=reverse)
        
        # Rearrange items
        for idx, (_, item) in enumerate(items):
            self.products_tree.move(item, "", idx)

    def sort_by_column(self, col):
        """Sort treeview when column header is clicked"""
        items = [(self.products_tree.set(item, col), item) 
                for item in self.products_tree.get_children("")]
        
        # Determine sort order
        reverse = False
        if hasattr(self, "_sort_col") and self._sort_col == col:
            reverse = not getattr(self, "_sort_reverse", False)
        
        self._sort_col = col
        self._sort_reverse = reverse
        
        # Sort items
        items.sort(reverse=reverse)
        for idx, (_, item) in enumerate(items):
            self.products_tree.move(item, "", idx)

    def apply_discount(self):
        """Apply a discount to the current cart"""
        if not self.cart:
            messagebox.showwarning("Warning", "Cart is empty")
            return
        
        dialog = DiscountDialog(self.parent)
        self.parent.wait_window(dialog)
        
        if dialog.discount_amount is not None:
            self.update_cart_display(discount=dialog.discount_amount)

    def save_cart(self):
        """Save current cart to file"""
        if not self.cart:
            messagebox.showinfo("Info", "Nothing to save - cart is empty")
            return
        
        try:
            with open("saved_cart.json", "w") as f:
                json.dump(self.cart, f)
            messagebox.showinfo("Success", "Cart saved successfully")
        except Exception as e:
            logger.error(f"Failed to save cart: {e}")
            messagebox.showerror("Error", "Failed to save cart")

    def load_saved_cart(self):
        """Load previously saved cart"""
        try:
            if os.path.exists("saved_cart.json"):
                with open("saved_cart.json", "r") as f:
                    self.cart = json.load(f)
                self.update_cart_display()
        except Exception as e:
            logger.error(f"Failed to load saved cart: {e}")

    def update_statistics(self):
        """Update daily sales statistics"""
        try:
            # Get today's sales from database
            stats = self.db.get_daily_sales()
            if stats:
                total_revenue = float(stats['total_revenue'] or 0)
                total_items = int(stats['total_items'] or 0)
                
                self.stats_label.configure(
                    text=f"Today: ${total_revenue:.2f} ({total_items} items)"
                )
            else:
                self.stats_label.configure(text="Today: $0.00 (0 items)")
                
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
            self.stats_label.configure(text="Today: $0.00 (0 items)")

    def setup_hotkeys(self):
        """Setup keyboard shortcuts"""
        if not self.hotkeys_enabled:
            return
            
        self.parent.bind('<Control-s>', lambda e: self.save_cart())
        self.parent.bind('<Control-o>', lambda e: self.load_saved_cart())
        self.parent.bind('<Control-n>', lambda e: self.clear_cart())
        self.parent.bind('<Control-d>', lambda e: self.apply_discount())
        self.parent.bind('<F5>', lambda e: self.load_products())
        self.parent.bind('<F1>', lambda e: self.show_help())
        self.parent.bind('<Control-p>', lambda e: self.print_receipt())
        self.parent.bind('<Escape>', lambda e: self.toggle_hotkeys())

    def show_help(self):
        """Show help dialog with keyboard shortcuts"""
        help_text = """
        Keyboard Shortcuts:
        ------------------
        Ctrl + S: Save Cart
        Ctrl + O: Load Saved Cart
        Ctrl + N: New Cart (Clear)
        Ctrl + D: Apply Discount
        F5: Refresh Products
        F1: Show This Help
        Ctrl + P: Print Receipt
        Escape: Toggle Hotkeys
        
        Cart Operations:
        ---------------
        Double-click/Enter: Add to Cart
        Delete: Remove from Cart
        
        For more help, visit our documentation.
        """
        
        help_dialog = ctk.CTkToplevel(self.parent)
        help_dialog.title("Keyboard Shortcuts")
        help_dialog.geometry("400x500")
        
        # Center dialog
        help_dialog.update_idletasks()
        x = (help_dialog.winfo_screenwidth() // 2) - (help_dialog.winfo_width() // 2)
        y = (help_dialog.winfo_screenheight() // 2) - (help_dialog.winfo_height() // 2)
        help_dialog.geometry(f"+{x}+{y}")
        
        # Help content
        frame = ctk.CTkFrame(help_dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame,
                    text="Keyboard Shortcuts",
                    font=("Helvetica", 18, "bold")).pack(pady=10)
        
        text = ctk.CTkTextbox(frame, width=350, height=400)
        text.pack(pady=10)
        text.insert("1.0", help_text)
        text.configure(state="disabled")
        
        ctk.CTkButton(frame,
                     text="View Online Documentation",
                     command=lambda: webbrowser.open("https://docs.example.com")).pack(pady=10)

    def toggle_hotkeys(self):
        """Toggle keyboard shortcuts on/off"""
        self.hotkeys_enabled = not self.hotkeys_enabled
        status = "enabled" if self.hotkeys_enabled else "disabled"
        messagebox.showinfo("Hotkeys", f"Keyboard shortcuts are now {status}")
        
        if self.hotkeys_enabled:
            self.setup_hotkeys()
        else:
            # Unbind all shortcuts
            for key in ['<Control-s>', '<Control-o>', '<Control-n>', 
                       '<Control-d>', '<F5>', '<F1>', '<Control-p>', '<Escape>']:
                self.parent.unbind(key)

    def animate_header(self):
        """Animate header with fade-in effect"""
        try:
            def fade_in(widget, alpha=0):
                if alpha < 1:
                    # Calculate color with alpha
                    r = int(0x2B * alpha)
                    g = int(0x60 * alpha)
                    b = int(0xDE * alpha)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    try:
                        widget.configure(fg_color=color)
                        self.animation_after_id = self.after(20, lambda: fade_in(widget, alpha + 0.1))
                    except Exception as e:
                        logger.error(f"Animation error: {e}")
            
            fade_in(self.header_frame)
            
        except Exception as e:
            logger.error(f"Error animating header: {e}")
            
    def start_loading_animation(self):
        """Start loading spinner animation"""
        try:
            def animate():
                if not hasattr(self, 'loading_label') or not self.loading_label.winfo_exists():
                    return
                    
                if self.loading_animation:
                    frame = self.animation_frames[self.animation_frame]
                    self.loading_label.configure(text=f"Loading {frame}")
                    self.animation_frame = (self.animation_frame + 1) % len(self.animation_frames)
                    self.animation_after_id = self.after(100, animate)
            
            self.loading_animation = True
            animate()
            
        except Exception as e:
            logger.error(f"Error starting loading animation: {e}")
            
    def stop_loading_animation(self):
        """Stop loading animation"""
        try:
            self.loading_animation = False
            if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
                self.loading_label.configure(text="")
                
            if hasattr(self, 'animation_after_id'):
                self.after_cancel(self.animation_after_id)
                
        except Exception as e:
            logger.error(f"Error stopping loading animation: {e}")
            
    def show_error(self, message, widget=None):
        """Show error dialog with animation"""
        try:
            # Flash widget if provided
            if widget and widget.winfo_exists():
                original_color = widget.cget("fg_color")
                def flash(times=3):
                    if not widget.winfo_exists():
                        return
                    if times > 0:
                        widget.configure(fg_color=COLORS['error'])
                        self.after(200, lambda: restore(times))
                    else:
                        widget.configure(fg_color=original_color)
                        
                def restore(times):
                    if not widget.winfo_exists():
                        return
                    widget.configure(fg_color=original_color)
                    self.after(200, lambda: flash(times - 1))
                    
                flash()
            
            # Show error dialog
            try:
                dialog = ErrorDialog(self.parent, message)
                dialog.show()
            except Exception as e:
                logger.error(f"Failed to show error dialog: {e}")
                messagebox.showerror("Error", message)
            
        except Exception as e:
            logger.error(f"Error showing error dialog: {e}")
            messagebox.showerror("Error", message)
            
    def show_success(self, message, widget=None):
        """Show success dialog with animation"""
        try:
            # Pulse widget if provided
            if widget and widget.winfo_exists():
                original_color = widget.cget("fg_color")
                def pulse(times=2):
                    if not widget.winfo_exists():
                        return
                    if times > 0:
                        widget.configure(fg_color=COLORS['success'])
                        self.after(300, lambda: restore(times))
                    else:
                        widget.configure(fg_color=original_color)
                        
                def restore(times):
                    if not widget.winfo_exists():
                        return
                    widget.configure(fg_color=original_color)
                    self.after(300, lambda: pulse(times - 1))
                    
                pulse()
            
            # Show success dialog
            try:
                dialog = SuccessDialog(self.parent, message)
                dialog.show()
            except Exception as e:
                logger.error(f"Failed to show success dialog: {e}")
                messagebox.showinfo("Success", message)
            
        except Exception as e:
            logger.error(f"Error showing success dialog: {e}")
            messagebox.showinfo("Success", message)
            
    def edit_cart_item(self, event=None):
        """Edit quantity of cart item"""
        try:
            selection = self.cart_tree.selection()
            if not selection:
                return
                
            item = self.cart_tree.item(selection[0])
            product_id = item['values'][0]
            
            # Find cart item
            cart_item = next((item for item in self.cart if item['id'] == product_id), None)
            if not cart_item:
                return
            
            # Show quantity dialog
            dialog = QuantityDialog(
                self,
                max_quantity=cart_item['stock'],
                product_name=cart_item['name'],
                initial_quantity=cart_item['quantity']
            )
            
            self.wait_window(dialog)
            
            if dialog.quantity is not None:
                if dialog.quantity == 0:
                    # Remove item if quantity is 0
                    self.cart = [item for item in self.cart if item['id'] != product_id]
                else:
                    # Update quantity
                    cart_item['quantity'] = dialog.quantity
                
                # Update display
                self.update_cart_display()
                
        except Exception as e:
            logger.error(f"Error editing cart item: {e}")
            self.show_error("Failed to edit cart item")

    def start_animations(self):
        """Start all UI animations"""
        try:
            # Animate header
            self.animate_header()
            
            # Start loading animation
            self.start_loading_animation()
            
            # Animate cart totals
            self.animate_totals()
            
        except Exception as e:
            logger.error(f"Error starting animations: {e}")
            
    def animate_totals(self):
        """Animate cart totals with pulse effect"""
        try:
            def pulse(times=2):
                if times > 0:
                    self.subtotal_label.configure(fg_color=COLORS['success'])
                    self.tax_label.configure(fg_color=COLORS['success'])
                    self.discount_label.configure(fg_color=COLORS['success'])
                    self.total_label.configure(fg_color=COLORS['success'])
                    self.after(300, lambda: pulse(times - 1))
            
            pulse()
            
        except Exception as e:
            logger.error(f"Error animating totals: {e}")

    def create_barcode_section(self):
        """Create barcode scanning section"""
        try:
            # Barcode frame with glass effect
            barcode_frame = ctk.CTkFrame(
                self.left_frame,
                fg_color=COLORS['glass'],
                corner_radius=10
            )
            barcode_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
            barcode_frame.grid_columnconfigure(1, weight=1)
            
            # Barcode icon
            barcode_icon = ctk.CTkLabel(
                barcode_frame,
                text="📱",
                font=("Segoe UI Emoji", 20),
                text_color=COLORS['primary']
            )
            barcode_icon.grid(row=0, column=0, padx=10, pady=8)
            
            # Barcode entry
            self.barcode_var = tk.StringVar()
            self.barcode_entry = ctk.CTkEntry(
                barcode_frame,
                textvariable=self.barcode_var,
                placeholder_text="Scan barcode or enter product code...",
                height=35,
                font=("Segoe UI", 13),
                fg_color="transparent",
                border_width=0
            )
            self.barcode_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
            
            # Bind barcode events
            self.barcode_entry.bind('<Return>', self.handle_barcode)
            
        except Exception as e:
            logger.error(f"Error creating barcode section: {e}")
            raise
            
    def handle_barcode(self, event=None):
        """Handle barcode scan or manual entry"""
        try:
            barcode = self.barcode_var.get().strip()
            if not barcode:
                return
                
            # Clear barcode entry
            self.barcode_var.set("")
            self.barcode_entry.focus_set()
            
            # Search for product
            products = self.db.get_products_with_optional_search(barcode)
            product = next((p for p in products if p.get('barcode') == barcode), None)
            
            if not product:
                self.show_error(f"Product not found for barcode: {barcode}")
                return
                
            # Add to cart using existing method
            self.add_to_cart_by_id(product['id'])
            
        except Exception as e:
            logger.error(f"Error processing barcode: {e}")
            self.show_error("Failed to process barcode")

    def add_to_cart_by_id(self, product_id):
        """Add product to cart by ID with quantity 1"""
        try:
            # Get product details
            product = self.db.get_products_with_optional_search(None)
            if not product:
                self.show_error("Product not found")
                return
                
            # Find the specific product
            product = next((p for p in product if p['id'] == product_id), None)
            if not product:
                self.show_error("Product not found")
                return
            
            # Check stock
            if product['stock'] <= 0:
                self.show_error(f"Sorry, {product['name']} is out of stock")
                return
            
            # Check if product is already in cart
            cart_item = next((item for item in self.cart if item['id'] == product_id), None)
            
            if cart_item:
                # Update existing cart item
                if cart_item['quantity'] + 1 > product['stock']:
                    self.show_error(f"Sorry, only {product['stock']} units available")
                    return
                cart_item['quantity'] += 1
            else:
                # Add new cart item
                self.cart.append({
                    'id': product_id,
                    'name': product['name'],
                    'price': float(product['price']),
                    'quantity': 1,
                    'stock': product['stock']
                })
            
            # Update display
            self.update_cart_display()
            
            # Show success message
            self.show_success(f"Added {product['name']} to cart")
            
            # Save cart automatically
            self.save_cart()
            
        except Exception as e:
            logger.error(f"Error adding product to cart: {e}")
            self.show_error("Failed to add product to cart")

class ErrorDialog(ctk.CTkToplevel):
    """Custom error dialog with animations"""
    
    def __init__(self, parent, message):
        super().__init__(parent)
        
        self.title("Error")
        self.geometry("400x250")
        
        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Create content
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Error icon
        icon_label = ctk.CTkLabel(
            frame,
            text="❌",
            font=("Segoe UI Emoji", 48),
            text_color=COLORS['error']
        )
        icon_label.pack(pady=10)
        
        # Message
        msg_label = ctk.CTkLabel(
            frame,
            text=message,
            font=("Segoe UI", 14),
            wraplength=300,
            justify="center"
        )
        msg_label.pack(pady=10)
        
        # OK button
        ok_button = ctk.CTkButton(
            frame,
            text="OK",
            command=self.destroy,
            width=100,
            height=35,
            fg_color=COLORS['error'],
            hover_color=COLORS['error_hover']
        )
        ok_button.pack(pady=10)
        
        # Bind escape
        self.bind("<Escape>", lambda e: self.destroy())
        ok_button.focus_set()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
    def show(self):
        """Show dialog with smooth fade-in animation"""
        try:
            self.attributes('-alpha', 0.0)
            
            def fade_in(alpha=0.0):
                if not self.winfo_exists():
                    return
                if alpha < 1.0:
                    alpha += 0.05  # Smaller steps for smoother animation
                    self.attributes('-alpha', alpha)
                    self.after(10, lambda: fade_in(alpha))
                    
            fade_in()
            
        except Exception as e:
            logger.error(f"Error in dialog fade animation: {e}")
            self.attributes('-alpha', 1.0)  # Ensure dialog is visible
            self.after(2000, self.destroy)  # Still auto-close after delay
        
    def animate_sparkle(self, index=0):
        """Animate sparkle icon"""
        sparkles = ["✨", "⭐", "🌟"]
        if self.winfo_exists():
            self.icon_label.configure(text=sparkles[index])
            next_index = (index + 1) % len(sparkles)
            self.after(500, lambda: self.animate_sparkle(next_index)) 

class QuantityDialog(ctk.CTkToplevel):
    """Dialog for entering product quantity"""
    
    def __init__(self, parent, max_quantity, product_name, initial_quantity=1):
        super().__init__(parent)
        
        self.title("Enter Quantity")
        self.geometry("400x300")
        
        self.quantity = None
        self.max_quantity = max_quantity
        
        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Create content
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Product name
        name_label = ctk.CTkLabel(
            frame,
            text=product_name,
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS['text']
        )
        name_label.pack(pady=10)
        
        # Available stock
        stock_label = ctk.CTkLabel(
            frame,
            text=f"Available Stock: {max_quantity}",
            font=("Segoe UI", 14),
            text_color=COLORS['text_secondary']
        )
        stock_label.pack(pady=5)
        
        # Quantity controls
        controls_frame = ctk.CTkFrame(frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=15)
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Decrease button
        decrease_btn = ctk.CTkButton(
            controls_frame,
            text="-",
            width=40,
            height=40,
            command=self.decrease_quantity,
            font=("Segoe UI", 16),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover']
        )
        decrease_btn.grid(row=0, column=0, padx=5)
        
        # Quantity entry
        self.quantity_entry = ctk.CTkEntry(
            controls_frame,
            width=100,
            height=40,
            font=("Segoe UI", 14),
            justify="center"
        )
        self.quantity_entry.grid(row=0, column=1, padx=10)
        self.quantity_entry.insert(0, str(initial_quantity))
        
        # Increase button
        increase_btn = ctk.CTkButton(
            controls_frame,
            text="+",
            width=40,
            height=40,
            command=self.increase_quantity,
            font=("Segoe UI", 16),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover']
        )
        increase_btn.grid(row=0, column=2, padx=5)
        
        # Action buttons
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=20)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=self.cancel,
            width=120,
            height=40,
            font=("Segoe UI", 13),
            fg_color=COLORS['error'],
            hover_color=COLORS['error_hover']
        )
        cancel_btn.grid(row=0, column=0, padx=5)
        
        # Add button
        add_btn = ctk.CTkButton(
            buttons_frame,
            text="Add to Cart",
            command=self.ok,
            width=120,
            height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['success_hover']
        )
        add_btn.grid(row=0, column=1, padx=5)
        
        # Bind keys
        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())
        
        # Set focus
        self.quantity_entry.focus()
        self.quantity_entry.select_range(0, "end")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
    def increase_quantity(self):
        """Increase quantity by 1"""
        try:
            current = int(self.quantity_entry.get())
            if current < self.max_quantity:
                self.quantity_entry.delete(0, "end")
                self.quantity_entry.insert(0, str(current + 1))
                
        except ValueError:
            pass
            
    def decrease_quantity(self):
        """Decrease quantity by 1"""
        try:
            current = int(self.quantity_entry.get())
            if current > 1:
                self.quantity_entry.delete(0, "end")
                self.quantity_entry.insert(0, str(current - 1))
                
        except ValueError:
            pass
            
    def ok(self):
        """Validate and accept quantity"""
        try:
            quantity = int(self.quantity_entry.get())
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if quantity > self.max_quantity:
                raise ValueError(f"Maximum quantity is {self.max_quantity}")
                
            self.quantity = quantity
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            
    def cancel(self):
        """Cancel quantity selection"""
        self.destroy()
        
class DiscountDialog(ctk.CTkToplevel):
    """Dialog for applying discounts"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Apply Discount")
        self.geometry("400x300")
        
        self.discount_amount = None
        
        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Create content
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            frame,
            text="Apply Discount",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS['text']
        )
        title_label.pack(pady=10)
        
        # Discount type
        self.discount_type = ctk.StringVar(value="amount")
        
        type_frame = ctk.CTkFrame(frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=15)
        
        # Amount radio
        amount_radio = ctk.CTkRadioButton(
            type_frame,
            text="Amount ($)",
            variable=self.discount_type,
            value="amount",
            font=("Segoe UI", 13),
            fg_color=COLORS['primary']
        )
        amount_radio.pack(side="left", padx=10)
        
        # Percent radio
        percent_radio = ctk.CTkRadioButton(
            type_frame,
            text="Percentage (%)",
            variable=self.discount_type,
            value="percent",
            font=("Segoe UI", 13),
            fg_color=COLORS['primary']
        )
        percent_radio.pack(side="left", padx=10)
        
        # Amount entry
        self.amount_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Enter discount amount",
            width=200,
            height=40,
            font=("Segoe UI", 14)
        )
        self.amount_entry.pack(pady=15)
        
        # Action buttons
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=20)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=self.cancel,
            width=120,
            height=40,
            font=("Segoe UI", 13),
            fg_color=COLORS['error'],
            hover_color=COLORS['error_hover']
        )
        cancel_btn.grid(row=0, column=0, padx=5)
        
        # Apply button
        apply_btn = ctk.CTkButton(
            buttons_frame,
            text="Apply Discount",
            command=self.apply,
            width=120,
            height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['success_hover']
        )
        apply_btn.grid(row=0, column=1, padx=5)
        
        # Set focus
        self.amount_entry.focus()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
    def apply(self):
        """Validate and apply discount"""
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError("Amount must be positive")
                
            if self.discount_type.get() == "percent":
                if amount > 100:
                    raise ValueError("Percentage cannot exceed 100%")
                    
            self.discount_amount = amount
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            
    def cancel(self):
        """Cancel discount application"""
        self.destroy() 

class SuccessDialog(ctk.CTkToplevel):
    """Custom success dialog with animations"""
    
    def __init__(self, parent, message):
        super().__init__(parent)
        
        self.title("Success")
        self.geometry("400x250")
        
        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Create content
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Success icon with animation
        self.icon_label = ctk.CTkLabel(
            frame,
            text="✨",
            font=("Segoe UI Emoji", 48),
            text_color=COLORS['success']
        )
        self.icon_label.pack(pady=10)
        
        # Message
        msg_label = ctk.CTkLabel(
            frame,
            text=message,
            font=("Segoe UI", 14),
            wraplength=300,
            justify="center"
        )
        msg_label.pack(pady=10)
        
        # OK button
        ok_button = ctk.CTkButton(
            frame,
            text="OK",
            command=self.destroy,
            width=100,
            height=35,
            fg_color=COLORS['success'],
            hover_color=COLORS['success_hover']
        )
        ok_button.pack(pady=10)
        
        # Bind escape
        self.bind("<Escape>", lambda e: self.destroy())
        ok_button.focus_set()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Auto-close with fade-out after 2 seconds
        self.after(2000, self.start_fade_out)
        
    def show(self):
        """Show dialog with smooth fade-in animation"""
        try:
            self.attributes('-alpha', 0.0)
            
            def fade_in(alpha=0.0):
                if not self.winfo_exists():
                    return
                if alpha < 1.0:
                    alpha += 0.05  # Smaller steps for smoother animation
                    self.attributes('-alpha', alpha)
                    self.after(10, lambda: fade_in(alpha))
                    
            fade_in()
            
        except Exception as e:
            logger.error(f"Error in dialog fade animation: {e}")
            self.attributes('-alpha', 1.0)  # Ensure dialog is visible
            self.after(2000, self.destroy)  # Still auto-close after delay
        
    def start_fade_out(self):
        """Start fade-out animation"""
        try:
            def fade_out(alpha=1.0):
                if alpha > 0:
                    alpha -= 0.05  # Smaller steps for smoother animation
                    self.attributes('-alpha', alpha)
                    self.after(10, lambda: fade_out(alpha))
            fade_out()
        except Exception as e:
            logger.error(f"Error starting fade-out animation: {e}")
            self.attributes('-alpha', 1.0)  # Ensure dialog is visible
            self.after(2000, self.destroy)  # Still auto-close after delay