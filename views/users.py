import customtkinter as ctk
from tkinter import ttk, messagebox
from utils.database import Database
import bcrypt

class UsersView:
    def __init__(self, parent, db: Database):
        self.parent = parent
        self.db = db
        
        self.create_widgets()
        self.load_users()

    def create_widgets(self):
        # Title and toolbar
        toolbar = ctk.CTkFrame(self.parent)
        toolbar.pack(fill="x", padx=20, pady=10)
        
        title = ctk.CTkLabel(toolbar, text="User Management", font=("Helvetica", 24))
        title.pack(side="left", pady=10)
        
        # Add user button
        ctk.CTkButton(toolbar, text="Add User", 
                     command=self.show_user_dialog).pack(side="right", padx=5)
        
        # Users table
        table_frame = ctk.CTkFrame(self.parent)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create Treeview
        columns = ("ID", "Username", "Role", "Created At")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", 
                                command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_double_click)

    def load_users(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get users from database
        query = "SELECT id, username, role, created_at FROM users"
        users = self.db.execute_query(query)
        
        # Insert users into tree
        for user in users:
            self.tree.insert("", "end", values=(
                user['id'],
                user['username'],
                user['role'],
                user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            ))

    def show_user_dialog(self, user=None):
        dialog = UserDialog(self.parent, self.db, user)
        self.parent.wait_window(dialog)
        self.load_users()

    def on_double_click(self, event):
        item = self.tree.selection()[0]
        user_id = self.tree.item(item)['values'][0]
        
        # Get user details from database
        query = "SELECT * FROM users WHERE id = %s"
        result = self.db.execute_query(query, (user_id,))
        
        if result:
            self.show_user_dialog(result[0])

class UserDialog(ctk.CTkToplevel):
    def __init__(self, parent, db: Database, user=None):
        super().__init__(parent)
        
        self.db = db
        self.user = user
        
        self.title("Edit User" if user else "Add User")
        self.geometry("400x400")
        
        # Center window
        self.center_window()
        
        # Create widgets
        self.create_widgets()
        
        # Load user data if editing
        if user:
            self.load_user_data()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Username
        ctk.CTkLabel(main_frame, text="Username:").pack(pady=5)
        self.username_entry = ctk.CTkEntry(main_frame)
        self.username_entry.pack(fill="x", pady=5)
        
        # Password
        ctk.CTkLabel(main_frame, text="Password:").pack(pady=5)
        self.password_entry = ctk.CTkEntry(main_frame, show="*")
        self.password_entry.pack(fill="x", pady=5)
        
        if self.user:
            ctk.CTkLabel(main_frame, 
                        text="Leave password blank to keep current").pack(pady=5)
        
        # Role
        ctk.CTkLabel(main_frame, text="Role:").pack(pady=5)
        self.role_var = ctk.StringVar(value="staff")
        self.role_dropdown = ctk.CTkOptionMenu(
            main_frame,
            variable=self.role_var,
            values=["admin", "staff"]
        )
        self.role_dropdown.pack(fill="x", pady=5)
        
        # Buttons
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(buttons_frame, text="Save", 
                     command=self.save_user).pack(side="left", padx=5, expand=True)
        
        if self.user:  # Show delete button only when editing
            ctk.CTkButton(buttons_frame, text="Delete", 
                         command=self.delete_user,
                         fg_color="red").pack(side="left", padx=5, expand=True)
        
        ctk.CTkButton(buttons_frame, text="Cancel", 
                     command=self.destroy).pack(side="left", padx=5, expand=True)

    def load_user_data(self):
        self.username_entry.insert(0, self.user['username'])
        self.role_var.set(self.user['role'])

    def save_user(self):
        try:
            username = self.username_entry.get()
            password = self.password_entry.get()
            role = self.role_var.get()
            
            if not username:
                messagebox.showerror("Error", "Username is required")
                return
            
            if self.user:
                # Update existing user
                if password:  # Only update password if provided
                    hashed = bcrypt.hashpw(
                        password.encode('utf-8'), 
                        bcrypt.gensalt()
                    ).decode('utf-8')
                    query = """
                        UPDATE users 
                        SET username = %s, password = %s, role = %s 
                        WHERE id = %s
                    """
                    success = self.db.execute_query(
                        query, 
                        (username, hashed, role, self.user['id'])
                    )
                else:
                    query = """
                        UPDATE users 
                        SET username = %s, role = %s 
                        WHERE id = %s
                    """
                    success = self.db.execute_query(
                        query, 
                        (username, role, self.user['id'])
                    )
            else:
                # Create new user
                if not password:
                    messagebox.showerror("Error", "Password is required")
                    return
                
                success = self.db.create_user(username, password, role)
            
            if success is not False:  # None is also considered success for execute_query
                messagebox.showinfo(
                    "Success", 
                    "User updated successfully" if self.user else "User created successfully"
                )
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to save user")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def delete_user(self):
        if not messagebox.askyesno("Confirm Delete", 
                                 "Are you sure you want to delete this user?"):
            return
        
        try:
            query = "DELETE FROM users WHERE id = %s"
            if self.db.execute_query(query, (self.user['id'],)) is not False:
                messagebox.showinfo("Success", "User deleted successfully")
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to delete user")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}") 