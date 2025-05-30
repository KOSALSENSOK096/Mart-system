import customtkinter as ctk
from utils.database import Database
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import matplotlib
from PIL import Image, ImageTk
import os
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from tkinter import messagebox
from utils.font_config import configure_fonts

# Configure logging
logger = logging.getLogger(__name__)

# Define color scheme with gradients and hover states
COLORS = {
    'primary': '#2B60DE',      # Royal Blue
    'primary_dark': '#1E4BB8', # Darker Blue for hover
    'secondary': '#38B6FF',    # Sky Blue
    'accent': '#FF6B6B',       # Coral
    'success': '#4CAF50',      # Green
    'success_dark': '#3D8B40', # Darker Green for hover
    'warning': '#FFA500',      # Orange
    'warning_dark': '#E69500', # Darker Orange for hover
    'background': '#F5F5F5',   # Light Gray
    'card': '#FFFFFF',         # White
    'text': '#333333',         # Dark Gray
    'text_secondary': '#666666' # Medium Gray
}

# Font configurations
FONTS = {
    'title': ('Helvetica', 32, 'bold'),
    'subtitle': ('Helvetica', 16, 'bold'),
    'heading': ('Helvetica', 14, 'bold'),
    'body': ('Helvetica', 12),
    'small': ('Helvetica', 10)
}

