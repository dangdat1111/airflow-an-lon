# /src/monitoring_audit.py
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

DB_PARAMS = {
    "database": "test",
    "user": "anhquan",
    "password": "123",
    "host": "172.19.0.3",
    "port": 3306
}

def connect_db():
    return mysql.connector.connect(**DB_PARAMS)


def check_high_value_transactions():
    conn = connect_db()
    cur = conn.cursor()
    checks = []

    cur.execute("""
        SELECT pt.`TransactionID`, pt.`Amount`, pt.`AuthLogID`, al.`AuthType`
        FROM `PaymentTransaction` pt
        LEFT JOIN `AuthenticationLog` al ON pt.`AuthLogID` = al.`AuthLogID`
        WHERE pt.`Amount` > 10000000
        AND (al.`AuthType` IS NULL OR al.`AuthType` NOT IN ('OTP', 'Biometric'))
    """)
    invalid_transactions = cur.fetchall()

    checks.append({
        'Check': 'High-Value Transaction Auth',
        'Status': 'FAIL' if invalid_transactions else 'PASS',
        'Details': f'{len(invalid_transactions)} transactions >10M VND without strong auth'
    })

    cur.close()
    conn.close()
    return checks


def check_unverified_devices():
    conn = connect_db()
    cur = conn.cursor()
    checks = []

    cur.execute("""
        SELECT pt.`TransactionID`, d.`DeviceID`, d.`Status`
        FROM `PaymentTransaction` pt
        JOIN `Device` d ON pt.`DeviceID` = d.`DeviceID`
        WHERE d.`Status` IN ('Suspicious', 'Blocked')
    """)
    unverified_devices = cur.fetchall()

    checks.append({
        'Check': 'Unverified Device Usage',
        'Status': 'FAIL' if unverified_devices else 'PASS',
        'Details': f'{len(unverified_devices)} transactions from unverified devices'
    })

    cur.close()
    conn.close()
    return checks


def check_daily_transaction_limit():
    conn = connect_db()
    cur = conn.cursor()
    checks = []

    cur.execute("""
        SELECT c.`CustomerID`, c.`FirstName`, c.`LastName`, SUM(pt.`Amount`) as TotalAmount
        FROM `PaymentTransaction` pt
        JOIN `BankAccount` ba ON pt.`AccountID` = ba.`AccountID`
        JOIN `Customer` c ON ba.`CustomerID` = c.`CustomerID`
        LEFT JOIN `AuthenticationLog` al ON pt.`AuthLogID` = al.`AuthLogID`
        WHERE pt.`TransactionDate` >= NOW() - INTERVAL 1 DAY
        GROUP BY c.`CustomerID`, c.`FirstName`, c.`LastName`
        HAVING SUM(pt.`Amount`) > 20000000
        AND COUNT(CASE WHEN al.`AuthType` IN ('OTP', 'Biometric') THEN 1 END) = 0
    """)
    high_spenders = cur.fetchall()

    checks.append({
        'Check': 'Daily Transaction Limit Auth',
        'Status': 'FAIL' if high_spenders else 'PASS',
        'Details': f'{len(high_spenders)} customers with >20M VND/day without strong auth'
    })

    cur.close()
    conn.close()
    return checks


def run_monitoring_audit():
    checks = []
    checks.extend(check_high_value_transactions())
    checks.extend(check_unverified_devices())
    checks.extend(check_daily_transaction_limit())

    # Convert to DataFrame for summary
    # df = pd.DataFrame(checks)
    print("\nMonitoring and Audit Summary:")
    print(f"checks = {checks}")
    # print(df)
    # df.to_csv('monitoring_audit_report.csv', index=False)

    # Log failures
    # failed_checks = df[df['Status'] == 'FAIL']
    # if not failed_checks.empty:
    #    print("\nFailed Checks:")
    #    print(failed_checks)

    


if __name__ == "__main__":
    run_monitoring_audit()
