import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
from utils.database import Database
import bcrypt
import os
import subprocess
from datetime import datetime
import platform
import socket
import json
import uuid
import csv

class SettingsView:
    def __init__(self, parent, db: Database):
        self.parent = parent
        self.db = db
        self.theme_color = "#1f538d"  # Modern blue
        self.accent_color = "#2980b9"  # Lighter blue
        self.success_color = "#27ae60"  # Green
        self.warning_color = "#f39c12"  # Orange
        self.error_color = "#c0392b"    # Red
        
        self.create_widgets()
        self.load_login_history()

    def create_widgets(self):
        # Modern title with accent bar
        title_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        title_frame.pack(fill="x", pady=(20, 10))
        
        accent_bar = ctk.CTkFrame(title_frame, height=3, fg_color=self.accent_color)
        accent_bar.pack(fill="x", padx=50)
        
        title = ctk.CTkLabel(title_frame, text="⚙️ System Settings", 
                            font=("Helvetica", 28, "bold"))
        title.pack(pady=(10, 5))
        
        subtitle = ctk.CTkLabel(title_frame, 
                              text="Manage your security and system preferences",
                              font=("Helvetica", 12),
                              text_color="gray")
        subtitle.pack(pady=(0, 10))
        
        # Main container with tabs
        self.tab_view = ctk.CTkTabview(self.parent)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add tabs
        security_tab = self.tab_view.add("🔒 Security")
        system_tab = self.tab_view.add("💻 System Info")
        backup_tab = self.tab_view.add("💾 Backup")
        activity_tab = self.tab_view.add("📊 Activity")
        
        # Create sections in each tab
        self.create_security_section(security_tab)
        self.create_system_section(system_tab)
        self.create_backup_section(backup_tab)
        self.create_activity_section(activity_tab)

    def create_security_section(self, parent):
        # Password change frame with modern design
        password_frame = ctk.CTkFrame(parent)
        password_frame.pack(fill="x", pady=10, padx=20)
        
        header_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(header_frame, text="🔐 Password Security",
                    font=("Helvetica", 18, "bold")).pack(side="left")
        
        strength_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        strength_frame.pack(fill="x", padx=15, pady=5)
        
        # Password fields with icons
        fields = [
            ("🔑 Current Password:", "current_password"),
            ("🆕 New Password:", "new_password"),
            ("✅ Confirm Password:", "confirm_password")
        ]
        
        for label_text, attr_name in fields:
            field_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
            field_frame.pack(fill="x", padx=15, pady=5)
            
            ctk.CTkLabel(field_frame, text=label_text,
                        font=("Helvetica", 12)).pack(side="left")
            
            entry = ctk.CTkEntry(field_frame, show="•", width=200,
                               placeholder_text="Enter password")
            entry.pack(side="right")
            setattr(self, attr_name, entry)
        
        # Password requirements
        req_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        req_frame.pack(fill="x", padx=15, pady=10)
        
        requirements = [
            "At least 8 characters long",
            "Contains uppercase & lowercase letters",
            "Contains numbers",
            "Contains special characters"
        ]
        
        for req in requirements:
            ctk.CTkLabel(req_frame, text=f"• {req}",
                        font=("Helvetica", 10),
                        text_color="gray").pack(anchor="w")
        
        # Stylish change button
        button_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkButton(button_frame, text="Update Password",
                     command=self.change_password,
                     font=("Helvetica", 12, "bold"),
                     fg_color=self.theme_color,
                     hover_color=self.accent_color).pack(side="right")

    def create_system_section(self, parent):
        # System information with modern cards
        info_frame = ctk.CTkFrame(parent)
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # System specs
        specs = self.get_system_info()
        for title, value in specs.items():
            card = ctk.CTkFrame(info_frame)
            card.pack(fill="x", pady=5, padx=10)
            
            ctk.CTkLabel(card, text=title,
                        font=("Helvetica", 12, "bold")).pack(pady=(10,0), padx=10)
            
            ctk.CTkLabel(card, text=str(value),
                        font=("Helvetica", 10),
                        text_color="gray").pack(pady=(0,10), padx=10)

    def create_activity_section(self, parent):
        """Create enhanced activity section with modern styling"""
        # Main container with gradient effect
        history_frame = ctk.CTkFrame(parent, fg_color=self.theme_color)
        history_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Header with stats
        header_frame = ctk.CTkFrame(history_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(15,5), padx=15)
        
        # Title with icon
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")
        
        ctk.CTkLabel(title_frame, 
                    text="📊 Login Activity Dashboard",
                    font=("Helvetica", 20, "bold"),
                    text_color="white").pack(side="left")
        
        # Stats panel
        stats_frame = ctk.CTkFrame(history_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10, padx=15)
        
        # Create stat boxes
        self.create_stat_box(stats_frame, "Total Logins", "🔢", self.get_total_logins())
        self.create_stat_box(stats_frame, "Success Rate", "📈", self.get_success_rate())
        self.create_stat_box(stats_frame, "Last Login", "🕒", self.get_last_login())
        
        # Filter section
        filter_frame = ctk.CTkFrame(history_frame, fg_color="transparent")
        filter_frame.pack(fill="x", pady=5, padx=15)
        
        # Search box
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(filter_frame,
                                  placeholder_text="Search login history...",
                                  width=200,
                                  textvariable=self.search_var)
        search_entry.pack(side="left", padx=5)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(filter_frame,
                                  text="🔄 Refresh",
                                  command=self.load_login_history,
                                  width=100,
                                  fg_color=self.accent_color,
                                  hover_color=self.theme_color)
        refresh_btn.pack(side="right", padx=5)
        
        # Export button
        export_btn = ctk.CTkButton(filter_frame,
                                 text="📥 Export",
                                 command=self.export_history,
                                 width=100,
                                 fg_color=self.success_color,
                                 hover_color=self.theme_color)
        export_btn.pack(side="right", padx=5)
        
        # Create modern table
        table_frame = ctk.CTkFrame(history_frame, fg_color="#ffffff")
        table_frame.pack(fill="both", expand=True, pady=10, padx=15)
        
        # Define columns
        columns = ("Date", "Time", "Username", "IP Address", "Location", "Device", "Browser", "Status")
        self.activity_tree = ttk.Treeview(table_frame, 
                                        columns=columns, 
                                        show="headings",
                                        style="Custom.Treeview")
        
        # Configure modern style
        style = ttk.Style()
        style.configure("Custom.Treeview",
                       background="#ffffff",
                       foreground="#333333",
                       rowheight=30,
                       fieldbackground="#ffffff")
        style.configure("Custom.Treeview.Heading",
                       background=self.theme_color,
                       foreground="white",
                       relief="flat")
        style.map("Custom.Treeview",
                 background=[("selected", self.accent_color)],
                 foreground=[("selected", "#ffffff")])
        
        # Configure columns
        column_widths = {
            "Date": 100,
            "Time": 100,
            "Username": 120,
            "IP Address": 120,
            "Location": 150,
            "Device": 150,
            "Browser": 120,
            "Status": 80
        }
        
        for col in columns:
            self.activity_tree.heading(col, 
                                     text=col,
                                     command=lambda c=col: self.sort_treeview(c))
            self.activity_tree.column(col, width=column_widths.get(col, 100))
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.activity_tree.yview)
        x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.activity_tree.xview)
        self.activity_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack scrollbars and tree
        self.activity_tree.pack(side="left", fill="both", expand=True)
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        
        # Bind search
        self.search_var.trace("w", self.filter_history)
        
        # Initial load
        self.load_login_history()

    def create_stat_box(self, parent, title, icon, value):
        """Create a modern stat box"""
        box = ctk.CTkFrame(parent, fg_color=self.accent_color)
        box.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        
        ctk.CTkLabel(box,
                    text=f"{icon} {title}",
                    font=("Helvetica", 12),
                    text_color="white").pack(pady=(10,0))
        
        ctk.CTkLabel(box,
                    text=str(value),
                    font=("Helvetica", 20, "bold"),
                    text_color="white").pack(pady=(0,10))

    def get_total_logins(self):
        """Get total number of login attempts"""
        try:
            query = "SELECT COUNT(*) as total FROM login_history"
            result = self.db.execute_query(query)
            return result[0]['total'] if result else 0
        except Exception:
            return 0

    def get_success_rate(self):
        """Calculate login success rate"""
        try:
            query = """
                SELECT 
                    ROUND(
                        (SUM(CASE WHEN status = TRUE THEN 1 ELSE 0 END) * 100.0) / 
                        COUNT(*)
                    , 1) as rate
                FROM login_history
            """
            result = self.db.execute_query(query)
            return f"{result[0]['rate']}%" if result and result[0]['rate'] is not None else "0%"
        except Exception:
            return "0%"

    def get_last_login(self):
        """Get last successful login time"""
        try:
            query = """
                SELECT created_at 
                FROM login_history 
                WHERE status = TRUE 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            result = self.db.execute_query(query)
            return result[0]['created_at'].strftime('%Y-%m-%d %H:%M') if result else "Never"
        except Exception:
            return "Never"

    def sort_treeview(self, col):
        """Sort treeview by column"""
        items = [(self.activity_tree.set(item, col), item) for item in self.activity_tree.get_children("")]
        items.sort(reverse=getattr(self, "sort_reverse", False))
        
        for index, (_, item) in enumerate(items):
            self.activity_tree.move(item, "", index)
        
        self.sort_reverse = not getattr(self, "sort_reverse", False)
        
        # Update column headers
        for column in self.activity_tree["columns"]:
            self.activity_tree.heading(column, text=column.replace("▼", "").replace("▲", ""))
        self.activity_tree.heading(col, 
                                 text=f"{col} {'▼' if self.sort_reverse else '▲'}")

    def filter_history(self, *args):
        """Filter login history based on search"""
        search_term = self.search_var.get().lower()
        self.load_login_history(search_term)

    def load_login_history(self, search_term=""):
        """Load and display login history with enhanced details"""
        try:
            # Clear existing items
            for item in self.activity_tree.get_children():
                self.activity_tree.delete(item)
            
            # Get login history from database with user info
            query = """
                SELECT 
                    lh.created_at,
                    u.username,
                    lh.ip_address,
                    lh.device_info,
                    lh.status,
                    lh.browser_info,
                    lh.location
                FROM login_history lh
                LEFT JOIN users u ON lh.user_id = u.id
                WHERE 
                    u.username LIKE %s OR
                    lh.ip_address LIKE %s OR
                    lh.device_info LIKE %s
                ORDER BY lh.created_at DESC
                LIMIT 100
            """
            
            search_pattern = f"%{search_term}%"
            history = self.db.execute_query(query, 
                                         (search_pattern, search_pattern, search_pattern))
            
            for entry in history:
                # Parse device info
                device_info = json.loads(entry['device_info']) if entry['device_info'] else {}
                browser_info = entry['browser_info'] or "Unknown"
                location = entry['location'] or "Unknown"
                
                # Format date and time
                date = entry['created_at'].strftime('%Y-%m-%d')
                time = entry['created_at'].strftime('%H:%M:%S')
                
                # Insert with all details
                self.activity_tree.insert("", "end", values=(
                    date,
                    time,
                    entry['username'] or "Unknown",
                    entry['ip_address'],
                    location,
                    device_info.get('device', 'Unknown'),
                    browser_info,
                    "✅ Success" if entry['status'] else "❌ Failed"
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load login history: {str(e)}")

    def export_history(self):
        """Export login history to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Login History"
            )
            
            if not filename:
                return
                
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                # Write headers
                headers = [col for col in self.activity_tree["columns"]]
                writer.writerow(headers)
                
                # Write data
                for item in self.activity_tree.get_children():
                    values = [self.activity_tree.set(item, col) for col in headers]
                    writer.writerow(values)
                    
            messagebox.showinfo("Success", "Login history exported successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export login history: {str(e)}")

    def create_backup_section(self, parent):
        backup_frame = ctk.CTkFrame(parent)
        backup_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Header with icon
        header = ctk.CTkFrame(backup_frame, fg_color="transparent")
        header.pack(fill="x", pady=10)
        
        ctk.CTkLabel(header, text="💾 Database Management",
                    font=("Helvetica", 16, "bold")).pack(side="left")
        
        # Info section
        info_frame = ctk.CTkFrame(backup_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(info_frame,
                    text="Regular backups help protect your data from loss",
                    font=("Helvetica", 12),
                    text_color="gray").pack()
        
        # Backup location
        location_frame = ctk.CTkFrame(backup_frame)
        location_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(location_frame, text="📁 Backup Location:",
                    font=("Helvetica", 12, "bold")).pack(pady=5)
        
        path_label = ctk.CTkLabel(location_frame,
                                text=os.path.abspath("backups"),
                                font=("Helvetica", 10),
                                text_color="gray")
        path_label.pack(pady=5)
        
        # Action buttons
        button_frame = ctk.CTkFrame(backup_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(button_frame, text="Create Backup",
                     command=self.backup_database,
                     fg_color=self.success_color,
                     hover_color=self.theme_color).pack(side="left", padx=5, expand=True)
        
        ctk.CTkButton(button_frame, text="Restore Backup",
                     command=self.restore_database,
                     fg_color=self.warning_color,
                     hover_color=self.theme_color).pack(side="left", padx=5, expand=True)

    def get_system_info(self):
        """Get system information in a structured format"""
        return {
            "🖥️ Operating System": f"{platform.system()} {platform.release()}",
            "💻 Machine": platform.machine(),
            "🌐 Hostname": socket.gethostname(),
            "🔍 Processor": platform.processor(),
            "🆔 Machine ID": str(uuid.getnode()),
            "📂 Working Directory": os.getcwd(),
            "🐍 Python Version": platform.python_version()
        }

    def change_password(self):
        current = self.current_password.get()
        new = self.new_password.get()
        confirm = self.confirm_password.get()
        
        if not all([current, new, confirm]):
            messagebox.showerror("Error", "All fields are required")
            return
        
        if new != confirm:
            messagebox.showerror("Error", "New passwords do not match")
            return
        
        if len(new) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters")
            return
        
        try:
            # Verify current password
            query = "SELECT password FROM users WHERE id = %s"
            result = self.db.execute_query(query, (1,))  # TODO: Get actual user ID
            
            if not result or not bcrypt.checkpw(
                current.encode('utf-8'), 
                result[0]['password'].encode('utf-8')
            ):
                messagebox.showerror("Error", "Current password is incorrect")
                return
            
            # Update password
            hashed = bcrypt.hashpw(new.encode('utf-8'), bcrypt.gensalt())
            query = "UPDATE users SET password = %s WHERE id = %s"
            if self.db.execute_query(query, (hashed.decode('utf-8'), 1)) is not False:
                messagebox.showinfo("Success", "Password changed successfully")
                self.current_password.delete(0, 'end')
                self.new_password.delete(0, 'end')
                self.confirm_password.delete(0, 'end')
            else:
                messagebox.showerror("Error", "Failed to change password")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def backup_database(self):
        try:
            # Create backups directory if it doesn't exist
            if not os.path.exists('backups'):
                os.makedirs('backups')
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backups/mart_db_backup_{timestamp}.sql"
            
            # Get database credentials from config
            from config import DB_CONFIG
            
            # Create backup using mysqldump
            command = [
                'mysqldump',
                '-h', DB_CONFIG['host'],
                '-u', DB_CONFIG['user'],
                f"-p{DB_CONFIG['password']}",
                DB_CONFIG['database'],
                '>', filename
            ]
            
            # Execute backup command
            result = subprocess.run(
                ' '.join(command),
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                messagebox.showinfo(
                    "Success", 
                    f"Database backup created successfully\nLocation: {filename}"
                )
            else:
                raise Exception(result.stderr)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to backup database: {str(e)}")

    def restore_database(self):
        try:
            filename = filedialog.askopenfilename(
                initialdir="backups",
                title="Select backup file",
                filetypes=[("SQL files", "*.sql"), ("All files", "*.*")]
            )
            
            if not filename:
                return
            
            # Confirm restore
            if not messagebox.askyesno(
                "Confirm Restore",
                "This will overwrite the current database. Are you sure?"
            ):
                return
            
            # Get database credentials from config
            from config import DB_CONFIG
            
            # Restore database using mysql
            command = [
                'mysql',
                '-h', DB_CONFIG['host'],
                '-u', DB_CONFIG['user'],
                f"-p{DB_CONFIG['password']}",
                DB_CONFIG['database'],
                '<', filename
            ]
            
            # Execute restore command
            result = subprocess.run(
                ' '.join(command),
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "Database restored successfully")
            else:
                raise Exception(result.stderr)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore database: {str(e)}") 