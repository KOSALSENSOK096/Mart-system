from fpdf import FPDF
import os
from datetime import datetime
from config import RECEIPT_WIDTH, RECEIPT_MARGIN, COMPANY_NAME, RECEIPT_FOOTER, COMPANY_ADDRESS, COMPANY_CONTACT, RETURN_POLICY
import logging
from copy import deepcopy
import time
import urllib.request
import shutil
import ssl
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

# Define constants
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts')
RECEIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'receipts')

# Font URLs from a reliable source
FONT_URLS = {
    'DejaVuSansCondensed.ttf': 'https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip',
    'DejaVuSansCondensed-Bold.ttf': 'https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip'
}

# Alternative font URLs (backup)
ALTERNATIVE_FONT_URLS = {
    'DejaVuSansCondensed.ttf': 'https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSansCondensed.ttf',
    'DejaVuSansCondensed-Bold.ttf': 'https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSansCondensed-Bold.ttf'
}

def ensure_directories():
    """Ensure required directories exist"""
    for directory in [FONTS_DIR, RECEIPTS_DIR]:
        try:
            os.makedirs(directory, exist_ok=True)
            if not os.access(directory, os.W_OK):
                raise OSError(f"Directory {directory} is not writable")
        except Exception as e:
            logger.error(f"Failed to create/verify directory {directory}: {e}")
            raise