class HoverButton(ctk.CTkButton):
    def __init__(self, *args, hover_color=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.hover_color = hover_color
        self.normal_color = kwargs.get('fg_color')
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_enter(self, e):
        if self.hover_color:
            self.configure(fg_color=self.hover_color)

    def on_leave(self, e):
        if self.normal_color:
            self.configure(fg_color=self.normal_color)

class DashboardView:
    def __init__(self, parent, db: Database):
        self.parent = parent
        self.db = db
        
        # Configure color theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Load icons
        self.load_icons()
        
        # Configure fonts for plots
        configure_fonts()
        
        self.create_widgets()
        self.load_data()
        # Start auto-refresh timer (every 5 minutes)
        self.parent.after(300000, self.load_data)

    def load_icons(self):
        # Define icon paths - you'll need to create an 'assets' folder with these icons
        icon_size = (24, 24)
        self.icons = {
            'sales': '📊',
            'revenue': '💰',
            'stock': '📦',
            'warning': '⚠️',
            'refresh': '🔄',
            'chart': '📈',
            'calendar': '📅',
            'trending_up': '📈',
            'trending_down': '📉'
        }

    def create_widgets(self):
        # Main container with gradient background
        self.parent.configure(fg_color=COLORS['background'])
        
        # Create header section
        self.create_header()
        
        # Create main container with two columns
        main_container = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left column - Summary boxes and alerts
        left_column = ctk.CTkFrame(main_container, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=10)
        
        # Create sections
        self.create_summary_section(left_column)
        self.create_low_stock_section(left_column)
        
        # Right column - Charts and additional info
        right_column = ctk.CTkFrame(main_container, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True, padx=10)
        
        self.create_charts_section(right_column)

    def create_header(self):
        # Header container
        header = ctk.CTkFrame(self.parent, fg_color=COLORS['card'], height=100)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)
        
        # Left side - Title and timestamp
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)
        
        title = ctk.CTkLabel(
            title_frame,
            text="Store Dashboard",
            font=FONTS['title'],
            text_color=COLORS['primary']
        )
        title.pack(anchor="w")
        
        self.timestamp_label = ctk.CTkLabel(
            title_frame,
            text="Last updated: Never",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        )
        self.timestamp_label.pack(anchor="w")
        
        # Right side - Refresh button
        refresh_btn = HoverButton(
            header,
            text="Refresh Data",
            font=FONTS['body'],
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_dark'],
            command=self.load_data
        )
        refresh_btn.pack(side="right", padx=20, pady=10)

    def create_summary_section(self, parent):
        # Summary section title
        section_title = ctk.CTkLabel(
            parent,
            text="Key Metrics",
            font=FONTS['subtitle'],
            text_color=COLORS['text']
        )
        section_title.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Summary boxes container
        summary_frame = ctk.CTkFrame(parent, fg_color="transparent")
        summary_frame.pack(fill="x", pady=5)
        
        # Create summary boxes with hover effect
        self.sales_box = self.create_summary_box(
            summary_frame,
            "Today's Sales",
            "0",
            self.icons['sales'],
            COLORS['primary'],
            COLORS['primary_dark']
        )
        
        self.revenue_box = self.create_summary_box(
            summary_frame,
            "Today's Revenue",
            "$0",
            self.icons['revenue'],
            COLORS['success'],
            COLORS['success_dark']
        )
        
        self.stock_box = self.create_summary_box(
            summary_frame,
            "Low Stock Items",
            "0",
            self.icons['warning'],
            COLORS['warning'],
            COLORS['warning_dark']
        )

    def create_summary_box(self, parent, title, value, icon, color, hover_color):
        frame = ctk.CTkFrame(
            parent,
            corner_radius=15,
            fg_color=COLORS['card'],
            border_width=2,
            border_color=color
        )
        frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Add hover effect
        frame.bind('<Enter>', lambda e: frame.configure(border_color=hover_color))
        frame.bind('<Leave>', lambda e: frame.configure(border_color=color))
        
        # Icon and title container
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        # Icon with background
        icon_label = ctk.CTkLabel(
            header_frame,
            text=icon,
            font=FONTS['heading'],
            width=30,
            height=30,
            corner_radius=8,
            fg_color=color
        )
        icon_label.pack(side="left", padx=5)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=FONTS['heading'],
            text_color=color
        )
        title_label.pack(side="left", padx=5)
        
        # Value
        value_frame = ctk.CTkFrame(frame, fg_color="transparent")
        value_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        value_label = ctk.CTkLabel(
            value_frame,
            text=value,
            font=('Helvetica', 24, 'bold'),
            text_color=COLORS['text']
        )
        value_label.pack(side="left", padx=5)
        
        return value_label

    def create_low_stock_section(self, parent):
        # Section container with shadow effect
        section_frame = ctk.CTkFrame(
            parent,
            corner_radius=15,
            fg_color=COLORS['card'],
            border_width=2,
            border_color=COLORS['warning']
        )
        section_frame.pack(fill="both", expand=True, pady=10)
        
        # Header with icon
        header_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)
        
        icon_label = ctk.CTkLabel(
            header_frame,
            text=self.icons['warning'],
            font=FONTS['heading'],
            width=30,
            height=30,
            corner_radius=8,
            fg_color=COLORS['warning']
        )
        icon_label.pack(side="left", padx=5)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Low Stock Alerts",
            font=FONTS['subtitle'],
            text_color=COLORS['warning']
        )
        title_label.pack(side="left", padx=5)
        
        # Create styled Treeview
        from tkinter import ttk
        style = ttk.Style()
        
        # Configure Treeview style
        style.configure(
            "Dashboard.Treeview",
            background=COLORS['card'],
            foreground=COLORS['text'],
            fieldbackground=COLORS['card'],
            rowheight=40,
            font=FONTS['body']
        )
        
        style.configure(
            "Dashboard.Treeview.Heading",
            background=COLORS['primary'],
            foreground="white",
            relief="flat",
            font=FONTS['heading']
        )
        
        # Create Treeview
        columns = ("Product", "Category", "Stock", "Min Stock", "Status")
        self.low_stock_tree = ttk.Treeview(
            section_frame,
            columns=columns,
            show="headings",
            height=5,
            style="Dashboard.Treeview"
        )
        
        # Configure columns
        column_widths = {
            "Product": 200,
            "Category": 150,
            "Stock": 100,
            "Min Stock": 100,
            "Status": 100
        }
        
        for col, width in column_widths.items():
            self.low_stock_tree.heading(col, text=col)
            self.low_stock_tree.column(col, width=width, anchor="center")
        
        self.low_stock_tree.pack(fill="both", expand=True, padx=15, pady=10)

    def create_charts_section(self, parent):
        """Create charts with proper font configuration"""
        try:
            # Create figure with proper DPI and font settings
            self.fig = Figure(figsize=(8, 10), dpi=100)
            self.fig.set_facecolor(self.parent.cget('fg_color'))
            
            # Create subplots
            self.ax1 = self.fig.add_subplot(211)
            self.ax2 = self.fig.add_subplot(212)
            
            # Configure subplot styling
            for ax in [self.ax1, self.ax2]:
                ax.set_facecolor(self.parent.cget('fg_color'))
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['right'].set_color('white')
                ax.spines['left'].set_color('white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                ax.title.set_color('white')
            
            # Create canvas
            self.canvas = FigureCanvasTkAgg(self.fig, parent)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            logger.error(f"Failed to create charts: {e}")
            self.show_error_message("Failed to create charts")

    def load_data(self):
        try:
            # Update timestamp with animation
            if hasattr(self, 'timestamp_label') and self.timestamp_label.winfo_exists():
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.timestamp_label.configure(
                    text=f"Last updated: {current_time}",
                    text_color=COLORS['primary']
                )
                
                def reset_timestamp_color():
                    if self.timestamp_label.winfo_exists():
                        self.timestamp_label.configure(text_color=COLORS['text_secondary'])
                        
                self.parent.after(1000, reset_timestamp_color)
            
            # Get today's sales summary
            summary = self.db.get_daily_sales_summary()
            if summary:
                # Animate value changes
                self._animate_value_change(
                    self.sales_box,
                    str(summary['total_sales'] or 0)
                )
                self._animate_value_change(
                    self.revenue_box,
                    f"${summary['total_revenue'] or 0:,.2f}"
                )
            
            # Get low stock items
            low_stock = self.db.get_low_stock_products()
            self._animate_value_change(
                self.stock_box,
                str(len(low_stock))
            )
            
            # Update low stock tree with status indicators
            for item in self.low_stock_tree.get_children():
                self.low_stock_tree.delete(item)
            
            for i, product in enumerate(low_stock):
                stock_level = product['stock']
                min_stock = product['min_stock']
                
                # Calculate status and icon
                if stock_level == 0:
                    status = "❌ Out"
                    tag = 'critical'
                elif stock_level <= min_stock * 0.5:
                    status = "⚠️ Critical"
                    tag = 'warning'
                else:
                    status = "⚡ Low"
                    tag = 'low'
                
                self.low_stock_tree.insert(
                    "",
                    "end",
                    values=(
                        product['name'],
                        product['category_name'] or "No Category",
                        f"{stock_level:,}",
                        f"{min_stock:,}",
                        status
                    ),
                    tags=(tag,)
                )
            
            # Configure row colors and hover effect
            self.low_stock_tree.tag_configure('critical', background='#FFE5E5')
            self.low_stock_tree.tag_configure('warning', background='#FFF3E5')
            self.low_stock_tree.tag_configure('low', background='#F5F5F5')
            
            # Update charts with animation
            self.update_charts()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dashboard data: {str(e)}")

    def _animate_value_change(self, label, new_value):
        """Safely animate value change with widget existence check"""
        if not hasattr(self, 'parent') or not self.parent.winfo_exists():
            return
            
        if not label.winfo_exists():
            return
            
        try:
            label.configure(text_color=COLORS['primary'])
            label.configure(text=new_value)
            
            def reset_color():
                if label.winfo_exists():  # Check again before resetting color
                    label.configure(text_color=COLORS['text'])
                    
            self.parent.after(1000, reset_color)
        except Exception as e:
            logger.error(f"Failed to animate value change: {e}")

    def update_charts(self):
        try:
            # Clear previous plots
            self.ax1.clear()
            self.ax2.clear()
            
            # Sales trend for last 7 days
            query = """
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as num_sales,
                    SUM(total_amount) as total_revenue
                FROM sales
                WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date
            """
            
            try:
                sales_data = self.db.execute_query(query)
                if not sales_data:
                    logger.warning("No sales data available for the last 7 days")
                    sales_data = []
            except Exception as e:
                logger.error(f"Failed to fetch sales data: {e}")
                sales_data = []
            
            dates = [row['date'].strftime('%Y-%m-%d') for row in sales_data]
            revenues = [float(row['total_revenue'] or 0) for row in sales_data]
            
            # Create gradient color for bars
            gradient_colors = []
            for i in range(len(dates)):
                alpha = 0.5 + (i * 0.5 / len(dates))
                gradient_colors.append(COLORS['primary'])
            
            # Plot with improved styling
            if dates and revenues:
                bars = self.ax1.bar(dates, revenues, color=gradient_colors, alpha=0.7)
                
                # Add trend line
                if len(revenues) > 1:
                    try:
                        z = np.polyfit(range(len(revenues)), revenues, 1)
                        p = np.poly1d(z)
                        self.ax1.plot(range(len(revenues)), p(range(len(revenues))),
                                    "r--", alpha=0.8, color=COLORS['accent'])
                    except Exception as e:
                        logger.error(f"Failed to create trend line: {e}")
                
                self.ax1.set_title('Revenue Trend (Last 7 Days)',
                                pad=20, fontsize=12, fontweight='bold')
                self.ax1.set_ylabel('Revenue ($)', fontsize=10)
                
                # Add value labels with arrows for significant changes
                prev_height = None
                for i, bar in enumerate(bars):
                    try:
                        height = bar.get_height()
                        self.ax1.text(
                            bar.get_x() + bar.get_width()/2.,
                            height,
                            f'${height:,.0f}',
                            ha='center',
                            va='bottom',
                            fontsize=8
                        )
                        
                        if prev_height is not None:
                            if height > prev_height:
                                self.ax1.text(
                                    bar.get_x() + bar.get_width()/2.,
                                    height,
                                    '↑',
                                    ha='center',
                                    va='bottom',
                                    color='green',
                                    fontsize=10
                                )
                            elif height < prev_height:
                                self.ax1.text(
                                    bar.get_x() + bar.get_width()/2.,
                                    height,
                                    '↓',
                                    ha='center',
                                    va='bottom',
                                    color='red',
                                    fontsize=10
                                )
                        
                        prev_height = height
                    except Exception as e:
                        logger.error(f"Failed to add value label: {e}")
                        continue
            else:
                self.ax1.text(
                    0.5, 0.5,
                    'No sales data available',
                    ha='center',
                    va='center',
                    fontsize=12,
                    color=COLORS['text_secondary'],
                    transform=self.ax1.transAxes
                )
            
            plt.setp(self.ax1.xaxis.get_majorticklabels(),
                    rotation=45, ha='right')
            
            # Top 5 selling products with improved visualization
            query = """
                SELECT 
                    p.name,
                    SUM(sd.quantity) as total_quantity,
                    SUM(sd.quantity * p.price) as total_revenue,
                    COUNT(DISTINCT s.id) as num_transactions
                FROM sales s
                JOIN sales_details sd ON s.id = sd.sale_id
                JOIN products p ON sd.product_id = p.id
                WHERE s.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY p.id, p.name
                ORDER BY total_quantity DESC
                LIMIT 5
            """
            
            try:
                product_data = self.db.execute_query(query)
                if not product_data:
                    logger.warning("No product sales data available for the last 30 days")
                    product_data = []
            except Exception as e:
                logger.error(f"Failed to fetch product data: {e}")
                product_data = []
            
            if product_data:
                products = [row['name'] for row in product_data]
                quantities = [int(row['total_quantity']) for row in product_data]
                revenues = [float(row['total_revenue']) for row in product_data]
                
                # Create horizontal bars with gradient colors
                bars = self.ax2.barh(
                    products,
                    quantities,
                    color=COLORS['secondary'],
                    alpha=0.7
                )
                
                self.ax2.set_title('Top 5 Products by Sales Volume (30 Days)',
                                pad=20, fontsize=12, fontweight='bold')
                self.ax2.set_xlabel('Units Sold', fontsize=10)
                
                # Add value labels and revenue information
                for i, bar in enumerate(bars):
                    try:
                        width = bar.get_width()
                        revenue = revenues[i]
                        
                        # Add quantity label
                        self.ax2.text(
                            width + (max(quantities) * 0.02),  # Add small offset instead of padding
                            bar.get_y() + bar.get_height()/2.,
                            f'{int(width):,} units (${revenue:,.2f})',
                            ha='left',
                            va='center',
                            fontsize=8
                        )
                    except Exception as e:
                        logger.error(f"Failed to add product label: {e}")
                        continue
            else:
                self.ax2.text(
                    0.5, 0.5,
                    'No product data available',
                    ha='center',
                    va='center',
                    fontsize=12,
                    color=COLORS['text_secondary'],
                    transform=self.ax2.transAxes
                )
            
            # Improve overall chart appearance
            self.fig.set_facecolor(COLORS['card'])
            for ax in [self.ax1, self.ax2]:
                ax.grid(True, linestyle='--', alpha=0.3)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.set_facecolor(COLORS['card'])
            
            # Adjust layout and redraw
            plt.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Failed to update charts: {e}")
            messagebox.showerror("Error", f"Failed to update charts: {str(e)}")
            
            # Show error message in charts
            for ax in [self.ax1, self.ax2]:
                ax.clear()
                ax.text(
                    0.5, 0.5,
                    'Error loading chart data',
                    ha='center',
                    va='center',
                    fontsize=12,
                    color=COLORS['error'],
                    transform=ax.transAxes
                )
            
            try:
                plt.tight_layout()
                self.canvas.draw()
            except Exception as draw_error:
                logger.error(f"Failed to draw error message: {draw_error}")

    def show_error_message(self, message):
        """Show error message to user"""
        error_label = ctk.CTkLabel(
            self.parent,
            text=message,
            text_color="red",
            font=("Arial", 12)
        )
        error_label.pack(pady=20) 