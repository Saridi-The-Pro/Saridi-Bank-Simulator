import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import sqlite3
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
            "balance": 10000
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
        if result is not True:
            raise RuntimeError(f"Failed to create test table: {result}")

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
                if connection is not None:
                    connection.close()
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
            self.assertIsNotNone(result)
        finally:
            try:
                if connection is not None:
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
                if connection is not None:
                    cursor.close()
            finally:
                if connection is not None:
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
                if connection is not None:
                    cursor.close()
            finally:
                if connection is not None:
                    connection.close()

    def test_add_balance(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        result = database.add_balance(sender["username"], amount)
        if result is not True:
            raise RuntimeError(f"Failed \"add_balance()\" database: {result}")
        self.assertTrue(result)
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"] + amount)

    def test_add_balance_over_balance(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        sender["balance"] = 999_000_000_000_000
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 1
        result = database.add_balance(sender["username"], amount)
        if not result.startswith("EXCEEDED MAXIMUM BALANCE"):
            raise RuntimeError("Failed \"add_balance()\" database: Deposit more than receiver balance limit!")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])

    def test_add_balance_over_transaction(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 100_000_001
        result = database.add_balance(sender["username"], amount)
        if not result.startswith("EXCEEDED MAXIMUM MONEY TRANSACTION"):
            raise RuntimeError("Failed \"add_balance()\" database: Deposit while the transaction amount passed the limit!")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])

    def test_add_balance_anomaly_datatype(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amounts = ("10000", 10000j, None, -10000, -10000.9)
        for amount in amounts:
            result = database.add_balance(sender["username"], amount)
            if result is True:
                raise RuntimeError("Failed \"add_balance()\" database: deposit with invalid amount!")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])
 
    def test_decrease_balance(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        result = database.decrease_balance(sender["username"], amount)
        if result is not True:
            raise RuntimeError(f"Failed \"decrease_balance()\" database: {result}")
        self.assertTrue(result)
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"] - amount)
    
    def test_decrease_balance_over_transaction(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 100_000_001
        result = database.decrease_balance(sender["username"], amount)
        if not result.startswith("EXCEEDED MAXIMUM MONEY TRANSACTION"):
            raise RuntimeError("Failed \"decrease_balance\" database: Withdraw while the transaction amount passed the limit!")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])

    def test_decrease_balance_anomaly_datatype(self):
        sender = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amounts = ("10000", 10000j, None, -10000, -10000.9)
        for amount in amounts:
            result = database.decrease_balance(sender["username"], amount)
            if result is True:
                raise RuntimeError("Failed \"decrease_balance()\" database: withdraw with invalid amount!")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])

    def test_transfer_balance(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        receiver = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        result = database.transfer_balance(sender["username"], amount, receiver["username"])
        if result is not True:
            raise RuntimeError(f"Failed \"transfer_balance()\" database: {result}")
        self.assertTrue(result)
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"] - amount)
        self.assertEqual(self.get_user_balance(receiver["username"]), receiver["balance"] + amount)
    
    def test_transfer_balance_over_balance(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 1
        receiver = self.TEST_ACCOUNTS["recipient"].copy()
        receiver["balance"] = 999_000_000_000_000
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        result = database.transfer_balance(sender["username"], amount, receiver["username"])
        if not result.startswith("EXCEEDED MAXIMUM RECEIVER BALANCE"):
            raise RuntimeError("Failed \"transfer_balance()\" database: Transferred more than receiver balance limit!")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])
        self.assertEqual(self.get_user_balance(receiver["username"]), receiver["balance"])
    
    def test_transfer_balance_over_transaction(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 100_000_001
        receiver = self.TEST_ACCOUNTS["recipient"].copy()
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        result = database.transfer_balance(sender["username"], amount, receiver["username"])
        if not result.startswith("EXCEEDED MAXIMUM MONEY TRANSACTION"):
            raise RuntimeError("Failed \"transfer_balance()\" database: Transferred while the transaction amount passed the limit!")
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
            if result is True:
                raise RuntimeError("Failed \"transfer_balance()\" database: Transferred with invalid amount!")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])
        self.assertEqual(self.get_user_balance(receiver["username"]), receiver["balance"])

    def test_transfer_balance_fake_account(self):
        sender = self.TEST_ACCOUNTS["sender"].copy()
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        amount = 10000
        result = database.transfer_balance(sender["username"], amount, "fakeAccount123")
        if result != "UNKNOWN RECEIVER USERNAME!":
            raise RuntimeError("Failed \"transfer_balance()\" database: Transferred into fake account!")
        self.assertEqual(self.get_user_balance(sender["username"]), sender["balance"])

if __name__ == "__main__":
    unittest.main()