def download_file(url, dest_path, context=None):
    """Download a file with proper error handling"""
    try:
        with urllib.request.urlopen(url, context=context) as response:
            with open(dest_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        return True
    except Exception as e:
        logger.error(f"Failed to download from {url}: {e}")
        return False

def download_fonts():
    """Download required fonts if not present"""
    # Create an SSL context that doesn't verify certificates
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    import zipfile
    import io
    
    # Download zip file once for both fonts
    zip_url = list(FONT_URLS.values())[0]  # Both URLs are the same
    try:
        logger.info("Downloading DejaVu fonts package")
        with urllib.request.urlopen(zip_url, context=context) as response:
            zip_data = response.read()
            
        # Extract fonts from zip
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
            # Extract required fonts
            font_files = {
                'DejaVuSansCondensed.ttf': 'dejavu-fonts-ttf-2.37/ttf/DejaVuSansCondensed.ttf',
                'DejaVuSansCondensed-Bold.ttf': 'dejavu-fonts-ttf-2.37/ttf/DejaVuSansCondensed-Bold.ttf'
            }
            
            for font_file, zip_path in font_files.items():
                font_path = os.path.join(FONTS_DIR, font_file)
                if not os.path.exists(font_path):
                    logger.info(f"Extracting font: {font_file}")
                    try:
                        with zip_file.open(zip_path) as source, open(font_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        logger.info(f"Font extracted successfully: {font_file}")
                    except Exception as e:
                        logger.error(f"Failed to extract {font_file}: {e}")
                        if os.path.exists(font_path):
                            os.remove(font_path)
                        
    except Exception as e:
        logger.error(f"Failed to download font package: {e}")

# Initialize directories and fonts
try:
    ensure_directories()
    download_fonts()
except Exception as e:
    logger.error(f"Failed to initialize PDF utilities: {e}")
    # Don't raise here, let the application continue with fallback fonts

class ReceiptPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format=(90, 200))
        self.set_auto_page_break(True, margin=10)
        self.set_margins(left=5, top=10, right=5)
        
        # Try to add custom fonts, fall back to Arial if necessary
        try:
            self.add_font('DejaVu', '', os.path.join(FONTS_DIR, 'DejaVuSansCondensed.ttf'), uni=True)
            self.add_font('DejaVu', 'B', os.path.join(FONTS_DIR, 'DejaVuSansCondensed-Bold.ttf'), uni=True)
            self.default_font = 'DejaVu'
        except Exception as e:
            logger.warning(f"Failed to load custom fonts, falling back to Arial: {e}")
            self.default_font = 'Arial'
        
        self._set_styles()

    def sanitize_text(self, text):
        """Sanitize text to remove problematic characters"""
        if not text:
            return ""
        # Replace problematic characters with ASCII equivalents
        replacements = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',
            '—': '-',
            '…': '...',
            '•': '*',
            '°': 'deg',
            '©': '(c)',
            '®': '(R)',
            '™': '(TM)',
            '€': 'EUR',
            '£': 'GBP',
            '¥': 'JPY',
            '→': '->',
            '←': '<-',
            '↑': '^',
            '↓': 'v',
            '✓': 'v',
            '✗': 'x',
            '❤': '<3',
            '☺': ':)',
            '☹': ':(',
            '•': '*'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove any remaining non-ASCII characters
        return ''.join(c for c in text if ord(c) < 128)

    def cell(self, w, h=0, txt='', border=0, ln=0, align='', fill=False, link=''):
        """Override cell to handle text encoding"""
        sanitized_txt = self.sanitize_text(txt)
        super().cell(w, h, sanitized_txt, border, ln, align, fill, link)

    def text(self, x, y, txt=''):
        """Override text to handle text encoding"""
        sanitized_txt = self.sanitize_text(txt)
        super().text(x, y, sanitized_txt)

    def multi_cell(self, w, h, txt='', border=0, align='J', fill=False):
        """Override multi_cell to handle text encoding"""
        sanitized_txt = self.sanitize_text(txt)
        super().multi_cell(w, h, sanitized_txt, border, align, fill)

    def set_font(self, family='', style='', size=0):
        """Override set_font to handle fallbacks"""
        try:
            if family == 'DejaVu' and not os.path.exists(os.path.join(FONTS_DIR, 'DejaVuSansCondensed.ttf')):
                super().set_font('Arial', style, size)
            else:
                super().set_font(family, style, size)
        except Exception as e:
            logger.warning(f"Font error, falling back to Arial: {e}")
            super().set_font('Arial', style, size)

    def header(self):
        # Use Unicode-compatible font
        self.set_font('DejaVu', 'B', 12)
        
    def footer(self):
        # Use Unicode-compatible font
        self.set_font('DejaVu', '', 8)

    def _set_styles(self):
        """Define modern, stylish receipt styles"""
        # Enhanced color scheme
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'gray': (128, 128, 128),
            'light_gray': (200, 200, 200),
            'accent': (41, 128, 185),      # Modern blue
            'accent_light': (52, 152, 219), # Lighter blue
            'success': (46, 204, 113),     # Green
            'highlight': (241, 196, 15),   # Yellow
            'subtle': (236, 240, 241)      # Very light gray
        }
        
        # Spacing
        self.line_height = 5
        self.item_spacing = 2
        self.section_spacing = 3
        
        # Font sizes
        self.font_sizes = {
            'title': 14,
            'header': 10,
            'normal': 8,
            'small': 7,
            'tiny': 6
        }

    def safe_set_font(self, family=None, style='', size=0):
        """Safely set font with fallback to Arial"""
        try:
            if family is None:
                family = self.default_font
            self.set_font(family, style, size)
        except Exception as e:
            logger.warning(f"Font error, using Arial: {e}")
            self.set_font('Arial', style, size)

    def _draw_header_design(self):
        """Draw stylish header design elements"""
        # Top border with gradient effect
        y = 5
        for i in range(10):
            self.set_draw_color(*self.colors['accent'])
            self.set_line_width(0.3)
            self.line(5 + i*8, y, 10 + i*8, y)

        # Store icon (shopping bag)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(*self.colors['accent'])
        self.text(35, y + 8, "🛍️")

    def _draw_decorative_bullet(self, x, y, size=1.5):
        """Draw a decorative bullet point"""
        self.set_fill_color(*self.colors['accent'])
        self.circle(x, y, size, 'F')

    def _draw_section_separator(self):
        """Draw a stylish section separator"""
        y = self.get_y()
        # Center line
        self.set_draw_color(*self.colors['light_gray'])
        self.line(10, y, 80, y)
        
        # Decorative elements
        self.set_fill_color(*self.colors['accent'])
        self.circle(10, y, 1, 'F')
        self.circle(80, y, 1, 'F')

    def _draw_rounded_rect(self, x, y, w, h, r, style='F', fill_color=None, stroke_color=None):
        """Draw a rounded rectangle"""
        if fill_color:
            self.set_fill_color(*fill_color)
        if stroke_color:
            self.set_draw_color(*stroke_color)

        k = self.k
        hp = self.h
        # Draw rounded corners
        self.circle(x+r, y+r, r, style)
        self.circle(x+w-r, y+r, r, style)
        self.circle(x+w-r, y+h-r, r, style)
        self.circle(x+r, y+h-r, r, style)
        # Draw connecting rectangles
        self.rect(x+r, y, w-2*r, h, style)
        self.rect(x, y+r, w, h-2*r, style)

    def _draw_gradient_background(self, x, y, w, h, start_color, end_color, steps=20):
        """Draw a vertical gradient background"""
        step_h = h / steps
        for i in range(steps):
            r = start_color[0] + (end_color[0] - start_color[0]) * i / steps
            g = start_color[1] + (end_color[1] - start_color[1]) * i / steps
            b = start_color[2] + (end_color[2] - start_color[2]) * i / steps
            self.set_fill_color(r, g, b)
            self.rect(x, y + (i * step_h), w, step_h + 1, 'F')

    def _draw_stylish_barcode_section(self, receipt_number):
        """Draw a stylish barcode section with modern design elements"""
        # Save current position
        start_y = self.get_y()
        
        # Calculate dimensions
        margin = 5
        section_width = self.w - (2 * margin)
        section_height = 45  # Increased height for better design
        corner_radius = 3
        
        # Draw gradient background with rounded corners
        self._draw_gradient_background(
            margin, start_y,
            section_width, section_height,
            (245, 247, 250),  # Light gray-blue
            (235, 238, 245)   # Slightly darker gray-blue
        )
        
        # Draw rounded rectangle frame
        self._draw_rounded_rect(
            margin, start_y,
            section_width, section_height,
            corner_radius, 'D',
            stroke_color=self.colors['accent']
        )
        
        # Add decorative lines
        line_color = self.colors['accent']
        self.set_draw_color(*line_color)
        self.set_line_width(0.2)
        
        # Draw diagonal lines in corners
        line_length = 5
        # Top left
        self.line(margin + 2, start_y + 2, margin + line_length, start_y + 2)
        self.line(margin + 2, start_y + 2, margin + 2, start_y + line_length)
        # Top right
        self.line(self.w - margin - 2, start_y + 2, self.w - margin - line_length, start_y + 2)
        self.line(self.w - margin - 2, start_y + 2, self.w - margin - 2, start_y + line_length)
        # Bottom left
        self.line(margin + 2, start_y + section_height - 2, margin + line_length, start_y + section_height - 2)
        self.line(margin + 2, start_y + section_height - 2, margin + 2, start_y + section_height - line_length)
        # Bottom right
        self.line(self.w - margin - 2, start_y + section_height - 2, self.w - margin - line_length, start_y + section_height - 2)
        self.line(self.w - margin - 2, start_y + section_height - 2, self.w - margin - 2, start_y + section_height - line_length)

        # Add title with modern styling
        self.ln(4)
        self.safe_set_font(style='B', size=self.font_sizes['small'])
        self.set_text_color(*self.colors['accent'])
        self.cell(0, 4, "SCAN FOR DIGITAL COPY", ln=True, align='C')
        
        # Generate and add barcode
        self.ln(1)
        barcode_data = self.generate_barcode(receipt_number)
        if barcode_data:
            temp_file = os.path.join(RECEIPTS_DIR, f"temp_barcode_{receipt_number}.png")
            try:
                with open(temp_file, 'wb') as f:
                    f.write(barcode_data)
                
                # Calculate barcode dimensions
                max_width = section_width - 10  # Leave some margin
                self.image(
                    temp_file,
                    x=(self.w - max_width) / 2,
                    y=self.get_y(),
                    w=max_width
                )
            finally:
                try:
                    os.remove(temp_file)
                except:
                    pass

        # Add scanning instructions with icon
        self.ln(1)
        self.safe_set_font(size=self.font_sizes['tiny'])
        self.set_text_color(*self.colors['gray'])
        self.cell(0, 3, "📱 Scan with any barcode scanner app", ln=True, align='C')
        
        # Move cursor to end of section
        self.set_y(start_y + section_height + 2)

    def generate_barcode(self, receipt_number):
        """Generate a Code128 barcode for the receipt"""
        try:
            # Create barcode instance
            code128 = barcode.get('code128', receipt_number, writer=ImageWriter())
            
            # Create a BytesIO object to store the image
            fp = BytesIO()
            
            # Save the barcode to the BytesIO object
            code128.write(fp, options={
                'module_width': 0.4,  # Adjust width for better scanning
                'module_height': 10.0,  # Adjust height for better scanning
                'quiet_zone': 3.0,  # Add quiet zone for better scanning
                'font_size': 7,  # Smaller font size for receipt
                'text_distance': 1.0,  # Distance between barcode and text
            })
            
            # Get the image data
            fp.seek(0)
            return fp.read()
            
        except Exception as e:
            logger.error(f"Failed to generate barcode: {e}")
            return None

    def add_barcode(self, receipt_number):
        """Add a barcode to the receipt"""
        try:
            # Generate barcode
            barcode_data = self.generate_barcode(receipt_number)
            if not barcode_data:
                return False
            
            # Save barcode temporarily
            temp_file = os.path.join(RECEIPTS_DIR, f"temp_barcode_{receipt_number}.png")
            with open(temp_file, 'wb') as f:
                f.write(barcode_data)
            
            # Calculate dimensions
            original_width = 80  # Typical barcode width in mm
            max_width = self.w - (2 * RECEIPT_MARGIN)  # Available width
            scale = max_width / original_width
            
            # Add barcode image
            try:
                self.image(temp_file, 
                          x=(self.w - max_width) / 2,  # Center horizontally
                          y=self.get_y(),
                          w=max_width)  # Scale to fit receipt width
                return True
            finally:
                # Clean up temporary file
                try:
                    os.remove(temp_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to add barcode: {e}")
            return False

    def create_receipt(self, sale_data):
        """Create a stylish, modern receipt"""
        try:
            self.add_page()
            
            # Draw header design
            self._draw_header_design()
            
            # Store Information with modern styling
            self.safe_set_font(style='B', size=self.font_sizes['title'])
            self.set_text_color(*self.colors['accent'])
            self.cell(0, 8, COMPANY_NAME, ln=True, align='C')
            
            # Store Details with icons
            self.safe_set_font(size=self.font_sizes['small'])
            self.set_text_color(*self.colors['black'])
            
            # Address
            self.cell(0, self.line_height, COMPANY_ADDRESS['street'], ln=True, align='C')
            self.cell(0, self.line_height, 
                     f"{COMPANY_ADDRESS['city']}, {COMPANY_ADDRESS['state']} {COMPANY_ADDRESS['zip']}", 
                     ln=True, align='C')
            
            # Phone
            self.cell(0, self.line_height, f"Tel: {COMPANY_CONTACT['phone']}", ln=True, align='C')
            
            # Stylish separator
            self.ln(2)
            self._draw_section_separator()
            self.ln(2)
            
            # Receipt Details with modern design
            self.safe_set_font(style='B', size=self.font_sizes['header'])
            self.set_text_color(*self.colors['accent'])
            self.cell(0, 6, '*** SALES RECEIPT ***', ln=True, align='C')
            
            # Receipt info
            self.safe_set_font(size=self.font_sizes['normal'])
            self.set_text_color(*self.colors['black'])
            
            # Two-column layout for receipt details
            self.cell(45, self.line_height, "Receipt #:", align='R')
            self.cell(40, self.line_height, str(sale_data['receipt_number']), ln=True)
            
            self.cell(45, self.line_height, "Date:", align='R')
            self.cell(40, self.line_height, datetime.now().strftime('%Y-%m-%d %H:%M'), ln=True)
            
            if 'staff_name' in sale_data:
                self.cell(45, self.line_height, "Served by:", align='R')
                self.cell(40, self.line_height, str(sale_data['staff_name']), ln=True)
            
            # Stylish separator
            self.ln(2)
            self._draw_section_separator()
            self.ln(2)
            
            # Items table with modern header
            self.safe_set_font(style='B', size=self.font_sizes['normal'])
            self.set_fill_color(*self.colors['accent'])
            self.set_text_color(*self.colors['white'])
            
            # Table headers with background
            self.cell(35, 6, ' Item', 1, 0, 'L', 1)
            self.cell(10, 6, 'Qty', 1, 0, 'C', 1)
            self.cell(20, 6, 'Price', 1, 0, 'R', 1)
            self.cell(20, 6, 'Total', 1, 1, 'R', 1)
            
            # Items with alternating background
            self.set_text_color(*self.colors['black'])
            subtotal = 0
            for i, item in enumerate(sale_data['items']):
                # Alternate row colors
                if i % 2 == 0:
                    self.set_fill_color(*self.colors['subtle'])
                else:
                    self.set_fill_color(*self.colors['white'])
                
                # Handle long item names
                name = str(item['name'])
                if len(name) > 20:
                    name = name[:17] + '...'
                
                # Calculate item total
                item_total = item['quantity'] * item['price']
                subtotal += item_total
                
                # Print item with background
                self.cell(35, 5, f" {name}", 0, 0, 'L', 1)
                self.cell(10, 5, str(item['quantity']), 0, 0, 'C', 1)
                self.cell(20, 5, f"${item['price']:.2f}", 0, 0, 'R', 1)
                self.cell(20, 5, f"${item_total:.2f}", 0, 1, 'R', 1)
            
            # Totals section with modern design
            self.ln(2)
            self._draw_section_separator()
            self.ln(2)
            
            # Subtotal
            self.safe_set_font(size=self.font_sizes['normal'])
            self.cell(60, 5, "Subtotal:", 0, 0, 'R')
            self.cell(25, 5, f"${subtotal:.2f}", 0, 1, 'R')
            
            # Calculate final total
            total = subtotal
            
            # Tax calculation
            if 'tax_rate' in sale_data:
                tax_rate = float(sale_data.get('tax_rate', 0))
                tax_amount = subtotal * tax_rate
                total += tax_amount
                self.cell(60, 5, f"Tax ({tax_rate*100:.1f}%):", 0, 0, 'R')
                self.cell(25, 5, f"${tax_amount:.2f}", 0, 1, 'R')
            
            # Discount
            if 'discount' in sale_data:
                discount = float(sale_data['discount'])
                total -= discount
                self.cell(60, 5, "Discount:", 0, 0, 'R')
                self.cell(25, 5, f"-${discount:.2f}", 0, 1, 'R')
            
            # Final total with highlight
            self.ln(1)
            self.safe_set_font(style='B', size=self.font_sizes['header'])
            self.set_text_color(*self.colors['accent'])
            self.cell(60, 6, "TOTAL:", 0, 0, 'R')
            self.cell(25, 6, f"${total:.2f}", 0, 1, 'R')
            
            # Payment information
            if 'payment_method' in sale_data:
                self.safe_set_font(size=self.font_sizes['normal'])
                self.set_text_color(*self.colors['black'])
                
                self.cell(60, 5, "Payment Method:", 0, 0, 'R')
                self.cell(25, 5, str(sale_data['payment_method']), 0, 1, 'R')
                
                if 'amount_paid' in sale_data:
                    amount_paid = float(sale_data['amount_paid'])
                    self.cell(60, 5, "Amount Paid:", 0, 0, 'R')
                    self.cell(25, 5, f"${amount_paid:.2f}", 0, 1, 'R')
                    
                    if amount_paid > total:
                        change = amount_paid - total
                        self.cell(60, 5, "Change:", 0, 0, 'R')
                        self.cell(25, 5, f"${change:.2f}", 0, 1, 'R')
            
            # Stylish separator
            self.ln(2)
            self._draw_section_separator()
            self.ln(2)
            
            # Footer with modern design
            self.safe_set_font(size=self.font_sizes['small'])
            self.set_text_color(*self.colors['black'])
            
            # Return policy
            self.cell(0, 4, "Return Policy", ln=True, align='C')
            self.safe_set_font(size=self.font_sizes['tiny'])
            self.cell(0, 4, RETURN_POLICY, ln=True, align='C')
            
            # Contact info
            self.ln(1)
            self.cell(0, 4, COMPANY_CONTACT['website'], ln=True, align='C')
            self.cell(0, 4, COMPANY_CONTACT['email'], ln=True, align='C')
            
            # Thank you message
            self.ln(1)
            self.safe_set_font(style='B', size=self.font_sizes['small'])
            self.set_text_color(*self.colors['accent'])
            self.cell(0, 4, RECEIPT_FOOTER, ln=True, align='C')
            
            # Receipt ID and timestamp in subtle styling
            self.ln(2)
            self.safe_set_font(size=self.font_sizes['tiny'])
            self.set_text_color(*self.colors['gray'])
            self.cell(0, 3, f"Receipt ID: {sale_data['receipt_number']}", ln=True, align='C')
            self.cell(0, 3, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
            
            # Replace the old barcode section with the new stylish one
            self.ln(2)
            self._draw_section_separator()
            self.ln(2)
            
            # Add stylish barcode section
            self._draw_stylish_barcode_section(str(sale_data['receipt_number']))
            
            # Bottom design element
            self.ln(2)
            y = self.get_y() + 2
            for i in range(10):
                self.set_draw_color(*self.colors['accent'])
                self.set_line_width(0.3)
                self.line(5 + i*8, y, 10 + i*8, y)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating receipt: {e}")
            raise Exception(f"Failed to create receipt: {str(e)}")

    def circle(self, x, y, r, style=''):
        """Draw a circle"""
        self.ellipse(x-r, y-r, 2*r, 2*r, style=style)

    def save_receipt(self, filename):
        """Save the receipt with enhanced reliability"""
        try:
            # Clean filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
            if not safe_filename:
                safe_filename = f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
            elif not safe_filename.endswith('.pdf'):
                safe_filename += '.pdf'
            
            filepath = os.path.join(RECEIPTS_DIR, safe_filename)
            
            # Save with retries
            max_retries = 3
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    # Set PDF metadata with ASCII-only text
                    self.set_title('Sales Receipt')
                    self.set_author('Mart Manager')
                    self.set_creator('Mart Manager')
                    self.set_subject('Sales Receipt')
                    self.set_keywords('receipt,sale,mart')
                    
                    # Save the file with proper encoding
                    self.output(filepath, 'F')
                    
                    # Verify file
                    if not os.path.exists(filepath):
                        raise Exception("File was not created")
                    
                    if os.path.getsize(filepath) < 100:
                        raise Exception("Generated file is too small")
                    
                    # Verify PDF header
                    with open(filepath, 'rb') as f:
                        if not f.read(4).startswith(b'%PDF'):
                            raise Exception("Generated file is not a valid PDF")
                    
                    logger.info(f"Receipt saved successfully: {filepath}")
                    return filepath
                    
                except Exception as e:
                    last_error = str(e)
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                        time.sleep(1)
                        
                        # Clean up failed attempt
                        try:
                            if os.path.exists(filepath):
                                os.remove(filepath)
                        except:
                            pass
                    continue
            
            raise Exception(f"Failed to save receipt after {max_retries} attempts. Last error: {last_error}")
            
        except Exception as e:
            logger.error(f"Failed to save receipt: {e}")
            raise Exception(f"Failed to save receipt: {str(e)}")

def generate_receipt(sale_data):
    """Generate a receipt with proper Unicode support"""
    try:
        # Create PDF with Unicode support
        pdf = ReceiptPDF()
        
        # Create receipt content
        if not pdf.create_receipt(sale_data):
            raise Exception("Failed to create receipt content")
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"receipt_{sale_data['receipt_number']}_{timestamp}.pdf"
        
        # Save receipt
        return pdf.save_receipt(filename)
                    
    except Exception as e:
        logger.error(f"Failed to generate receipt: {str(e)}")
        raise 