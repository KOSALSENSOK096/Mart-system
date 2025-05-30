import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from utils.database import Database
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ReportsView:
    def __init__(self, parent, db: Database):
        self.parent = parent
        self.db = db
        
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Title
        title = ctk.CTkLabel(self.parent, text="Reports & Analytics", 
                           font=("Helvetica", 24))
        title.pack(pady=10)
        
        # Date range frame
        date_frame = ctk.CTkFrame(self.parent)
        date_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(date_frame, text="Date Range:").pack(side="left", padx=5)
        
        # Start date
        self.start_date = DateEntry(date_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2)
        self.start_date.pack(side="left", padx=5)
        self.start_date.set_date(datetime.now() - timedelta(days=30))
        
        ctk.CTkLabel(date_frame, text="to").pack(side="left", padx=5)
        
        # End date
        self.end_date = DateEntry(date_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2)
        self.end_date.pack(side="left", padx=5)
        
        # Refresh button
        ctk.CTkButton(date_frame, text="Refresh", 
                     command=self.load_data).pack(side="left", padx=5)
        
        # Export button
        ctk.CTkButton(date_frame, text="Export to Excel", 
                     command=self.export_to_excel).pack(side="right", padx=5)
        
        # Create main container with two columns
        main_container = ctk.CTkFrame(self.parent)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left column - Summary
        left_column = ctk.CTkFrame(main_container)
        left_column.pack(side="left", fill="both", expand=True, padx=5)
        
        # Summary boxes
        summary_frame = ctk.CTkFrame(left_column)
        summary_frame.pack(fill="x", pady=5)
        
        # Total Sales
        self.total_sales_label = self.create_summary_box(
            summary_frame, "Total Sales", "0")
        
        # Total Revenue
        self.total_revenue_label = self.create_summary_box(
            summary_frame, "Total Revenue", "$0")
        
        # Average Sale
        self.avg_sale_label = self.create_summary_box(
            summary_frame, "Average Sale", "$0")
        
        # Sales table
        table_frame = ctk.CTkFrame(left_column)
        table_frame.pack(fill="both", expand=True, pady=5)
        
        columns = ("Date", "Items", "Total")
        self.sales_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        for col in columns:
            self.sales_tree.heading(col, text=col)
            self.sales_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", 
                                command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sales_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Right column - Charts
        right_column = ctk.CTkFrame(main_container)
        right_column.pack(side="right", fill="both", expand=True, padx=5)
        
        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(6, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_column)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def create_summary_box(self, parent, title, value):
        frame = ctk.CTkFrame(parent)
        frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        title_label = ctk.CTkLabel(frame, text=title, font=("Helvetica", 14))
        title_label.pack(pady=5)
        
        value_label = ctk.CTkLabel(frame, text=value, font=("Helvetica", 20, "bold"))
        value_label.pack(pady=5)
        
        return value_label

    def load_data(self):
        try:
            start_date = self.start_date.get_date()
            end_date = self.end_date.get_date()
            
            # Get sales data
            query = """
                SELECT 
                    DATE(s.created_at) as date,
                    COUNT(DISTINCT s.id) as num_sales,
                    SUM(s.total_amount) as total_revenue,
                    COUNT(sd.id) as num_items
                FROM sales s
                LEFT JOIN sales_details sd ON s.id = sd.sale_id
                WHERE DATE(s.created_at) BETWEEN %s AND %s
                GROUP BY DATE(s.created_at)
                ORDER BY date
            """
            
            sales_data = self.db.execute_query(query, (start_date, end_date))
            
            # Update summary
            total_sales = sum(row['num_sales'] for row in sales_data)
            total_revenue = sum(row['total_revenue'] for row in sales_data)
            avg_sale = total_revenue / total_sales if total_sales > 0 else 0
            
            self.total_sales_label.configure(text=str(total_sales))
            self.total_revenue_label.configure(text=f"${total_revenue:.2f}")
            self.avg_sale_label.configure(text=f"${avg_sale:.2f}")
            
            # Update sales table
            for item in self.sales_tree.get_children():
                self.sales_tree.delete(item)
            
            for row in sales_data:
                self.sales_tree.insert("", "end", values=(
                    row['date'].strftime('%Y-%m-%d'),
                    row['num_items'],
                    f"${row['total_revenue']:.2f}"
                ))
            
            # Update charts
            self.update_charts(sales_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def update_charts(self, sales_data):
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        
        # Daily sales chart
        dates = [row['date'] for row in sales_data]
        revenues = [row['total_revenue'] for row in sales_data]
        
        self.ax1.bar(dates, revenues)
        self.ax1.set_title('Daily Sales Revenue')
        self.ax1.set_ylabel('Revenue ($)')
        plt.setp(self.ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Product sales chart
        query = """
            SELECT 
                p.name,
                SUM(sd.quantity) as total_quantity,
                SUM(sd.quantity * sd.price) as total_revenue
            FROM sales s
            JOIN sales_details sd ON s.id = sd.sale_id
            JOIN products p ON sd.product_id = p.id
            WHERE DATE(s.created_at) BETWEEN %s AND %s
            GROUP BY p.id, p.name
            ORDER BY total_revenue DESC
            LIMIT 5
        """
        
        product_data = self.db.execute_query(
            query, 
            (self.start_date.get_date(), self.end_date.get_date())
        )
        
        products = [row['name'] for row in product_data]
        quantities = [row['total_quantity'] for row in product_data]
        
        self.ax2.bar(products, quantities)
        self.ax2.set_title('Top 5 Products by Quantity Sold')
        self.ax2.set_ylabel('Quantity Sold')
        plt.setp(self.ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # Adjust layout and redraw
        plt.tight_layout()
        self.canvas.draw()

    def export_to_excel(self):
        """Export sales data to Excel with enhanced formatting"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not filename:
                return
            
            # Get detailed sales data
            query = """
                SELECT 
                    s.id as sale_id,
                    s.created_at,
                    p.name as product_name,
                    sd.quantity,
                    sd.price,
                    (sd.quantity * sd.price) as total,
                    u.username as sold_by
                FROM sales s
                JOIN sales_details sd ON s.id = sd.sale_id
                JOIN products p ON sd.product_id = p.id
                JOIN users u ON s.user_id = u.id
                WHERE DATE(s.created_at) BETWEEN %s AND %s
                ORDER BY s.created_at
            """
            
            sales_data = self.db.execute_query(
                query, 
                (self.start_date.get_date(), self.end_date.get_date())
            )
            
            # Create Excel writer with xlsxwriter engine
            writer = pd.ExcelWriter(filename, engine='openpyxl')
            
            # Sales details sheet
            df_sales = pd.DataFrame(sales_data)
            df_sales.to_excel(writer, sheet_name='Sales Details', index=False)
            
            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Sales Details']
            
            # Format datetime columns
            df_sales['created_at'] = pd.to_datetime(df_sales['created_at'])
            df_sales['created_at'] = df_sales['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Format currency columns
            df_sales['price'] = df_sales['price'].map('${:,.2f}'.format)
            df_sales['total'] = df_sales['total'].map('${:,.2f}'.format)
            
            # Summary sheet
            summary_data = {
                'Metric': ['Total Sales', 'Total Revenue', 'Average Sale'],
                'Value': [
                    len(set(row['sale_id'] for row in sales_data)),
                    sum(row['total'] for row in sales_data),
                    sum(row['total'] for row in sales_data) / 
                    len(set(row['sale_id'] for row in sales_data))
                    if sales_data else 0
                ]
            }
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Format summary sheet
            worksheet = writer.sheets['Summary']
            df_summary.loc[df_summary['Metric'].isin(['Total Revenue', 'Average Sale']), 'Value'] = \
                df_summary.loc[df_summary['Metric'].isin(['Total Revenue', 'Average Sale']), 'Value'].map('${:,.2f}'.format)
            
            # Product summary sheet
            product_summary = {}
            for row in sales_data:
                if row['product_name'] not in product_summary:
                    product_summary[row['product_name']] = {
                        'quantity': 0,
                        'revenue': 0
                    }
                product_summary[row['product_name']]['quantity'] += row['quantity']
                product_summary[row['product_name']]['revenue'] += row['total']
            
            df_products = pd.DataFrame([
                {
                    'Product': product,
                    'Quantity Sold': data['quantity'],
                    'Revenue': data['revenue']
                }
                for product, data in product_summary.items()
            ])
            
            # Sort by revenue descending
            df_products = df_products.sort_values('Revenue', ascending=False)
            
            # Format revenue column
            df_products['Revenue'] = df_products['Revenue'].map('${:,.2f}'.format)
            
            df_products.to_excel(writer, sheet_name='Product Summary', index=False)
            
            # Save and close
            writer.close()
            
            messagebox.showinfo("Success", "Report exported successfully")
            
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            messagebox.showerror("Error", f"Failed to export report: {str(e)}") 