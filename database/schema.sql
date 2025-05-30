-- Drop database if exists and create new one
DROP DATABASE IF EXISTS mart_db;
CREATE DATABASE mart_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mart_db;

-- Enable strict mode and other important settings
SET SQL_MODE = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
SET GLOBAL max_connections = 300;
SET GLOBAL connect_timeout = 60;
SET GLOBAL wait_timeout = 600;
SET GLOBAL interactive_timeout = 600;

-- Users table with enhanced security
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'staff') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    CHECK (LENGTH(username) >= 3)
) ENGINE=InnoDB;

-- Login history with enhanced tracking
CREATE TABLE login_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    ip_address VARCHAR(45),
    device_info JSON,
    browser_info VARCHAR(255),
    location VARCHAR(255),
    os_info VARCHAR(100),
    login_type ENUM('password', 'token', 'oauth') DEFAULT 'password',
    session_id VARCHAR(100),
    status BOOLEAN DEFAULT TRUE,
    status_message VARCHAR(255),
    attempt_count INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status),
    INDEX idx_ip_address (ip_address),
    INDEX idx_session (session_id)
) ENGINE=InnoDB;

-- Categories table with better constraints
CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    CHECK (LENGTH(name) >= 2)
) ENGINE=InnoDB;

-- Products table with enhanced tracking
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    barcode VARCHAR(50) UNIQUE,
    category_id INT,
    min_stock INT DEFAULT 10,
    max_stock INT DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_barcode (barcode),
    INDEX idx_category (category_id),
    CHECK (price >= 0),
    CHECK (stock >= 0),
    CHECK (min_stock >= 0),
    CHECK (max_stock >= min_stock)
) ENGINE=InnoDB;

-- Customers table with validation
CREATE TABLE customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_phone (phone),
    INDEX idx_email (email),
    CHECK (LENGTH(name) >= 2)
) ENGINE=InnoDB;

-- Sales table with better tracking
CREATE TABLE sales (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('cash', 'card') NOT NULL,
    payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'completed',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_customer (customer_id),
    INDEX idx_user (user_id),
    CHECK (total_amount >= 0)
) ENGINE=InnoDB;

-- Sales details table with validation
CREATE TABLE sales_details (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_sale (sale_id),
    INDEX idx_product (product_id),
    CHECK (quantity > 0),
    CHECK (price >= 0)
) ENGINE=InnoDB;

-- Insert default admin user with better password handling
INSERT INTO users (username, password, role) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY.5AYPs7U5Hle.', 'admin');

-- Insert essential categories
INSERT INTO categories (name, description) VALUES 
('Beverages', 'Drinks and liquid refreshments'),
('Snacks', 'Quick bites and packaged treats'),
('Groceries', 'Essential food and household items'),
('Electronics', 'Electronic devices and accessories'),
('Household', 'Home care and maintenance products');

-- Insert sample products with barcodes
INSERT INTO products (name, description, price, stock, barcode, category_id, min_stock, max_stock) VALUES 
('Coca Cola 330ml', 'Refreshing carbonated drink', 1.50, 100, '5449000000996', 1, 20, 200),
('Pepsi 330ml', 'Classic cola beverage', 1.50, 100, '5449000000989', 1, 20, 200),
('Lays Classic', 'Original potato chips', 2.99, 50, '5449000000972', 2, 15, 100),
('Doritos Nacho Cheese', 'Cheese flavored chips', 2.99, 50, '5449000000965', 2, 15, 100),
('Rice 1kg', 'Premium long grain rice', 5.99, 30, '5449000000958', 3, 10, 50),
('USB Cable', 'Type-C charging cable', 9.99, 20, '5449000000941', 4, 5, 30),
('Dish Soap', 'Liquid dish washing soap', 3.99, 40, '5449000000934', 5, 10, 60);

-- Create trigger for stock management
DELIMITER //
CREATE TRIGGER after_sale_detail_insert 
AFTER INSERT ON sales_details
FOR EACH ROW
BEGIN
    UPDATE products 
    SET stock = stock - NEW.quantity
    WHERE id = NEW.product_id;
END//

CREATE TRIGGER check_stock_before_sale
BEFORE INSERT ON sales_details
FOR EACH ROW
BEGIN
    DECLARE current_stock INT;
    SELECT stock INTO current_stock FROM products WHERE id = NEW.product_id;
    IF current_stock < NEW.quantity THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock';
    END IF;
END//
DELIMITER ;

-- Create views for common queries
CREATE VIEW low_stock_products AS
SELECT p.*, c.name as category_name
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.stock <= p.min_stock AND p.is_active = TRUE;

CREATE VIEW daily_sales_summary AS
SELECT 
    DATE(created_at) as sale_date,
    COUNT(*) as total_sales,
    SUM(total_amount) as total_revenue,
    payment_method
FROM sales
GROUP BY DATE(created_at), payment_method;

-- Create additional indexes for performance
CREATE INDEX idx_product_name ON products(name);
CREATE INDEX idx_product_price ON products(price);
CREATE INDEX idx_product_stock ON products(stock);
CREATE INDEX idx_sale_date ON sales(created_at);
CREATE INDEX idx_sale_amount ON sales(total_amount);

-- Create additional views for reporting
CREATE VIEW product_sales_summary AS
SELECT 
    p.id,
    p.name,
    p.barcode,
    c.name as category,
    COUNT(sd.id) as times_sold,
    SUM(sd.quantity) as total_quantity_sold,
    SUM(sd.quantity * sd.price) as total_revenue
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN sales_details sd ON p.id = sd.product_id
GROUP BY p.id, p.name, p.barcode, c.name;

CREATE VIEW category_sales_summary AS
SELECT 
    c.name as category,
    COUNT(DISTINCT p.id) as total_products,
    SUM(p.stock) as total_stock,
    COUNT(sd.id) as total_sales
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
LEFT JOIN sales_details sd ON p.id = sd.product_id
GROUP BY c.name;

-- Create stored procedure for restocking products
DELIMITER //
CREATE PROCEDURE restock_products()
BEGIN
    SELECT 
        id,
        name,
        stock,
        min_stock,
        (min_stock - stock) as quantity_needed
    FROM products
    WHERE stock <= min_stock AND is_active = TRUE
    ORDER BY (min_stock - stock) DESC;
END//

-- Create stored procedure for daily sales report
CREATE PROCEDURE daily_sales_report(IN report_date DATE)
BEGIN
    SELECT 
        p.name as product_name,
        c.name as category_name,
        SUM(sd.quantity) as quantity_sold,
        SUM(sd.quantity * sd.price) as total_revenue
    FROM sales s
    JOIN sales_details sd ON s.id = sd.sale_id
    JOIN products p ON sd.product_id = p.id
    JOIN categories c ON p.category_id = c.id
    WHERE DATE(s.created_at) = report_date
    GROUP BY p.name, c.name
    ORDER BY total_revenue DESC;
END//

DELIMITER ;

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON mart_db.* TO 'mart_user'@'localhost' IDENTIFIED BY 'mart_password';
FLUSH PRIVILEGES;

-- Verify database setup
SELECT 'Database setup completed successfully' as status;
SELECT COUNT(*) as total_products FROM products;
SELECT COUNT(*) as total_categories FROM categories;
SELECT COUNT(*) as total_users FROM users;

-- Test connection and data
SELECT * FROM products LIMIT 5;
SELECT * FROM low_stock_products;
CALL restock_products(); 