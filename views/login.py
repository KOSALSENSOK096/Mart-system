import customtkinter as ctk
from tkinter import messagebox
from utils.database import Database
import bcrypt
import socket
import platform
import uuid

class LoginView:
    def __init__(self, parent, db: Database, on_login_success=None):
        self.parent = parent
        self.db = db
        self.on_login_success = on_login_success
        
        # Modern color scheme
        self.theme_color = "#1f538d"
        self.accent_color = "#2980b9"
        self.error_color = "#c0392b"
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main container with gradient background
        self.main_frame = ctk.CTkFrame(self.parent)
        self.main_frame.pack(fill="both", expand=True)
        
        # Login container
        login_frame = ctk.CTkFrame(self.main_frame, 
                                 fg_color="transparent")
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo/Title
        title_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        logo_label = ctk.CTkLabel(title_frame, 
                                text="🏪",
                                font=("Helvetica", 48))
        logo_label.pack()
        
        title = ctk.CTkLabel(title_frame,
                           text="Mart Application",
                           font=("Helvetica", 24, "bold"))
        title.pack()
        
        subtitle = ctk.CTkLabel(title_frame,
                              text="Sign in to continue",
                              font=("Helvetica", 12),
                              text_color="gray")
        subtitle.pack()
        
        # Username field
        username_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        username_frame.pack(fill="x", pady=10)
        
        username_icon = ctk.CTkLabel(username_frame, text="👤")
        username_icon.pack(side="left", padx=5)
        
        self.username_entry = ctk.CTkEntry(username_frame,
                                         placeholder_text="Username",
                                         width=200)
        self.username_entry.pack(side="left", padx=5)
        
        # Password field
        password_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=10)
        
        password_icon = ctk.CTkLabel(password_frame, text="🔑")
        password_icon.pack(side="left", padx=5)
        
        self.password_entry = ctk.CTkEntry(password_frame,
                                         placeholder_text="Password",
                                         show="•",
                                         width=200)
        self.password_entry.pack(side="left", padx=5)
        
        # Login button
        self.login_button = ctk.CTkButton(login_frame,
                                        text="Sign In",
                                        command=self.login,
                                        font=("Helvetica", 12, "bold"),
                                        fg_color=self.theme_color,
                                        hover_color=self.accent_color)
        self.login_button.pack(fill="x", pady=20)
        
        # Version info
        version_label = ctk.CTkLabel(login_frame,
                                   text="Version 1.0.0",
                                   font=("Helvetica", 10),
                                   text_color="gray")
        version_label.pack(pady=(20, 0))
        
        # Bind enter key to login
        self.username_entry.bind("<Return>", lambda e: self.login())
        self.password_entry.bind("<Return>", lambda e: self.login())
    
    def get_device_info(self):
        """Get device information for login tracking"""
        return {
            "os": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "hostname": socket.gethostname(),
            "device_id": str(uuid.getnode())
        }
    
    def record_login_attempt(self, user_id, status):
        """Record login attempt in history"""
        try:
            device_info = str(self.get_device_info())
            ip_address = socket.gethostbyname(socket.gethostname())
            
            query = """
                INSERT INTO login_history 
                (user_id, ip_address, device_info, status)
                VALUES (%s, %s, %s, %s)
            """
            
            self.db.execute_query(query, (user_id, ip_address, device_info, status))
            
        except Exception as e:
            print(f"Failed to record login attempt: {e}")
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        try:
            # Get user from database
            query = "SELECT * FROM users WHERE username = %s"
            result = self.db.execute_query(query, (username,))
            
            if not result:
                self.record_login_attempt(None, False)
                messagebox.showerror("Error", "Invalid username or password")
                return
            
            user = result[0]
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), 
                            user['password'].encode('utf-8')):
                self.record_login_attempt(user['id'], True)
                if self.on_login_success:
                    self.on_login_success(user)
            else:
                self.record_login_attempt(user['id'], False)
                messagebox.showerror("Error", "Invalid username or password")
            
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}") 