import mysql.connector
import bcrypt
import logging
import os
from configparser import ConfigParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_config():
    """Read database configuration"""
    config = ConfigParser()
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        config.read(config_path)
        return {
            'host': config.get('mysql', 'host', fallback='localhost'),
            'user': config.get('mysql', 'user', fallback='root'),
            'password': config.get('mysql', 'password', fallback=''),
            'database': config.get('mysql', 'database', fallback='tea_house_db')
        }
    except Exception as e:
        logger.error(f"Failed to read config: {e}")
        return None

def create_database():
    """Create database if it doesn't exist"""
    config = read_config()
    if not config:
        return False

    try:
        # Connect without database selected
        conn = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password']
        )
        cursor = conn.cursor()

        # Create database with proper character encoding
        cursor.execute(f"""
            CREATE DATABASE IF NOT EXISTS {config['database']}
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
        """)
        logger.info(f"Database {config['database']} created successfully")

        # Switch to the database
        cursor.execute(f"USE {config['database']}")
        
        # Set connection character set
        cursor.execute("SET NAMES utf8mb4")
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")
        
        return True

    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def create_tables():
    """Create necessary tables"""
    config = read_config()
    if not config:
        return False

    try:
        conn = mysql.connector.connect(
            **config,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        cursor = conn.cursor()

        # Set connection character set
        cursor.execute("SET NAMES utf8mb4")
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin', 'staff') NOT NULL DEFAULT 'staff',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                status ENUM('active', 'inactive') DEFAULT 'active'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                category_id INT,
                stock INT DEFAULT 0,
                min_stock INT DEFAULT 10,
                barcode VARCHAR(100) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Sales table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                total_amount DECIMAL(10,2) NOT NULL,
                payment_method VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Sale items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sale_id INT,
                product_id INT,
                quantity INT NOT NULL,
                price_per_unit DECIMAL(10,2) NOT NULL,
                subtotal DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Login history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                device_info TEXT,
                browser_info VARCHAR(255),
                location VARCHAR(255),
                os_info VARCHAR(255),
                session_id VARCHAR(255),
                status BOOLEAN DEFAULT TRUE,
                status_message TEXT,
                login_type VARCHAR(50),
                FOREIGN KEY (user_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        conn.commit()
        logger.info("All tables created successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def create_admin_user():
    """Create default admin user if not exists"""
    config = read_config()
    if not config:
        return False

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)

        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            logger.info("Admin user already exists")
            return True

        # Create admin user
        password = "admin123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        """, ('admin', hashed.decode('utf-8'), 'admin'))
        
        conn.commit()
        logger.info("Admin user created successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        return False

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def create_default_data():
    """Create default categories and products"""
    config = read_config()
    if not config:
        return False

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)

        # Default categories
        categories = [
            ("Hot Tea", "Traditional hot tea varieties"),
            ("Cold Tea", "Refreshing cold tea drinks"),
            ("Snacks", "Light snacks and accompaniments"),
            ("Tea Sets", "Tea sets and accessories")
        ]

        for name, desc in categories:
            cursor.execute("""
                INSERT IGNORE INTO categories (name, description)
                VALUES (%s, %s)
            """, (name, desc))

        # Get category IDs
        cursor.execute("SELECT id, name FROM categories")
        category_map = {row['name']: row['id'] for row in cursor.fetchall()}

        # Default products
        products = [
            ("Green Tea", "Traditional Japanese green tea", 3.99, "Hot Tea", 100),
            ("Earl Grey", "Classic Earl Grey black tea", 4.99, "Hot Tea", 100),
            ("Iced Lemon Tea", "Refreshing iced tea with lemon", 5.99, "Cold Tea", 80),
            ("Bubble Tea", "Milk tea with tapioca pearls", 6.99, "Cold Tea", 50),
            ("Tea Cookies", "Butter cookies perfect with tea", 4.99, "Snacks", 150),
            ("Ceramic Tea Set", "Traditional ceramic tea set", 49.99, "Tea Sets", 20)
        ]

        for name, desc, price, category, stock in products:
            cursor.execute("""
                INSERT IGNORE INTO products 
                (name, description, price, category_id, stock)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, desc, price, category_map[category], stock))

        conn.commit()
        logger.info("Default categories and products created successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to create default data: {e}")
        return False

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def initialize_database():
    """Initialize the database with all required data"""
    if not create_database():
        return False
    
    if not create_tables():
        return False
    
    if not create_admin_user():
        return False
    
    if not create_default_data():
        return False
    
    return True

if __name__ == "__main__":
    initialize_database() 