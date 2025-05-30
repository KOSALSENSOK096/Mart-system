# Mart Manager

A modern point of sale and inventory management system with beautiful receipt generation.

## Features

- 🛍️ Modern and intuitive user interface
- 📊 Real-time sales tracking and analytics
- 🧾 Beautiful receipt generation with modern design
- 📦 Inventory management
- 👥 User management with role-based access
- 📈 Sales reports and analytics
- 🔍 Barcode scanning support
- 💾 Automatic data backup
- 📱 Responsive design
- 🌙 Dark mode support

## Requirements

- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mart-manager.git
cd mart-manager
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the database:
- Copy `config_example.py` to `config.py`
- Update the database settings in `config.py`
- Create a MySQL database named 'mart_db'

5. Initialize the database:
```bash
python setup.py
```

## Usage

1. Start the application:
```bash
python main.py
```

2. Login with default admin credentials:
- Username: admin
- Password: admin123

3. Change the default password after first login.

## Receipt Features

The application generates beautiful, modern receipts with:

- 🎨 Clean, professional design
- 📝 Comprehensive transaction details
- 💫 Modern styling with icons
- 📊 Clear item breakdown
- 💰 Tax and discount calculations
- 💳 Multiple payment method support
- ✨ Automatic backup saves
- 🔍 QR code for digital copy
- 📱 Mobile-friendly format

## Directory Structure

```
mart-manager/
├── assets/           # Static assets
├── backups/         # Data backups
├── logs/            # Application logs
├── receipts/        # Generated receipts
├── temp/            # Temporary files
├── utils/           # Utility functions
├── views/           # UI views
├── config.py        # Configuration
├── main.py          # Main application
└── requirements.txt # Dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:
- Open an issue on GitHub
- Email: support@martmanager.com
- Visit: www.martmanager.com

## Acknowledgments

- CustomTkinter for the modern UI components
- FPDF for PDF generation
- All other open-source contributors # Mart-system
