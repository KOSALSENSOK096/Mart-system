from utils.pdf_utils import generate_receipt
import os

def test_receipt_generation():
    """Test receipt generation with sample data"""
    # Sample sale data
    sale_data = {
        'receipt_number': 'TEST001',
        'items': [
            {
                'name': 'Test Product 1',
                'quantity': 2,
                'price': 10.99
            },
            {
                'name': 'Test Product 2',
                'quantity': 1,
                'price': 25.50
            },
            {
                'name': 'Test Product with Very Long Name That Should Be Truncated',
                'quantity': 3,
                'price': 5.99
            }
        ],
        'tax_rate': 0.08,
        'discount': 5.00,
        'payment_method': 'card',
        'amount_paid': 100.00,
        'staff_name': 'John Doe'
    }

    try:
        # Generate receipt
        print("Generating test receipt...")
        filepath = generate_receipt(sale_data)
        
        # Verify file was created
        if os.path.exists(filepath):
            print(f"✅ Receipt generated successfully at: {filepath}")
            
            # Verify file size
            size = os.path.getsize(filepath)
            print(f"📄 File size: {size/1024:.1f}KB")
            
            # Try to open the file
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(filepath)
                else:  # Linux/Mac
                    os.system(f'xdg-open "{filepath}"')
                print("📂 Opening receipt file...")
            except Exception as e:
                print(f"⚠️ Could not open file automatically: {e}")
                print(f"📍 File location: {filepath}")
        else:
            print("❌ Failed to generate receipt")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_receipt_generation() 