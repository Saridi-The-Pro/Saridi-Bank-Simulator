import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import sqlite3
import threading
import database

class TestDatabase(unittest.TestCase):
    TEST_ACCOUNTS = {
        "sender": {
            "username": "dummyAccount1",
            "password": "123456789012345",
            "balance": 10000
        },
        "recipient": {
            "username": "dummyAccount2",
            "password": "123456789012345",
            "balance": 0
        }
    }

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.path_patcher = patch("database.DATABASE_PATH", self.db_path)
        self.path_patcher.start()
        self.addCleanup(self.path_patcher.stop)
        result = database.create_table()
        self.assertTrue(result, msg=f"Failed to create test table: {result}")

    def create_dummy_user(self, username="dummyAccount1", password="123456789012345", balance=10000):
        if not isinstance(username, str):
            raise TypeError("username must be a string")
        if not isinstance(password, str):
            raise TypeError("password must be a string")
        if type(balance) is not int:
            raise TypeError("balance must be an integer")
        connection = None
        cursor = None
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (username, password, balance))
            connection.commit()
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            finally:
                if connection is not None:
                    connection.close()
    
    def test_database_path(self):
        self.assertEqual(database.DATABASE_PATH, self.db_path)

    def test_create_table(self):
        self.assertTrue(self.db_path.exists())
    
    def test_create_users_table(self):
        connection = None
        cursor = None
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' and name = 'users'")
            result = cursor.fetchone()
            self.assertIsNotNone(result, msg=f"Failed to create users table: {result}")
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            finally:
                if connection is not None:
                    connection.close()
    
    def test_users_table_structure(self):
        connection = None
        cursor = None
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            columns_names = [column[1] for column in columns]
            self.assertEqual(columns_names, ["id", "username", "password", "balance"])
            columns_types = [column[2] for column in columns]
            self.assertEqual(columns_types, ["INTEGER", "TEXT", "TEXT", "INTEGER"])
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            finally:
                if connection is not None:
                    connection.close()
    
    def test_database_busy_error(self):
        sender = self.TEST_ACCOUNTS["sender"]
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        connection = sqlite3.connect(self.db_path)
        connection.execute("BEGIN EXCLUSIVE")
        try:
            result = database.add_balance(sender["username"], amount)
            self.assertEqual(result, "DATABASE IS BUSY. PLEASE TRY AGAIN.", msg=f"Failed \"add_user\" database: {result}")
        finally:
            connection.rollback()
            connection.close()
    
    def get_user_balance(self, username):
        connection = None
        cursor = None
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT balance FROM users WHERE username = ?", (username, ))
            balance = cursor.fetchone()
            if balance is not None:
                balance = balance[0]
            return balance
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            finally:
                if connection is not None:
                    connection.close()

    def test_add_balance(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        result = database.add_balance(sender["username"], amount)
        self.assertTrue(result, msg=f"Failed \"add_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"] + amount, msg=f"Failed \"add_balance()\" database: {result}")

    def test_add_balance_over_balance(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        sender["balance"] = 999_000_000_000_000
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 1
        result = database.add_balance(sender["username"], amount)
        self.assertTrue(result.startswith("EXCEEDED MAXIMUM BALANCE"), msg=f"Failed \"add_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"], msg=f"Failed \"add_balance()\" database: {result}")

    def test_add_balance_over_transaction(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 100_000_001
        result = database.add_balance(sender["username"], amount)
        self.assertTrue(result.startswith("EXCEEDED MAXIMUM MONEY TRANSACTION"), msg=f"Failed \"add_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"], msg=f"Failed \"add_balance()\" database: {result}")

    def test_add_balance_anomaly_datatype(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amounts = ("10000", 10000j, None, -10000, -10000.9)
        for amount in amounts:
            result = database.add_balance(sender["username"], amount)
            self.assertTrue(result, msg=f"Failed \"add_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"], msg=f"Failed \"add_balance()\" database: {result}")

    def test_add_balance_fake_account(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        amount = 10000
        result = database.add_balance(sender["username"], amount)
        self.assertEqual(result, "UNKNOWN USERNAME!", f"Failed \"add_balance()\" database: {result}")

    def test_add_balance_concurrency(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        results = []
        def transaction_execution():
            result = database.add_balance(sender["username"], amount)
            results.append(result)
        threads = [threading.Thread(target=transaction_execution) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for result in results:
            self.assertTrue(
                result is True or result == "DATABASE IS BUSY. PLEASE TRY AGAIN.",
                f"Failed \"add_balance()\" database: {result}"
            )

    def test_decrease_balance(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        result = database.decrease_balance(sender["username"], amount)
        self.assertTrue(result, msg=f"Failed \"decrease_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"] - amount, msg=f"Failed \"decrease_balance()\" database: {result}")
    
    def test_decrease_balance_over_transaction(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 100_000_001
        result = database.decrease_balance(sender["username"], amount)
        self.assertTrue(result.startswith("EXCEEDED MAXIMUM MONEY TRANSACTION"), msg=f"Failed \"decrease_balance\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])

    def test_decrease_balance_more_than_balance(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 20000
        result = database.decrease_balance(sender["username"], amount)
        self.assertEqual(result, "DO NOT WITHDRAW MORE THAN YOUR BALANCE!", msg=f"Failed \"decrease_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"], msg=f"Failed \"decrease_balance()\" database: {result}")

    def test_decrease_balance_anomaly_datatype(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amounts = ("10000", 10000j, None, -10000, -10000.9)
        for amount in amounts:
            result = database.decrease_balance(sender["username"], amount)
            self.assertTrue(result, msg=f"Failed \"decrease_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"], msg=f"Failed \"decrease_balance()\" database: {result}")
    
    def test_decrease_balance_fake_account(self):
        sender = self.TEST_ACCOUNTS["sender"]
        amount = 10000
        result = database.decrease_balance(sender["username"], amount)
        self.assertEqual(result, "UNKNOWN USERNAME!", msg=f"Failed \"decrease_balance()\" database: {result}")

    def test_decrease_balance_concurrency(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        sender["balance"] = 100_000
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        results = []
        def transaction_execution():
            result = database.decrease_balance(sender["username"], amount)
            results.append(result)
        threads = [threading.Thread(target=transaction_execution) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for result in results:
            self.assertTrue(
                result is True or result == "DATABASE IS BUSY. PLEASE TRY AGAIN.",
                f"Failed \"decrease_balance()\" database: {result}"
            )

    def test_transfer_balance(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        receiver = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        result = database.transfer_balance(sender["username"], amount, receiver["username"])
        self.assertTrue(result, f"Failed \"transfer_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"] - amount, msg=f"Failed \"transfer_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(receiver["username"]), receiver["balance"] + amount, msg=f"Failed \"transfer_balance()\" database: {result}")
    
    def test_transfer_balance_over_balance(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 1
        receiver = self.TEST_ACCOUNTS["recipient"].copy()
        receiver["balance"] = 999_000_000_000_000
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        result = database.transfer_balance(sender["username"], amount, receiver["username"])
        self.assertTrue(result.startswith("EXCEEDED MAXIMUM RECEIVER BALANCE"), msg="Failed \"transfer_balance()\" database: Transferred more than receiver balance limit!")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])
        self.assertEqual(self.get_user_balance(receiver["username"]), receiver["balance"])
    
    def test_transfer_balance_over_transaction(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 100_000_001
        receiver = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        result = database.transfer_balance(sender["username"], amount, receiver["username"])
        self.assertTrue(result.startswith("EXCEEDED MAXIMUM MONEY TRANSACTION"), msg="Failed \"transfer_balance()\" database: Transferred while the transaction amount passed the limit!")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])
        self.assertEqual(self.get_user_balance(receiver["username"]), receiver["balance"])

    def test_transfer_balance_more_than_balance(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 20000
        receiver = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        result = database.transfer_balance(sender["username"], amount, receiver["username"])
        self.assertEqual(result, "DO NOT TRY TO TRANSFER MORE THAN YOUR BALANCE!", msg=f"Failed \"transfer_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])
        self.assertEqual(self.get_user_balance(receiver["username"]), receiver["balance"])

    def test_transfer_balance_anomaly_datatype(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amounts = ("10000", 10000j, None, -10000, -10000.9)
        receiver = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        for amount in amounts:
            result = database.transfer_balance(sender["username"], amount, receiver["username"])
            self.assertTrue(result, msg=f"Failed \"transfer_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"], msg=f"Failed \"transfer_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(receiver["username"]), receiver["balance"], msg=f"Failed \"transfer_balance()\" database: {result}")

    def test_transfer_balance_fake_account(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        result = database.transfer_balance(sender["username"], amount, "fakeAccount123")
        self.assertNotEqual(result,"UNKNOWN RECEIVER USERNAME", msg=f"Failed \"transfer_balance()\" database: {result}")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"], msg=f"Failed \"transfer_balance()\" database: {result}")

    def test_transfer_balance_the_same_account(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        result = database.transfer_balance(sender["username"], amount, sender["username"])
        self.assertEqual(result, "DO NOT TRY TO TRANSFER TO YOURSELF!", msg=f"Failed \"transfer_balance()\" database: {result}")

    def test_transfer_balance_concurrency(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        sender["balance"] = 100000
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        receiver = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        results = []
        def transaction_execution():
            result = database.transfer_balance(sender["username"], amount, receiver["username"])
            results.append(result)
        threads = [threading.Thread(target=transaction_execution) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for result in results:
            self.assertTrue(
                result is True or result == "DATABASE IS BUSY. PLEASE TRY AGAIN.",
                f"Failed \"transfer_balance()\" database: {result}"
            )

    def test_balance_consistency(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        old_username = sender["username"]
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        new_username = "dummyAccount3"
        result = database.update_username_password(True, username=sender["username"], new_username=new_username)
        self.assertTrue(result, msg=f"Failed \"update_username_password()\" database: {result}")
        new_balance = self.get_user_balance(new_username)
        old_balance = self.get_user_balance(old_username)
        self.assertEqual(sender["balance"], new_balance, msg=f"Failed \"update_username_password()\" database: {result}")
        self.assertIsNone(old_balance, msg=f"Failed \"update_username_password()\" database: {result}")

    def test_update_password_bytes_limit(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        long_password = ("✅" * 25)
        database.add_user(sender["username"], sender["password"])
        result = database.update_username_password(False, username=sender["username"], new_password=long_password)
        self.assertEqual(result, "PASSWORD TOO LONG! PLEASE USE A SHORTER PASSWORD.", msg=f"Failed \"update_username_password()\" database: {result}")

    def test_update_exist_username(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        database.add_user(sender["username"], sender["password"])
        receiver = self.TEST_ACCOUNTS["recipient"].copy()
        database.add_user(receiver["username"], receiver["password"])
        result = database.update_username_password(True, username=sender["username"], new_username=receiver["username"])
        self.assertEqual(result, "USERNAME IS ALREADY TAKEN! PLEASE CHOOSE THE OTHER ONE!", msg=f"Failed \"update_username_password()\" database: {result}")

    def test_identical_username(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        database.add_user(sender["username"], sender["password"])
        result = database.update_username_password(True, username=sender["username"], new_username=sender["username"])
        self.assertEqual(result, "DO NOT ENTER THE SAME USERNAME AS THE NEW USERNAME!", msg=f"Failed \"update_username_password()\" database: {result}")
    
    def test_identical_password(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        database.add_user(sender["username"], sender["password"])
        result = database.update_username_password(False, username=sender["username"], new_password=sender["password"])
        self.assertEqual(result, "DO NOT ENTER THE SAME PASSWORD AS THE NEW PASSWORD!", msg=f"Failed \"update_username_password()\" database: {result}")

    def test_add_exist_username(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        database.add_user(sender["username"], sender["password"])
        result = database.add_user(sender["username"], sender["password"])
        self.assertEqual(result, "USERNAME IS ALREADY TAKEN! PLEASE CHOOSE THE OTHER ONE!", msg=f"Failed \"add_user()\" database: {result}")

    def test_add_user_blank_username(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        sender["username"] = ""
        result = database.add_user(sender["username"], sender["password"])
        self.assertNotEqual(result, "DO NOT LEAVE USERNAME OR NEW USERNAME BLANK", msg=f"Failed \"add_user()\" database: {result}")

    def test_add_user_whitespace_username(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        sender["username"] = "     "
        result = database.add_user(sender["username"], sender["password"])
        self.assertEqual(result, "DO NOT LEAVE USERNAME OR NEW USERNAME BLANK!", msg=f"Failed \"add_user()\" database: {result}")

    def test_add_user_blank_password(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        sender["password"] = ""
        result = database.add_user(sender["username"], sender["password"])
        self.assertEqual(result, "DO NOT LEAVE THE PASSWORD BLANK!", msg=f"Failed \"add_user()\" database: {result}")
    
    def test_add_user_whitespace_password(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        sender["password"] = "     "
        result = database.add_user(sender["username"], sender["password"])
        self.assertEqual(result, "DO NOT LEAVE THE PASSWORD BLANK!", msg=f"Failed \"add_user()\" database: {result}")

    def test_add_user_password_bytes_limit(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        long_password = ("✅" * 25)
        result = database.add_user(sender["username"], long_password)
        self.assertEqual(result, "YOUR PASSWORD IS TOO LONG! PLEASE USE A SHORTER PASSWORD.", msg=f"Failed \"add_user()\" database: {result}")

if __name__ == "__main__":
    unittest.main()