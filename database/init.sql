CREATE DATABASE IF NOT EXISTS bankingdb;
USE bankingdb;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    account_type ENUM('savings', 'checking') DEFAULT 'savings',
    balance DECIMAL(15,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    type ENUM('deposit', 'withdrawal', 'transfer') NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    description VARCHAR(255),
    reference_account VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

-- Seed demo user (password: demo1234)
INSERT IGNORE INTO users (username, email, password_hash, full_name)
VALUES ('demo', 'demo@bank.com',
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36o6WOiHYEoUTpnE8nAOfuS',
        'Demo User');

INSERT IGNORE INTO accounts (user_id, account_number, account_type, balance)
SELECT id, 'ACC0000000001', 'savings', 5000.00 FROM users WHERE username='demo';
