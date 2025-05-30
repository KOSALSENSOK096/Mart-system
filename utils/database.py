import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
import bcrypt
from typing import Dict, List, Any, Optional
import logging
import time
from contextlib import contextmanager
from configparser import ConfigParser
import os
import threading

try:
    from config import DB_CONFIG
except ImportError:
    from config_example import DB_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    _instance = None
    _lock = threading.Lock()
    _pool = None
    _max_retries = 5
    _retry_delay = 1  # seconds
    _connection_timeout = 60  # seconds

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Database, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the database connection pool"""
        try:
            config = self._read_config()
            if not config:
                raise Exception("Failed to read database configuration")

            pool_config = {
                "pool_name": "mypool",
                "pool_size": 5,
                "pool_reset_session": True,
                **config
            }

            self._pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
            logger.info("Database connection pool initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _read_config(self) -> Dict[str, str]:
        """Read database configuration from config.ini"""
        config = ConfigParser()
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
            config.read(config_path)
            return {
                'host': config.get('mysql', 'host', fallback='localhost'),
                'user': config.get('mysql', 'user', fallback='root'),
                'password': config.get('mysql', 'password', fallback=''),
                'database': config.get('mysql', 'database', fallback='mart_db'),
                'charset': config.get('mysql', 'charset', fallback='utf8mb4'),
                'collation': config.get('mysql', 'collation', fallback='utf8mb4_unicode_ci'),
                'use_unicode': True
            }
        except Exception as e:
            logger.error(f"Failed to read config: {e}")
            return {}

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool with automatic cleanup"""
        conn = None
        try:
            conn = self._pool.get_connection()
            cursor = conn.cursor()
            
            # Set connection character set
            cursor.execute("SET NAMES utf8mb4")
            cursor.execute("SET CHARACTER SET utf8mb4")
            cursor.execute("SET character_set_connection=utf8mb4")
            
            cursor.close()
            logger.info("Database connection established successfully")
            yield conn
        except Error as err:
            logger.error(f"Database connection error: {err}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                    logger.info("Database connection returned to pool")
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")

    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict[str, Any]]]:
        """Execute a query and return results as a list of dictionaries"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, params)
                
                if query.strip().upper().startswith(('SELECT', 'SHOW')):
                    result = cursor.fetchall()
                else:
                    connection.commit()
                    result = None
                    
                cursor.close()
                return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            self.execute_query("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def ensure_admin_exists(self) -> bool:
        """Ensure admin user exists in database"""
        try:
            result = self.execute_query("SELECT id FROM users WHERE username = 'admin'")
            if not result:
                from setup import create_admin_user
                return create_admin_user()
            logger.info("Admin user already exists")
            return True
        except Exception as e:
            logger.error(f"Failed to check/create admin user: {e}")
            return False

    def create_user(self, username: str, password: str, role: str = 'staff') -> bool:
        """Create a new user"""
        try:
            # Check if username exists
            result = self.execute_query("SELECT id FROM users WHERE username = %s", (username,))
            if result:
                return False

            # Hash password
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create user
            self.execute_query(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed.decode('utf-8'), role)
            )
            
            return True

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False

    def disconnect(self):
        """Clean up database resources"""
        try:
            if hasattr(self, '_pool'):
                self._pool = None
                logger.info("Database resources cleaned up")
        except Exception as e:
            logger.warning(f"Error during database cleanup: {e}")

    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """Verify user credentials with retry logic"""
        try:
            query = "SELECT * FROM users WHERE username = %s AND is_active = TRUE"
            result = self.execute_query(query, (username,))
            
            if result and bcrypt.checkpw(password.encode('utf-8'), result[0]['password'].encode('utf-8')):
                # Update last login time
                update_query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s"
                self.execute_query(update_query, (result[0]['id'],))
                return result[0]
            return None
        except Error as e:
            logger.error(f"Error verifying user: {e}")
            return None

    def get_products(self, search: str = None) -> List[Dict]:
        """Get all products with optional search filter"""
        try:
            query = """
                SELECT p.*, c.name as category_name 
                FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = TRUE
            """
            params = []
            
            if search:
                query += " AND (p.name LIKE %s OR c.name LIKE %s)"
                params.extend([f"%{search}%", f"%{search}%"])
            
            query += " ORDER BY p.name"
            
            result = self.execute_query(query, tuple(params) if params else None)
            return result if result else []
            
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            return []

    def add_product(self, data: Dict[str, Any]) -> bool:
        """Add a new product with optional barcode"""
        query = """
            INSERT INTO products (
                name, description, price, stock, 
                category_id, min_stock, barcode
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            self.execute_query(query, (
                data['name'],
                data.get('description'),
                data['price'],
                data['stock'],
                data['category_id'],
                data.get('min_stock', 10),
                data.get('barcode')  # Added barcode field
            ))
            return True
        except Error:
            return False

    def update_product(self, product_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing product"""
        query = """
            UPDATE products 
            SET name = %s, description = %s, price = %s, stock = %s, 
                category_id = %s, min_stock = %s
            WHERE id = %s
        """
        try:
            self.execute_query(query, (
                data['name'],
                data.get('description'),
                data['price'],
                data['stock'],
                data['category_id'],
                data.get('min_stock', 10),
                product_id
            ))
            return True
        except Error:
            return False

    def delete_product(self, product_id: int) -> bool:
        """Delete a product"""
        query = "DELETE FROM products WHERE id = %s"
        try:
            self.execute_query(query, (product_id,))
            return True
        except Error:
            return False

    def get_categories(self) -> List[Dict]:
        """Get all categories"""
        return self.execute_query("SELECT * FROM categories")

    def add_sale(self, user_id: int, items: List[Dict], total: float, 
                customer_id: Optional[int] = None) -> Optional[int]:
        """Add a new sale with its details"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                # Insert sale
                sale_query = """
                    INSERT INTO sales (user_id, customer_id, total_amount, payment_method)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sale_query, (user_id, customer_id, total, 'cash'))
                sale_id = cursor.lastrowid
                
                # Insert sale details and update stock
                for item in items:
                    detail_query = """
                        INSERT INTO sales_details (sale_id, product_id, quantity, price)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(detail_query, (
                        sale_id, item['product_id'], item['quantity'], item['price']
                    ))
                    
                    # Update stock
                    stock_query = """
                        UPDATE products 
                        SET stock = stock - %s
                        WHERE id = %s
                    """
                    cursor.execute(stock_query, (item['quantity'], item['product_id']))
                
                connection.commit()
                cursor.close()
                return sale_id
                
        except Error as e:
            logger.error(f"Error adding sale: {e}")
            if 'connection' in locals():
                connection.rollback()
            return None

    def get_low_stock_products(self) -> List[Dict]:
        """Get products with stock below minimum level"""
        query = """
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.stock <= p.min_stock
        """
        return self.execute_query(query)

    def get_daily_sales_summary(self) -> Dict[str, Any]:
        """Get sales summary for the current day"""
        query = """
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as average_sale
            FROM sales 
            WHERE DATE(created_at) = CURDATE()
        """
        result = self.execute_query(query)
        return result[0] if result else None

    def get_product_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Get product details by barcode with enhanced error handling"""
        try:
            # Clean barcode input
            barcode = barcode.strip()
            if not barcode:
                return None
            
            # Query with category information
            query = """
                SELECT p.*, c.name as category_name 
                FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.barcode = %s AND p.is_active = TRUE
            """
            
            # Execute with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = self.execute_query(query, (barcode,))
                    if result:
                        # Convert decimal values to float
                        product = result[0]
                        if 'price' in product:
                            product['price'] = float(product['price'])
                        return product
                    return None
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error getting product by barcode: {e}")
            return None
    
    def update_product_barcode(self, product_id: int, barcode: str) -> bool:
        """Update product's barcode with validation"""
        try:
            # Clean barcode input
            barcode = barcode.strip()
            
            # Check if barcode already exists
            if barcode:
                existing = self.execute_query(
                    "SELECT id FROM products WHERE barcode = %s AND id != %s",
                    (barcode, product_id)
                )
                if existing:
                    logger.error(f"Barcode {barcode} already exists")
                    return False
            
            # Update barcode
            query = """
                UPDATE products 
                SET barcode = %s, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND is_active = TRUE
            """
            
            self.execute_query(query, (barcode, product_id))
            return True
            
        except Exception as e:
            logger.error(f"Error updating product barcode: {e}")
            return False
    
    def get_products_without_barcode(self) -> List[Dict[str, Any]]:
        """Get products without barcodes"""
        try:
            query = """
                SELECT p.*, c.name as category_name 
                FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE (p.barcode IS NULL OR p.barcode = '')
                AND p.is_active = TRUE
                ORDER BY p.name
            """
            
            result = self.execute_query(query)
            
            # Convert decimal values to float
            if result:
                for product in result:
                    if 'price' in product:
                        product['price'] = float(product['price'])
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting products without barcode: {e}")
            return []
    
    def validate_barcode(self, barcode: str) -> bool:
        """Validate barcode format and uniqueness"""
        try:
            # Clean barcode input
            barcode = barcode.strip()
            if not barcode:
                return False
            
            # Check barcode format (can be customized based on requirements)
            if not barcode.isalnum():
                return False
            
            # Check if barcode already exists
            query = "SELECT id FROM products WHERE barcode = %s AND is_active = TRUE"
            result = self.execute_query(query, (barcode,))
            
            return not bool(result)  # Return True if barcode doesn't exist
            
        except Exception as e:
            logger.error(f"Error validating barcode: {e}")
            return False

    def execute_query_with_retries(self, query: str, params: tuple = None) -> Optional[List[Dict[str, Any]]]:
        """Execute a query with enhanced error handling and retries"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(query, params)
                    
                    if query.strip().upper().startswith('SELECT'):
                        result = cursor.fetchall()
                        return result if result else []
                    else:
                        conn.commit()
                        return True
                    
            except Error as err:
                retry_count += 1
                logger.error(f"Database query failed (attempt {retry_count}): {err}")
                
                if retry_count == max_retries:
                    logger.error(f"Query failed after {max_retries} attempts")
                    raise
                
                time.sleep(1)  # Wait before retrying

    def verify_user_with_retries(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify user credentials with enhanced security"""
        try:
            query = """
                SELECT id, username, role 
                FROM users 
                WHERE username = %s AND password = %s AND is_active = TRUE
            """
            result = self.execute_query_with_retries(query, (username, password))
            
            if result and len(result) > 0:
                return result[0]
            return None
            
        except Exception as e:
            logger.error(f"User verification failed: {e}")
            return None

    def create_user_with_validation(self, username: str, password: str, role: str) -> bool:
        """Create a new user with validation"""
        try:
            # Validate role
            if role not in ['admin', 'staff']:
                logger.error(f"Invalid role: {role}")
                return False
            
            # Check for existing user
            check_query = "SELECT id FROM users WHERE username = %s"
            if self.execute_query_with_retries(check_query, (username,)):
                logger.error(f"Username already exists: {username}")
                return False
            
            # Create user
            query = """
                INSERT INTO users (username, password, role, is_active) 
                VALUES (%s, %s, %s, TRUE)
            """
            return bool(self.execute_query_with_retries(query, (username, password, role)))
            
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            return False

    def get_products_with_optional_search(self, search_term=None):
        """Get products with optional search term and enhanced error handling"""
        try:
            # Base query with category join
            query = """
                SELECT p.*, c.name as category_name 
                FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id 
                WHERE 1=1
            """
            params = []
            
            # Add search condition if term provided
            if search_term:
                # Clean and validate search term
                search_term = search_term.strip()
                if search_term:
                    query += """ 
                        AND (
                            p.name LIKE %s 
                            OR p.description LIKE %s
                            OR c.name LIKE %s
                            OR CAST(p.price AS CHAR) LIKE %s
                        )
                    """
                    search_pattern = f"%{search_term}%"
                    params.extend([search_pattern] * 4)
            
            # Add sorting and active products only
            query += " AND p.is_active = 1 ORDER BY p.name ASC"
            
            # Execute query with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    results = self.execute_query(query, params)
                    
                    # Convert decimal values to float for JSON serialization
                    if results:
                        for product in results:
                            if 'price' in product:
                                product['price'] = float(product['price'])
                    
                    return results if results else []
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(0.5)  # Wait before retry
            
        except Exception as e:
            logger.error(f"Error in get_products_with_optional_search: {e}")
            return []  # Return empty list on error
            
        return []  # Ensure we always return a list

    def add_product_with_validation(self, data: Dict[str, Any]) -> bool:
        """Add a new product with validation"""
        try:
            # Validate required fields
            required_fields = ['name', 'price', 'stock']
            if not all(field in data for field in required_fields):
                logger.error("Missing required product fields")
                return False
            
            # Create query dynamically based on provided fields
            fields = []
            values = []
            placeholders = []
            
            for key, value in data.items():
                if value is not None:
                    fields.append(key)
                    values.append(value)
                    placeholders.append('%s')
            
            query = f"""
                INSERT INTO products ({', '.join(fields)}, is_active) 
                VALUES ({', '.join(placeholders)}, TRUE)
            """
            
            return bool(self.execute_query_with_retries(query, tuple(values)))
            
        except Exception as e:
            logger.error(f"Failed to add product: {e}")
            return False

    def update_product_with_validation(self, product_id: int, data: Dict[str, Any]) -> bool:
        """Update product with validation"""
        try:
            # Validate product exists
            if not self.execute_query_with_retries(
                "SELECT id FROM products WHERE id = %s AND is_active = TRUE",
                (product_id,)
            ):
                logger.error(f"Product not found: {product_id}")
                return False
            
            # Create update query dynamically
            updates = []
            values = []
            
            for key, value in data.items():
                if value is not None:
                    updates.append(f"{key} = %s")
                    values.append(value)
            
            values.append(product_id)
            
            query = f"""
                UPDATE products 
                SET {', '.join(updates)} 
                WHERE id = %s
            """
            
            return bool(self.execute_query_with_retries(query, tuple(values)))
            
        except Exception as e:
            logger.error(f"Failed to update product: {e}")
            return False

    def delete_product_soft(self, product_id: int) -> bool:
        """Soft delete a product"""
        try:
            query = "UPDATE products SET is_active = FALSE WHERE id = %s"
            return bool(self.execute_query_with_retries(query, (product_id,)))
        except Exception as e:
            logger.error(f"Failed to delete product: {e}")
            return False

    def get_categories_active(self) -> List[Dict[str, Any]]:
        """Get all active categories"""
        try:
            query = "SELECT * FROM categories WHERE is_active = TRUE ORDER BY name"
            return self.execute_query_with_retries(query)
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return []

    def create_tables(self):
        try:
            # Create users table
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create login_history table
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS login_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    ip_address VARCHAR(45),
                    device_info VARCHAR(255),
                    status BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

        except Error as e:
            logger.error(f"Error creating tables: {e}")
            raise 

    def get_daily_sales(self) -> Dict[str, Any]:
        """Get daily sales statistics"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_sales,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COUNT(DISTINCT product_id) as unique_items,
                    COALESCE(SUM(quantity), 0) as total_items
                FROM sales s
                LEFT JOIN sales_details sd ON s.id = sd.sale_id
                WHERE DATE(s.created_at) = CURDATE()
            """
            result = self.execute_query(query)
            if result and result[0]:
                stats = result[0]
                # Convert decimal values to float
                if stats['total_revenue']:
                    stats['total_revenue'] = float(stats['total_revenue'])
                return stats
            return {
                'total_sales': 0,
                'total_revenue': 0.0,
                'unique_items': 0,
                'total_items': 0
            }
        except Exception as e:
            logger.error(f"Failed to get daily sales: {e}")
            return {
                'total_sales': 0,
                'total_revenue': 0.0,
                'unique_items': 0,
                'total_items': 0
            } 