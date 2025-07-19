# /src/data_quality_standards.py
import mysql.connector
import re
import pandas as pd
from datetime import datetime

DB_PARAMS = {
    "database": "test",
    "user": "anhquan",
    "password": "123",
    "host": "172.19.0.3",
    "port": 3306
}


def connect_db():
    return mysql.connector.connect(**DB_PARAMS)


def check_null_values():
    conn = connect_db()
    cur = conn.cursor()
    checks = []

    tables = ['Customer', 'BankAccount', 'Card', 'Merchant', 'Device', 'AuthenticationLog', 'PaymentTransaction',
              'FraudAlert']
    for table in tables:
        cur.execute(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = %s AND IS_NULLABLE = 'NO' AND TABLE_SCHEMA = 'staging'
        """, (table,))
        non_nullable_cols = [row[0] for row in cur.fetchall() if
                             row[0] not in ['TransactionID', 'CardID', 'DeviceID', 'AuthLogID']]

        for col in non_nullable_cols:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM `{table}`
                WHERE `{col}` IS NULL
            """)
            null_count = cur.fetchone()[0]
            checks.append({
                'Table': table,
                'Column': col,
                'Check': 'Null Check',
                'Status': 'FAIL' if null_count > 0 else 'PASS',
                'Details': f'{null_count} null values found'
            })

    cur.close()
    conn.close()
    return checks


def check_uniqueness():
    conn = connect_db()
    cur = conn.cursor()
    checks = []

    unique_constraints = [
        ('Customer', 'Email'),
        ('Customer', 'CCCD_Passport'),
        ('BankAccount', 'AccountNumber'),
        ('Card', 'CardNumber'),
        ('Device', 'DeviceFingerprint')
    ]

    for table, column in unique_constraints:
        cur.execute(f"""
            SELECT `{column}`, COUNT(*)
            FROM `{table}`
            GROUP BY `{column}`
            HAVING COUNT(*) > 1
        """)
        duplicates = cur.fetchall()
        checks.append({
            'Table': table,
            'Column': column,
            'Check': 'Uniqueness Check',
            'Status': 'FAIL' if duplicates else 'PASS',
            'Details': f'{len(duplicates)} duplicate values found' if duplicates else 'No duplicates'
        })

    cur.close()
    conn.close()
    return checks


def check_cccd_format():
    conn = connect_db()
    cur = conn.cursor()
    checks = []

    cccd_pattern = r'^\d{12}$'
    cur.execute("SELECT `CustomerID`, `CCCD_Passport` FROM `Customer`")
    rows = cur.fetchall()
    invalid_cccds = [
        row[0] for row in rows if not re.match(cccd_pattern, row[1])
    ]

    checks.append({
        'Table': 'Customer',
        'Column': 'CCCD_Passport',
        'Check': 'Format Check',
        'Status': 'FAIL' if invalid_cccds else 'PASS',
        'Details': f'{len(invalid_cccds)} invalid CCCD formats found' if invalid_cccds else 'All CCCDs valid'
    })

    cur.close()
    conn.close()
    return checks


def check_foreign_keys():
    conn = connect_db()
    cur = conn.cursor()
    checks = []

    fk_checks = [
        ('BankAccount', 'CustomerID', 'Customer', 'CustomerID'),
        ('Card', 'AccountID', 'BankAccount', 'AccountID'),
        ('PaymentTransaction', 'AccountID', 'BankAccount', 'AccountID'),
        ('PaymentTransaction', 'CardID', 'Card', 'CardID'),
        ('PaymentTransaction', 'MerchantID', 'Merchant', 'MerchantID'),
        ('PaymentTransaction', 'DeviceID', 'Device', 'DeviceID'),
        ('PaymentTransaction', 'AuthLogID', 'AuthenticationLog', 'AuthLogID'),
        ('Device', 'CustomerID', 'Customer', 'CustomerID'),
        ('AuthenticationLog', 'CustomerID', 'Customer', 'CustomerID'),
        ('AuthenticationLog', 'DeviceID', 'Device', 'DeviceID'),
        ('AuthenticationLog', 'TransactionID', 'PaymentTransaction', 'TransactionID'),
        ('FraudAlert', 'CustomerID', 'Customer', 'CustomerID'),
        ('FraudAlert', 'TransactionID', 'PaymentTransaction', 'TransactionID'),
        ('FraudAlert', 'DeviceID', 'Device', 'DeviceID'),
        ('FraudAlert', 'AuthLogID', 'AuthenticationLog', 'AuthLogID')
    ]

    for child_table, fk, parent_table, pk in fk_checks:
        cur.execute(f"""
            SELECT COUNT(*)
            FROM `{child_table}` c
            LEFT JOIN `{parent_table}` p ON c.`{fk}` = p.`{pk}`
            WHERE c.`{fk}` IS NOT NULL AND p.`{pk}` IS NULL
        """)
        invalid_fks = cur.fetchone()[0]
        checks.append({
            'Table': child_table,
            'Column': fk,
            'Check': 'Foreign Key Integrity',
            'Status': 'FAIL' if invalid_fks > 0 else 'PASS',
            'Details': f'{invalid_fks} invalid foreign keys found'
        })

    cur.close()
    conn.close()
    return checks


def run_data_quality_checks():
    checks = []
    checks.extend(check_null_values())
    checks.extend(check_uniqueness())
    checks.extend(check_cccd_format())
    checks.extend(check_foreign_keys())

    # Convert to DataFrame for summary
    df = pd.DataFrame(checks)
    print("\nData Quality Check Summary:")
    print(df)
    df.to_csv('data_quality_report.csv', index=False)

    # Log failures
    failed_checks = df[df['Status'] == 'FAIL']
    if not failed_checks.empty:
        print("\nFailed Checks:")
        print(failed_checks)
    print(f"checks = {checks}")
    return df


if __name__ == "__main__":
    run_data_quality_checks()
