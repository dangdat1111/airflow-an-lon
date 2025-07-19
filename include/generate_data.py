# /src/generate_data.py
import mysql.connector
import random
from faker import Faker
from datetime import datetime, timedelta
import uuid
import string

# Initialize Faker for realistic data
fake = Faker()

# Database connection parameters
DB_PARAMS = {
    "database": "test",
    "user": "anhquan",
    "password": "123",
    "host": "172.19.0.3",
    "port": 3306
}

def connect_db():
    print("--------connect success---------")
    return mysql.connector.connect(**DB_PARAMS)

def generate_cccd():
    """Generate a 12-digit CCCD (Vietnam Citizen ID)."""
    return ''.join(random.choices(string.digits, k=12))

def generate_card_number():
    """Generate a 16-digit card number."""
    return ''.join(random.choices(string.digits, k=16))

def validate_enum(value, allowed_values, field_name):
    """Validate that a value is in the allowed set (replacing CHECK constraints)."""
    if value not in allowed_values:
        raise ValueError(f"Invalid {field_name}: {value}. Must be one of {allowed_values}")
    return value

def generate_data():
    conn = connect_db()
    cur = conn.cursor()

    # Allowed values for enum-like fields
    customer_statuses = ['Active', 'Suspended', 'Inactive']
    account_types = ['Checking', 'Savings', 'Credit']
    card_types = ['Debit', 'Credit', 'Prepaid']
    card_statuses = ['Active', 'Blocked', 'Expired']
    device_types = ['Mobile', 'Desktop', 'Tablet']
    device_statuses = ['Trusted', 'Suspicious', 'Blocked']
    risk_tags = ['Low', 'Medium', 'High']
    auth_types = ['OTP', 'Biometric', 'Password']
    auth_statuses = ['Success', 'Failed', 'Pending']
    transaction_types = ['Online', 'POS', 'ATM', 'Transfer', 'Refund']
    transaction_statuses = ['Completed', 'Pending', 'Declined']
    alert_statuses = ['Open', 'Resolved', 'False']

    # Insert Customers (10 customers)
    customers = []
    for _ in range(10):
        cur.execute("""
            INSERT INTO `Customer` (`FirstName`, `LastName`, `Email`, `Phone`, `Address`, `CCCD_Passport`, `DateOfBirth`, `Status`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            fake.first_name(),
            fake.last_name(),
            fake.email(),
            fake.phone_number(),
            fake.address().replace('\n', ', '),
            generate_cccd(),
            fake.date_of_birth(minimum_age=18, maximum_age=80),
            validate_enum(random.choice(customer_statuses), customer_statuses, 'Customer.Status')
        ))
        cur.execute("SELECT LAST_INSERT_ID()")
        customers.append(cur.fetchone()[0])
    print(f"customers = {customers}")

    # Insert Bank Accounts (1-3 accounts per customer)
    accounts = []
    for customer_id in customers:
        for _ in range(random.randint(1, 3)):
            cur.execute("""
                INSERT INTO `BankAccount` (`CustomerID`, `AccountType`, `AccountNumber`, `Balance`, `OpenDate`, `Status`)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                customer_id,
                validate_enum(random.choice(account_types), account_types, 'BankAccount.AccountType'),
                generate_card_number(),
                round(random.uniform(100000, 50000000), 2),  # Balance in VND
                fake.date_between(start_date='-2y', end_date='today'),
                validate_enum(random.choice(['Active', 'Frozen']), ['Active', 'Frozen'], 'BankAccount.Status')
            ))
            cur.execute("SELECT LAST_INSERT_ID()")
            accounts.append(cur.fetchone()[0])
    print(f"accounts = {accounts}")

    # Insert Cards (0-2 cards per account)
    cards = []
    for account_id in accounts:
        for _ in range(random.randint(0, 2)):
            cur.execute("""
                INSERT INTO `Card` (`AccountID`, `CardNumber`, `CardType`, `ExpiryDate`, `CVV`, `Status`)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                account_id,
                generate_card_number(),
                validate_enum(random.choice(card_types), card_types, 'Card.CardType'),
                fake.date_between(start_date='today', end_date='+3y'),
                ''.join(random.choices(string.digits, k=3)),
                validate_enum(random.choice(card_statuses), card_statuses, 'Card.Status')
            ))
            cur.execute("SELECT LAST_INSERT_ID()")
            cards.append(cur.fetchone()[0])
    print(f"cards = {cards}")

    # Insert Merchants (10 merchants)
    merchants = []
    for _ in range(10):
        risk_score = random.randint(0, 100)
        cur.execute("""
            INSERT INTO `Merchant` (`MerchantName`, `Category`, `Location`, `RiskScore`)
            VALUES (%s, %s, %s, %s)
        """, (
            fake.company(),
            random.choice(['Retail', 'Food', 'Online', 'Travel']),
            fake.address().replace('\n', ', '),
            risk_score
        ))
        cur.execute("SELECT LAST_INSERT_ID()")
        merchants.append(cur.fetchone()[0])
    print(f"merchants = {merchants}")

    # Insert Devices (1-3 devices per customer)
    devices = []
    for customer_id in customers:
        for _ in range(random.randint(1, 3)):
            cur.execute("""
                INSERT INTO `Device` (`CustomerID`, `DeviceType`, `DeviceFingerprint`, `IPAddress`, `LastUsed`, `Status`, `RiskTag`)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                customer_id,
                validate_enum(random.choice(device_types), device_types, 'Device.DeviceType'),
                str(uuid.uuid4()),
                fake.ipv4(),
                fake.date_time_between(start_date='-30d', end_date='now'),
                validate_enum(random.choice(device_statuses), device_statuses, 'Device.Status'),
                validate_enum(random.choice(risk_tags), risk_tags, 'Device.RiskTag')
            ))
            cur.execute("SELECT LAST_INSERT_ID()")
            devices.append(cur.fetchone()[0])
    print(f"devices = {devices}")

    # Insert Authentication Logs (20 logs)
    auth_logs = []
    for _ in range(20):
        cur.execute("""
            INSERT INTO `AuthenticationLog` (`CustomerID`, `TransactionID`, `AuthType`, `AuthDate`, `Status`, `OTPCode`, `BiometricData`, `DeviceID`, `RiskTag`)
            VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s)
        """, (
            random.choice(customers),
            validate_enum(random.choice(auth_types), auth_types, 'AuthenticationLog.AuthType'),
            fake.date_time_between(start_date='-30d', end_date='now'),
            validate_enum(random.choice(auth_statuses), auth_statuses, 'AuthenticationLog.Status'),
            ''.join(random.choices(string.digits, k=6)) if random.choice([True, False]) else None,
            str(uuid.uuid4()) if random.choice([True, False]) else None,
            random.choice(devices) if random.choice([True, False]) else None,
            validate_enum(random.choice(risk_tags), risk_tags, 'AuthenticationLog.RiskTag')
        ))
        cur.execute("SELECT LAST_INSERT_ID()")
        auth_logs.append(cur.fetchone()[0])
    print(f"auth_logs = {auth_logs}")

    # Insert Payment Transactions (50 transactions, including high-value edge cases)
    transaction_ids = []
    for _ in range(50):
        amount = random.uniform(10000, 50000000)  # VND, including high-value cases
        device_id = random.choice(devices) if random.choice([True, False]) else None
        auth_log_id = random.choice(auth_logs) if random.choice([True, False]) else None
        risk_tag = 'High' if amount > 10000000 else random.choice(['Low', 'Medium'])
        cur.execute("""
            INSERT INTO `PaymentTransaction` (`AccountID`, `CardID`, `MerchantID`, `Amount`, `TransactionDate`, `TransactionType`, `Status`, `DeviceID`, `AuthLogID`, `RiskTag`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            random.choice(accounts),
            random.choice(cards) if random.choice([True, False]) else None,
            random.choice(merchants),
            round(amount, 2),
            fake.date_time_between(start_date='-30d', end_date='now'),
            validate_enum(random.choice(transaction_types), transaction_types, 'PaymentTransaction.TransactionType'),
            validate_enum(random.choice(transaction_statuses), transaction_statuses, 'PaymentTransaction.Status'),
            device_id,
            auth_log_id,
            validate_enum(risk_tag, risk_tags, 'PaymentTransaction.RiskTag')
        ))
        cur.execute("SELECT LAST_INSERT_ID()")
        transaction_ids.append(cur.fetchone()[0])

    # Update AuthenticationLog with TransactionID for some records
    for auth_log_id in random.sample(auth_logs, min(10, len(auth_logs))):
        cur.execute("""
            UPDATE `AuthenticationLog`
            SET `TransactionID` = %s
            WHERE `AuthLogID` = %s
        """, (random.choice(transaction_ids), auth_log_id))

    # Insert Fraud Alerts (10 alerts)
    for _ in range(10):
        risk_score = random.randint(0, 100)
        cur.execute("""
            INSERT INTO `FraudAlert` (`CustomerID`, `TransactionID`, `DeviceID`, `AuthLogID`, `AlertType`, `AlertDate`, `RiskScore`, `Status`, `RiskTag`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            random.choice(customers),
            random.choice(transaction_ids) if random.choice([True, False]) else None,
            random.choice(devices) if random.choice([True, False]) else None,
            random.choice(auth_logs) if random.choice([True, False]) else None,
            random.choice(['Unusual Activity', 'High-Risk Merchant', 'Suspicious Device', 'Failed Authentication']),
            fake.date_time_between(start_date='-30d', end_date='now'),
            risk_score,
            validate_enum(random.choice(alert_statuses), alert_statuses, 'FraudAlert.Status'),
            validate_enum(random.choice(risk_tags), risk_tags, 'FraudAlert.RiskTag')
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("Sample data generated successfully.")

if __name__ == "__main__":
    generate_data()
