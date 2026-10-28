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
    
    def test_add_balance(self):
        receiver = self.TEST_ACCOUNTS["sender"]
        amount = 10000
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        result = database.add_balance(receiver["username"], amount)
        if result is not True:
            raise RuntimeError(f"Failed \"add_balance()\" database: {result}")
        self.assertTrue(result)
        connection = None
        cursor = None
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT balance FROM users WHERE username = ?", (receiver["username"], ))
            result = cursor.fetchone()
            if result is not None:
                result = result[0]
            self.assertEqual(result, receiver["balance"] + amount)
        finally:
            try:
                if connection is not None:
                    cursor.close()
            finally:
                if connection is not None:
                    connection.close()
    
    def test_withdraw_balance(self):
        receiver = self.TEST_ACCOUNTS["sender"]
        amount = 10000
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        result = database.decrease_balance(receiver["username"], amount)
        if result is not True:
            raise RuntimeError(f"Failed \"decrease_balance()\" database: {result}")
        self.assertTrue(result)
        connection = None
        cursor = None
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT balance FROM users WHERE username = ?", (receiver["username"], ))
            result = cursor.fetchone()
            if result is not None:
                result = result[0]
            self.assertEqual(result, receiver["balance"] - amount)
        finally:
            try:
                if connection is not None:
                    cursor.close()
            finally:
                if connection is not None:
                    connection.close()
    
    def test_transfer_balance(self):
        sender = self.TEST_ACCOUNTS["sender"]
        self.create_dummy_user(sender["username"], sender["password"], sender["balance"])
        ammount = 10000
        receiver = self.TEST_ACCOUNTS["recipient"]
        self.create_dummy_user(receiver["username"], receiver["password"], receiver["balance"])
        result = database.transfer_balance(sender["username"], ammount, receiver["username"])
        if result is not True:
            raise RuntimeError(f"Failed \"transfer_balance()\" database: {result}")
        self.assertTrue(result)
        connection = None
        cursor = None
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT balance FROM users WHERE username = ?", (sender["username"],))
            result = cursor.fetchone()
            if result is not None:
                result = result[0]
            self.assertEqual(result, sender["balance"] - ammount)
            cursor.execute("SELECT balance FROM users WHERE username = ?", (receiver["username"],))
            result = cursor.fetchone()
            if result is not None:
                result = result[0]
            self.assertEqual(result, receiver["balance"] + ammount)
        finally:
            try:
                if connection is not None:
                    cursor.close()
            finally:
                if connection is not None:
                    connection.close()
    
if __name__ == "__main__":
    unittest.main()