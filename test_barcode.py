import customtkinter as ctk
from utils.barcode_utils import create_barcode_scanner, BarcodeManager
from utils.styles import setup_theme

def on_barcode_received(code):
    print(f"✅ Received barcode: {code}")
    
def main():
    # Initialize theme
    setup_theme()
    
    # Initialize the main window
    root = ctk.CTk()
    root.title("Barcode Test")
    root.geometry("400x300")
    
    # Center window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 300) // 2
    root.geometry(f"400x300+{x}+{y}")
    
    # Create a test button with proper styling
    test_btn = ctk.CTkButton(
        root,
        text="🔍 Open Barcode Scanner",
        command=lambda: create_barcode_scanner(root, on_barcode_received),
        width=200,
        height=45,
        corner_radius=10
    )
    test_btn.pack(pady=40)
    
    # Create barcode manager and test barcode generation
    barcode_mgr = BarcodeManager()
    try:
        # Test generating a barcode
        test_code = "123456789"
        barcode_path = barcode_mgr.generate_barcode(test_code, "Test Product")
        print(f"✅ Successfully generated barcode at: {barcode_path}")
    except Exception as e:
        print(f"❌ Error generating barcode: {e}")
    
    root.mainloop()

if __name__ == "__main__":
    main() 