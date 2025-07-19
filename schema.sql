
CREATE TABLE Customer (
    CustomerID SERIAL PRIMARY KEY,
    FirstName VARCHAR(255) NOT NULL,
    LastName VARCHAR(255) NOT NULL,
    Email VARCHAR(255) UNIQUE NOT NULL,
    Phone VARCHAR(255),
    Address TEXT,
    CCCD_Passport VARCHAR(255) UNIQUE NOT NULL, -- Encrypted in application
    DateOfBirth DATE NOT NULL,
    Status VARCHAR(255) NOT NULL CHECK (Status IN ('Active', 'Suspended', 'Inactive'))
);

-- BankAccount Table
CREATE TABLE BankAccount (
    AccountID SERIAL PRIMARY KEY,
    CustomerID INTEGER NOT NULL REFERENCES Customer(CustomerID),
    AccountType VARCHAR(255) NOT NULL CHECK (AccountType IN ('Checking', 'Savings', 'Credit')),
    AccountNumber VARCHAR(255) UNIQUE NOT NULL, -- Encrypted in application
    Balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    OpenDate DATE NOT NULL,
    Status VARCHAR(255) NOT NULL CHECK (Status IN ('Active', 'Frozen', 'Closed'))
);

-- Card Table
CREATE TABLE Card (
    CardID SERIAL PRIMARY KEY,
    AccountID INTEGER NOT NULL REFERENCES BankAccount(AccountID),
    CardNumber VARCHAR(255) UNIQUE NOT NULL, -- Encrypted in application
    CardType VARCHAR(255) NOT NULL CHECK (CardType IN ('Debit', 'Credit', 'Prepaid')),
    ExpiryDate DATE NOT NULL,
    CVV VARCHAR(255) NOT NULL, -- Encrypted in application
    Status VARCHAR(255) NOT NULL CHECK (Status IN ('Active', 'Blocked', 'Expired'))
);

-- Merchant Table
CREATE TABLE Merchant (
    MerchantID SERIAL PRIMARY KEY,
    MerchantName VARCHAR(255) NOT NULL,
    Category VARCHAR(255),
    Location TEXT,
    RiskScore INTEGER NOT NULL DEFAULT 0 CHECK (RiskScore >= 0 AND RiskScore <= 100)
);

-- Device Table
CREATE TABLE Device (
    DeviceID SERIAL PRIMARY KEY,
    CustomerID INTEGER NOT NULL REFERENCES Customer(CustomerID),
    DeviceType VARCHAR(255) NOT NULL CHECK (DeviceType IN ('Mobile', 'Desktop', 'Tablet')),
    DeviceFingerprint VARCHAR(255) UNIQUE NOT NULL,
    IPAddress VARCHAR(255),
    LastUsed TIMESTAMP,
    Status VARCHAR(255) NOT NULL CHECK (Status IN ('Trusted', 'Suspicious', 'Blocked')),
    RiskTag VARCHAR(255) NOT NULL CHECK (RiskTag IN ('Low', 'Medium', 'High'))
);

-- AuthenticationLog Table
CREATE TABLE AuthenticationLog (
    AuthLogID SERIAL PRIMARY KEY,
    CustomerID INTEGER NOT NULL REFERENCES Customer(CustomerID),
    TransactionID INTEGER REFERENCES PaymentTransaction(TransactionID),
    AuthType VARCHAR(255) NOT NULL CHECK (AuthType IN ('OTP', 'Biometric', 'Password')),
    AuthDate TIMESTAMP NOT NULL,
    Status VARCHAR(255) NOT NULL CHECK (Status IN ('Success', 'Failed', 'Pending')),
    OTPCode VARCHAR(255), -- Encrypted in application, Nullable
    BiometricData VARCHAR(255), -- Encrypted in application, Nullable
    DeviceID INTEGER REFERENCES Device(DeviceID),
    RiskTag VARCHAR(255) NOT NULL CHECK (RiskTag IN ('Low', 'Medium', 'High'))
);

-- PaymentTransaction Table
CREATE TABLE PaymentTransaction (
    TransactionID SERIAL PRIMARY KEY,
    AccountID INTEGER NOT NULL REFERENCES BankAccount(AccountID),
    CardID INTEGER REFERENCES Card(CardID),
    MerchantID INTEGER NOT NULL REFERENCES Merchant(MerchantID),
    Amount DECIMAL(15, 2) NOT NULL,
    TransactionDate TIMESTAMP NOT NULL,
    TransactionType VARCHAR(255) NOT NULL CHECK (TransactionType IN ('Online', 'POS', 'ATM', 'Transfer', 'Refund')),
    Status VARCHAR(255) NOT NULL CHECK (Status IN ('Completed', 'Pending', 'Declined')),
    DeviceID INTEGER REFERENCES Device(DeviceID),
    AuthLogID INTEGER REFERENCES AuthenticationLog(AuthLogID),
    RiskTag VARCHAR(255) NOT NULL CHECK (RiskTag IN ('Low', 'Medium', 'High'))
);

-- FraudAlert Table
CREATE TABLE FraudAlert (
    AlertID SERIAL PRIMARY KEY,
    TransactionID INTEGER REFERENCES PaymentTransaction(TransactionID),
    CustomerID INTEGER NOT NULL REFERENCES Customer(CustomerID),
    DeviceID INTEGER REFERENCES Device(DeviceID),
    AuthLogID INTEGER REFERENCES AuthenticationLog(AuthLogID),
    AlertType VARCHAR(255) NOT NULL,
    AlertDate TIMESTAMP NOT NULL,
    RiskScore INTEGER NOT NULL CHECK (RiskScore >= 0 AND RiskScore <= 100),
    Status VARCHAR(255) NOT NULL CHECK (Status IN ('Open', 'Resolved', 'False')),
    RiskTag VARCHAR(255) NOT NULL CHECK (RiskTag IN ('Low', 'Medium', 'High'))
);

-- Indexes for performance
CREATE INDEX idx_customer_email ON Customer(Email);
CREATE INDEX idx_account_customerid ON BankAccount(CustomerID);
CREATE INDEX idx_transaction_accountid ON PaymentTransaction(AccountID);
CREATE INDEX idx_transaction_deviceid ON PaymentTransaction(DeviceID);
CREATE INDEX idx_authlog_customerid ON AuthenticationLog(CustomerID);
CREATE INDEX idx_fraudalert_transactionid ON FraudAlert(TransactionID);
