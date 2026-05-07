-- Stores core authentication data and salts for AES-256 key derivation.
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,           -- UUID generated in Python
    username TEXT UNIQUE NOT NULL,
    enc_email BLOB,
    enc_phone BLOB,
    password_hash BLOB NOT NULL,        -- Argon2id output
    encryption_salt BLOB NOT NULL,      -- Salt for derive_aes_key()
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL  -- e.g., 'Hardware', 'Gaming', 'Rent'
);

CREATE TABLE vendors (
    vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT UNIQUE NOT NULL
);

-- Base Account Table
-- Implements abstract 'Account' class
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,        -- UUID
    user_id TEXT NOT NULL,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK(
        account_type IN ('CHECKING', 'SAVINGS', 'CREDIT', 'DEBIT')
    ),
    enc_acc_num BLOB NOT NULL,          -- Encrypted account number
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Specific data for each actual Account type
CREATE TABLE checking_details (
    account_id TEXT PRIMARY KEY,
    routing_number TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE
);

CREATE TABLE savings_details (
    account_id TEXT PRIMARY KEY,
    interest_rate REAL NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE
);

CREATE TABLE credit_card_details (
    account_id TEXT PRIMARY KEY,
    enc_cvv BLOB NOT NULL,              -- Encrypted
    credit_limit REAL NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE
);

CREATE TABLE debit_card_details (
    account_id TEXT PRIMARY KEY,
    enc_cvv BLOB NOT NULL,              -- Encrypted
    linked_checking_id TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE,
    FOREIGN KEY (linked_checking_id) REFERENCES checking_details (account_id)
);

-- Transactions
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,    -- UUID
    account_id TEXT NOT NULL,
    vendor_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL,               -- Positive absolute value
    transaction_date DATETIME NOT NULL,

    -- Hardcoded Types (Sadge, no ENUM in SQLite)
    transaction_type TEXT NOT NULL CHECK(
        transaction_type IN ('INCOME', 'EXPENSE', 'TRANSFER_IN', 'TRANSFER_OUT')
    ),

    FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_id) REFERENCES vendors (vendor_id),
    FOREIGN KEY (category_id) REFERENCES categories (category_id)
);

-- Initial Hardcoded Categories
INSERT INTO categories (category_name) VALUES
('Credit Card Interest'),
('Savings Interest'),
('Electronic Deposit'),
('Cash Deposit'),
('Check Deposit'),
('Internal Transfer'),
('Refund'),
('Shopping'),
('Entertainment'),
('Bills & Utilities'),
('Food & Dining'),
('Travel'),
('Cash Withdrawals'),
('Check Deposits');