import sqlite3
import uuid
import os

from datetime import datetime, timedelta
from decimal import Decimal

from core.authentication.AuthenticationService import AuthenticationService
from core.transaction.Transaction import Transaction
from core.transaction.TransactionRepository import TransactionRepository

DB_PATH = 'WealthTrackersDB.sqlite'
USERNAME = "BasilissaOfNuts"  # Login Username
PASSWORD = "Im2ooUncFor0r5!t"
EMAIL = "IHateAsymDuals@gmail.com"
PHONE = "777-666-9999"

def seed():
    auth = AuthenticationService()
    user_uuid = str(uuid.uuid4())  # Naturally generated UUID for user_id

    salt = os.urandom(16)
    password_hash = auth.hash_password(PASSWORD)
    session_key = auth.derive_aes_key(PASSWORD, salt)

    # --- PHASE 1: Base Data Setup ---
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # --- CLEANUP (Order is vital to avoid FK failures) ---
        print("Cleaning up old records...")
        cursor.execute("DELETE FROM transactions;")
        cursor.execute("DELETE FROM accounts;")
        cursor.execute("DELETE FROM vendors;")
        # Cleanup by username so we catch previous runs regardless of ID
        cursor.execute("DELETE FROM users WHERE username = ?", (USERNAME,))
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='vendors';")

        conn.commit()

        # --- GENERIC CATEGORY SEEDING ---
        generics = [("General Expense",), ("General Income",)]
        for gen in generics:
            cursor.execute("SELECT 1 FROM categories WHERE category_name = ?", gen)
            if not cursor.fetchone():
                cursor.execute("INSERT INTO categories (category_name) VALUES (?)", gen)

        conn.commit()

        # --- USER CREATION ---
        cursor.execute("""
                       INSERT INTO users (user_id, username, password_hash, encryption_salt, enc_email, enc_phone)
                       VALUES (?, ?, ?, ?, ?, ?)
                       """, (user_uuid, USERNAME, password_hash, salt, auth.encrypt(EMAIL, session_key),
                             auth.encrypt(PHONE, session_key)))

        # --- VENDOR SEEDING ---
        vendors_to_seed = [
            ("MICRO CENTER", 8, "Shopping"),
            ("IVY TECH PAYROLL", 3, "Electronic Deposit"),
            ("ALI'I POKE", 11, "Food & Dining"),
            ("PANDA EXPRESS", 11, "Food & Dining"),
            ("DUKE ENERGY", 10, "Bills & Utilities"),
            ("DISCORD", 9, "Entertainment"),
            ("TWITCH", 9, "Entertainment"),
            ("HOYOVERSE", 9, "Entertainment"),
            ("STEAM", 9, "Entertainment")
        ]

        vendor_map = {}
        for name, cat_id, cat_name in vendors_to_seed:
            cursor.execute("INSERT INTO vendors (vendor_name, default_category_id) VALUES (?, ?)", (name, cat_id))
            vendor_map[name] = {"id": cursor.lastrowid, "cat_id": cat_id, "cat_name": cat_name}

        # --- ACCOUNT CREATION ---
        # Checking
        checking_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)",
                       (checking_id, user_uuid, "Ivy Tech Student Checking", "CHECKING",
                        auth.encrypt("1000999888", session_key)))
        cursor.execute("INSERT INTO checking_details VALUES (?, ?)", (checking_id, "074029032"))

        # Savings
        savings_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)",
                       (savings_id, user_uuid, "Emergency Fund", "SAVINGS", auth.encrypt("555666777", session_key)))
        cursor.execute("INSERT INTO savings_details VALUES (?, ?)", (savings_id, 0.045))

        # Credit Card
        credit_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)",
                       (credit_id, user_uuid, "Titanium Rewards Visa", "CREDIT",
                        auth.encrypt("4111222233334444", session_key)))
        cursor.execute("INSERT INTO credit_card_details VALUES (?, ?, ?)",
                       (credit_id, auth.encrypt("999", session_key), 15000.00))

        # Debit Card
        debit_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)",
                       (debit_id, user_uuid, "Daily Swipe Card", "DEBIT",
                        auth.encrypt("5111222233334444", session_key)))
        cursor.execute("INSERT INTO debit_card_details VALUES (?, ?, ?)",
                       (debit_id, auth.encrypt("111", session_key), checking_id))

        conn.commit()
        print(f"Phase 1 complete. User UUID: {user_uuid}")

    except Exception as e:
        if conn: conn.rollback()
        print(f"Phase 1 Failure: {e}")
        return
    finally:
        if conn: conn.close()  # RELEASE LOCK

    # --- PHASE 2: TRANSACTION SEEDING ---
    print("Starting Phase 2: Ingesting original transaction data...")
    txn_repo = TransactionRepository(DB_PATH)

    try:
        # Transaction 1: RTX 5090 Purchase
        vm = vendor_map["MICRO CENTER"]
        txn_repo.save_transaction(Transaction(
            uuid.uuid4(), uuid.UUID(credit_id), vm["id"], "MICRO CENTER",
            vm["cat_id"], vm["cat_name"], Decimal("3999.99"), datetime.now(), 'EXPENSE'
        ))

        # Transaction 2: Monthly Salary
        vm = vendor_map["IVY TECH PAYROLL"]
        txn_repo.save_transaction(Transaction(
            uuid.uuid4(), uuid.UUID(checking_id), vm["id"], "IVY TECH PAYROLL",
            vm["cat_id"], vm["cat_name"], Decimal("3500.00"), datetime.now() - timedelta(days=5), 'INCOME'
        ))

        # Transaction 3: Poke Bowl Delivery
        vm = vendor_map["ALI'I POKE"]
        txn_repo.save_transaction(Transaction(
            uuid.uuid4(), uuid.UUID(debit_id), vm["id"], "ALI'I POKE",
            vm["cat_id"], vm["cat_name"], Decimal("35.39"), datetime.now(), 'EXPENSE'
        ))

        # Transaction 4: Panda Express Lunch
        vm = vendor_map["PANDA EXPRESS"]
        txn_repo.save_transaction(Transaction(
            uuid.uuid4(), uuid.UUID(debit_id), vm["id"], "PANDA EXPRESS",
            vm["cat_id"], vm["cat_name"], Decimal("15.45"), datetime.now(), 'EXPENSE'
        ))

        # Transaction 5: Monthly Electricity
        vm = vendor_map["DUKE ENERGY"]
        txn_repo.save_transaction(Transaction(
            uuid.uuid4(), uuid.UUID(checking_id), vm["id"], "DUKE ENERGY",
            vm["cat_id"], vm["cat_name"], Decimal("142.50"), datetime.now(), 'EXPENSE'
        ))

        # Transaction 6: Discord Nitro
        vm = vendor_map["DISCORD"]
        txn_repo.save_transaction(Transaction(
            uuid.uuid4(), uuid.UUID(credit_id), vm["id"], "DISCORD",
            vm["cat_id"], vm["cat_name"], Decimal("9.99"), datetime.now(), 'EXPENSE'
        ))

        # Transaction 7: Twitch Subscription
        vm = vendor_map["TWITCH"]
        txn_repo.save_transaction(Transaction(
            uuid.uuid4(), uuid.UUID(credit_id), vm["id"], "TWITCH",
            vm["cat_id"], vm["cat_name"], Decimal("5.99"), datetime.now(), 'EXPENSE'
        ))

        # Transaction 8: Gacha Spending
        vm = vendor_map["HOYOVERSE"]
        txn_repo.save_transaction(Transaction(
            uuid.uuid4(), uuid.UUID(credit_id), vm["id"], "HOYOVERSE",
            vm["cat_id"], vm["cat_name"], Decimal("80.99"), datetime.now(), 'EXPENSE'
        ))

        # Transaction 9: New PC Game
        vm = vendor_map["STEAM"]
        txn_repo.save_transaction(Transaction(
            uuid.uuid4(), uuid.UUID(debit_id), vm["id"], "STEAM",
            vm["cat_id"], vm["cat_name"], Decimal("59.99"), datetime.now(), 'EXPENSE'
        ))

        print(f"--- SEED COMPLETE ---")
        print(f"User: {USERNAME} is now ready for testing.")
    except Exception as e:
        print(f"Phase 2 Failure: {e}")

if __name__ == "__main__":
    seed()