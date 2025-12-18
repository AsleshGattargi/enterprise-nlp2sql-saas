-- FinanceHub PostgreSQL Database Initialization

-- Accounts table
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-003',
    account_number VARCHAR(20) UNIQUE NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Checking', 'Savings', 'Credit', 'Loan', 'Investment')),
    customer_name VARCHAR(100) NOT NULL,
    balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(10) DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Closed')),
    opened_date DATE NOT NULL,
    interest_rate DECIMAL(5,4) DEFAULT 0.0000,
    credit_limit DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-003',
    account_id INT NOT NULL REFERENCES accounts(account_id),
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Payment', 'Interest', 'Fee')),
    amount DECIMAL(15,2) NOT NULL,
    description TEXT,
    transaction_date DATE NOT NULL,
    transaction_time TIME DEFAULT CURRENT_TIME,
    balance_after DECIMAL(15,2) NOT NULL,
    reference_number VARCHAR(50) UNIQUE,
    merchant_name VARCHAR(100),
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loans table
CREATE TABLE loans (
    loan_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-003',
    account_id INT NOT NULL REFERENCES accounts(account_id),
    loan_type VARCHAR(30) NOT NULL CHECK (loan_type IN ('Personal', 'Mortgage', 'Auto', 'Business', 'Student')),
    principal_amount DECIMAL(15,2) NOT NULL,
    interest_rate DECIMAL(5,4) NOT NULL,
    term_months INT NOT NULL,
    monthly_payment DECIMAL(10,2) NOT NULL,
    outstanding_balance DECIMAL(15,2) NOT NULL,
    loan_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    status VARCHAR(15) DEFAULT 'Active' CHECK (status IN ('Active', 'Paid Off', 'Default')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Investments table
CREATE TABLE investments (
    investment_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-003',
    account_id INT NOT NULL REFERENCES accounts(account_id),
    investment_type VARCHAR(30) NOT NULL CHECK (investment_type IN ('Stocks', 'Bonds', 'Mutual Funds', 'ETF', 'CD')),
    symbol VARCHAR(10),
    shares_quantity DECIMAL(15,6),
    purchase_price DECIMAL(10,4),
    current_price DECIMAL(10,4),
    market_value DECIMAL(15,2),
    purchase_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Credit cards table
CREATE TABLE credit_cards (
    card_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-003',
    account_id INT NOT NULL REFERENCES accounts(account_id),
    card_number VARCHAR(20) NOT NULL,
    card_type VARCHAR(20) DEFAULT 'Credit',
    credit_limit DECIMAL(10,2) NOT NULL,
    current_balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    available_credit DECIMAL(10,2) GENERATED ALWAYS AS (credit_limit - current_balance) STORED,
    apr DECIMAL(5,4) NOT NULL,
    issue_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    status VARCHAR(10) DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Blocked')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO accounts (account_number, account_type, customer_name, balance, opened_date, interest_rate, credit_limit) VALUES
('ACC001001', 'Checking', 'Robert Johnson', 15750.50, '2020-03-15', 0.0050, NULL),
('ACC001002', 'Savings', 'Maria Garcia', 45320.75, '2019-08-22', 0.0250, NULL),
('ACC001003', 'Credit', 'David Wilson', -2150.25, '2021-01-10', 0.1899, 10000.00),
('ACC001004', 'Investment', 'Sarah Brown', 125800.00, '2018-11-05', 0.0000, NULL),
('ACC001005', 'Checking', 'Michael Davis', 8950.80, '2022-05-18', 0.0075, NULL),
('ACC001006', 'Loan', 'Jennifer Miller', -185000.00, '2020-09-12', 0.0425, NULL),
('ACC001007', 'Savings', 'Christopher Taylor', 67500.25, '2019-03-30', 0.0275, NULL);

INSERT INTO transactions (account_id, transaction_type, amount, description, transaction_date, balance_after, reference_number, merchant_name, category) VALUES
(1, 'Deposit', 5000.00, 'Salary deposit', '2024-01-15', 20750.50, 'TXN001', 'Employer Corp', 'Salary'),
(1, 'Withdrawal', -250.00, 'ATM withdrawal', '2024-01-16', 20500.50, 'TXN002', 'Bank ATM', 'Cash'),
(2, 'Interest', 45.32, 'Monthly interest payment', '2024-01-15', 45366.07, 'TXN003', 'Bank Interest', 'Interest'),
(3, 'Payment', -500.00, 'Credit card payment', '2024-01-17', -1650.25, 'TXN004', 'Online Payment', 'Payment'),
(4, 'Deposit', 2500.00, 'Investment contribution', '2024-01-18', 128300.00, 'TXN005', 'Investment Transfer', 'Investment'),
(5, 'Withdrawal', -1200.00, 'Rent payment', '2024-01-19', 7750.80, 'TXN006', 'Property Manager', 'Rent');

INSERT INTO loans (account_id, loan_type, principal_amount, interest_rate, term_months, monthly_payment, outstanding_balance, loan_date, maturity_date) VALUES
(6, 'Mortgage', 200000.00, 0.0425, 360, 985.20, 185000.00, '2020-09-12', '2050-09-12'),
(1, 'Auto', 25000.00, 0.0575, 60, 478.50, 18500.00, '2022-03-15', '2027-03-15'),
(5, 'Personal', 10000.00, 0.0899, 36, 318.00, 6200.00, '2023-06-01', '2026-06-01');

INSERT INTO investments (account_id, investment_type, symbol, shares_quantity, purchase_price, current_price, market_value, purchase_date) VALUES
(4, 'Stocks', 'AAPL', 100.000000, 150.25, 185.50, 18550.00, '2023-01-15'),
(4, 'Stocks', 'GOOGL', 25.000000, 2150.00, 2280.75, 57018.75, '2023-02-20'),
(4, 'ETF', 'VOO', 150.000000, 385.20, 425.80, 63870.00, '2023-03-10'),
(4, 'Bonds', 'GOVT', 200.000000, 25.50, 24.95, 4990.00, '2023-04-05');

INSERT INTO credit_cards (account_id, card_number, credit_limit, current_balance, apr, issue_date, expiry_date) VALUES
(3, '**** **** **** 1234', 10000.00, 2150.25, 0.1899, '2021-01-10', '2026-01-31'),
(1, '**** **** **** 5678', 15000.00, 850.75, 0.1649, '2022-06-15', '2027-06-30'),
(5, '**** **** **** 9012', 5000.00, 320.50, 0.2199, '2023-01-20', '2028-01-31');