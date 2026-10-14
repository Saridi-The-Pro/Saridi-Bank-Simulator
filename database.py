import sqlite3
from pathlib import Path
from bcrypt import gensalt, hashpw, checkpw
from time import sleep
from config import DATABASE_PATH, MAX_BALANCE, MAX_TRANSACTION, USERNAME_MAX_LENGTH, PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MAX_BYTES

def delete_table():
    connection = None
    cursor = None
    print("⚠WARNING⚠")
    print("IF YOU DID THIS ACTION, YOU WILL DELETE THE TABLE COMPLETELY WITHOUT ANY TRACE")
    print("THIS ACTION CANNOT BE UNDONE!")
    status = input("IF YOU UNDERSTAND, FACE YOUR OWN RISK! (yes/no): ")
    if status.lower() == "yes":
        print("⚠WARNING⚠")
        sleep(0.5)
        print("THE TABLE WILL BE DELETED SOON!")
        sleep(0.5)
        print("===CONNECTING TO SQLITE===")
        sleep(0.5)
        try:
            connection = sqlite3.connect(DATABASE_PATH)
            cursor = connection.cursor()
            print("===DELETING THE TABLE RIGHT NOW!===")
            sleep(0.5)
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'sqlite_sequence'")
            if cursor.fetchone() is not None:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'users'")
            connection.commit()
            print("===CHANGES SAVED===")
        except sqlite3.Error:
            if connection is not None:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
            print("===ERROR OCCURED===")
            print("===TABLE DELETION FAILED!===")
        except OSError:
            if connection is not None:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
            print("===ERROR OCURED===")
            print("===DATABASE OPERATION FAILED DUE TO A FILE SYSTEM ERROR===")
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

def create_table():
    connection = None
    cursor = None
    try:
        database_path = Path(DATABASE_PATH)
        database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0
        );
        """)
        connection.commit()
        return True
    except sqlite3.Error:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "DATABASE INITIALIZATION FAILED!"
    except OSError:
        return "DATABASE FOLDER COULD NOT BE CREATED OR ACCESSED!"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def verification(username):
    connection = None
    cursor = None
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def search_username(username):
    connection = None
    cursor = None
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result is not None:
            result = result[0]
        return result
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def add_user(username, password):
    if not isinstance(username, str):
        return "ENTER CHARACTERS ONLY!"
    if not isinstance(password, str):
        return "ENTER CHARACTERS ONLY!"
    length_new_user = len(username)
    length_new_pass = len(password)
    if length_new_user == 0:
        return "DO NOT LEAVE USERNAME OR NEW USERNAME BLANK!"
    if length_new_user > USERNAME_MAX_LENGTH:
        return f"YOUR USERNAME IS TOO LONG (Maximum {USERNAME_MAX_LENGTH} Characters)!"
    if username.isalnum() == False:
        return "SYMBOLS ARE NOT ALLOWED!"
    if length_new_pass == 0:
        return "DO NOT LEAVE THE PASSWORD BLANK!"
    if length_new_pass < PASSWORD_MIN_LENGTH:
        return f"YOUR PASSWORD IS TOO SHORT (Minimum {PASSWORD_MIN_LENGTH} Characters)!"
    if length_new_pass > PASSWORD_MAX_LENGTH:
        return f"YOUR PASSWORD IS TOO LONG (Maximum {PASSWORD_MAX_LENGTH} Characters)!"
    bytes_password = password.encode("utf-8")
    if len(bytes_password) > PASSWORD_MAX_BYTES:
        return f"YOUR PASSWORD IS TOO LONG! PLEASE USE A SHORTER PASSWORD."
    decode_password = hashpw(bytes_password, gensalt(rounds=12)).decode("utf-8")
    connection = None
    cursor = None
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, decode_password))
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "USERNAME IS ALREADY TAKEN! PLEASE CHOOSE THE OTHER ONE!"
    except sqlite3.ProgrammingError:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "ACCOUNT REGISTRATION FAILED DUE TO AN INTERNAL ERROR!"
    except sqlite3.OperationalError:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "ACCOUNT REGISTRATION FAILED: DATABASE OPERATION ERROR!"
    except sqlite3.Error:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "ACCOUNT REGISTRATION FAILED: DATABASE ERROR!"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def update_username_password(status, username, new_username="", new_password=""):
    if not isinstance(status, bool):
        return "UNKNOWN CONDITION!"
    connection = None
    cursor = None
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        check = cursor.fetchone()
        if check is None:
            return "UNKNOWN USERNAME!"
        else:
            # When the status value is "True", the changes lead to "Username".
            if status is True:
                if not isinstance(new_username, str):
                    return "ENTER CHARACTERS ONLY!"
                length_new_user = len(new_username)
                if length_new_user == 0:
                    return "DO NOT LEAVE USERNAME OR NEW USERNAME BLANK!"
                cursor.execute("SELECT username FROM users WHERE username = ?", (new_username,))
                validation = cursor.fetchone()
                if validation is not None:
                    validation = validation[0]
                if username == new_username:
                    return "DO NOT ENTER THE SAME USERNAME AS THE NEW USERNAME!"
                if length_new_user > USERNAME_MAX_LENGTH:
                    return f"YOUR USERNAME IS TOO LONG (Maximum {USERNAME_MAX_LENGTH} Characters)!"
                if new_username.isalnum() == False:
                    return "SYMBOLS ARE NOT ALLOWED!"
                if validation == new_username:
                    return "USERNAME IS ALREADY TAKEN! PLEASE CHOOSE THE OTHER ONE!"
                else:
                    try:
                        cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, username))
                        connection.commit()
                        return True
                    except sqlite3.IntegrityError:
                        if connection is not None:
                            try:
                                connection.rollback()
                            except sqlite3.Error:
                                pass
                        return "USERNAME IS ALREADY TAKEN! PLEASE CHOOSE THE OTHER ONE!"
            # When the status value is "False", the changes lead to "Password".
            elif status is False:
                if not isinstance(new_password, str):
                    return "ENTER CHARACTERS ONLY!"
                length_new_pass = len(new_password)
                if length_new_pass == 0:
                    return "DO NOT LEAVE THE PASSWORD BLANK!"
                if length_new_pass < PASSWORD_MIN_LENGTH:
                    return f"YOUR PASSWORD IS TOO SHORT (Minimum {PASSWORD_MIN_LENGTH} Characters)!"
                if length_new_pass > PASSWORD_MAX_LENGTH:
                    return f"YOUR PASSWORD IS TOO LONG (Maximum {PASSWORD_MAX_LENGTH} Characters)!"
                cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
                hashed_password = cursor.fetchone()
                if hashed_password is None:
                    return "PASSWORD HASH NOT FOUND!"
                stored_password = hashed_password[0]
                if not isinstance(stored_password, str):
                    return "SAVED PASSWORD ERROR IN STORAGE!"
                stored_password = stored_password.encode("utf-8")
                bytes_password = new_password.encode("utf-8")
                if len(bytes_password) > PASSWORD_MAX_BYTES:
                    return "PASSWORD TOO LONG! PLEASE USE A SHORTER PASSWORD."
                try:
                    if checkpw(bytes_password, stored_password) is True:
                        return "DO NOT ENTER THE SAME PASSWORD AS THE NEW PASSWORD!"
                except ValueError:
                    return "SAVED PASSWORD ERROR IN STORAGE!"
                cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashpw(bytes_password, gensalt(rounds=12)).decode("utf-8"), username))
                connection.commit()
                return True
    except sqlite3.ProgrammingError:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "ACCOUNT UPDATE FAILED DUE TO AN INTERNAL ERROR!"
    except sqlite3.OperationalError:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "ACCOUNT UPDATE FAILED: DATABASE OPERATION ERROR!"
    except sqlite3.Error:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "ACCOUNT UPDATE FAILED: DATABASE ERROR!"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def delete_user(username):
    connection = None
    cursor = None
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM users WHERE username  = ?", (username,))
        connection.commit()
        success = cursor.rowcount > 0
        return success
    except sqlite3.Error:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "ACCOUNT DELETION FAILED!"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def view_balance(username):
    connection = None
    cursor = None
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
        balance = cursor.fetchone()
        if balance is not None:
            balance = balance[0]
        return balance
    except sqlite3.Error:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "UNABLE TO RETRIEVE BALANCE!"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def add_balance(username, amount):
    connection = None
    cursor = None
    try:
        amount = int(amount)
        if amount > 0:
            if amount > MAX_TRANSACTION:
                return f"EXCEEDED MAXIMUM MONEY TRANSACTION (MAX {MAX_TRANSACTION:,})!"
            else:
                connection = sqlite3.connect(DATABASE_PATH)
                cursor = connection.cursor()
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
                balance = cursor.fetchone()
                if balance is None:
                    return "UNKNOWN USERNAME!"
                balance = balance[0]
                if (balance + amount) > MAX_BALANCE:
                    return f"EXCEEDED MAXIMUM BALANCE (MAX {MAX_BALANCE:,})!"
                else:
                    cursor.execute("UPDATE users SET balance = (balance + ?) WHERE username = ?", (amount, username))
                    result = cursor.rowcount
                    if result != 0:
                        connection.commit()
                        return True
                    else:
                        connection.rollback()
                        return "UNKNOWN USERNAME!"
        else:
            return "DO NOT ENTER ZERO OR MINUS NUMBERS!"
    except ValueError:
        return "INVALID AMOUNT! PLEASE ENTER A WHOLE NUMBER."
    except TypeError:
        return "INVALID AMOUNT! PLEASE ENTER A WHOLE NUMBER."
    except OverflowError:
        return "AMOUNT IS TOO LARGE!"
    except sqlite3.OperationalError as error:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        if error.sqlite_errorcode == sqlite3.SQLITE_BUSY:
            return "DATABASE IS BUSY. PLEASE TRY AGAIN."
        return "THE TRANSACTION COULD NOT BE PROCESSED AT THIS TIME. PLEASE TRY AGAIN SHORTLY."
    except sqlite3.Error:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "DEPOSIT FAILED DUE TO A DATABASE ERROR!"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def decrease_balance(username, amount):
    connection = None
    cursor = None
    try:
        amount = int(amount)
        if amount > 0:
            if amount > MAX_TRANSACTION:
                return f"EXCEEDED MAXIMUM MONEY TRANSACTION (MAX {MAX_TRANSACTION:,})!"
            else:
                connection = sqlite3.connect(DATABASE_PATH)
                cursor = connection.cursor()
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
                balance = cursor.fetchone()
                if balance is None:
                    return "UNKNOWN USERNAME!"
                balance = balance[0]
                if amount <= balance:
                    cursor.execute("UPDATE users SET balance = (balance - ?) WHERE username = ?", (amount, username))
                    result = cursor.rowcount
                    if result != 0:
                        connection.commit()
                        return True
                    else:
                        connection.rollback()
                        return "UNKNOWN USERNAME!"
                else:
                    return "DO NOT WITHDRAW MORE THAN YOUR BALANCE!"
        else:
            return "DO NOT ENTER ZERO OR MINUS NUMBERS!"
    except ValueError:
        return "INVALID AMOUNT! PLEASE ENTER A WHOLE NUMBER."
    except TypeError:
        return "INVALID AMOUNT! PLEASE ENTER A WHOLE NUMBER."
    except OverflowError:
        return "AMOUNT IS TOO LARGE!"
    except sqlite3.OperationalError as error:
        try:
            connection.rollback()
        except sqlite3.Error:
            pass
        if error.sqlite_errorcode == sqlite3.SQLITE_BUSY:
            return "DATABASE IS BUSY. PLEASE TRY AGAIN."
        return "THE TRANSACTION COULD NOT BE PROCESSED AT THIS TIME. PLEASE TRY AGAIN SHORTLY."
    except sqlite3.Error:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "WITHDRAWAL FAILED DUE TO A DATABASE ERROR!"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def transfer_balance(username, amount, receiver):
    if username == receiver:
        return "DO NOT TRY TO TRANSFER TO YOURSELF!"
    connection = None
    cursor = None
    try:
        amount = int(amount)
        if amount > 0:
            if amount > MAX_TRANSACTION:
                return f"EXCEEDED MAXIMUM MONEY TRANSACTION (MAX {MAX_TRANSACTION:,})!"
            else:
                connection = sqlite3.connect(DATABASE_PATH)
                cursor = connection.cursor()
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
                balance = cursor.fetchone()
                if balance is None:
                    return "UNKNOWN USERNAME!"
                balance = balance[0]
                cursor.execute("SELECT balance FROM users WHERE username = ?", (receiver,))
                balance_receiver = cursor.fetchone()
                if balance_receiver is None:
                    return "UNKNOWN RECEIVER USERNAME!"
                balance_receiver = balance_receiver[0]
                if (balance_receiver + amount) > MAX_BALANCE:
                    return f"EXCEEDED MAXIMUM RECEIVER BALANCE (MAX {MAX_BALANCE:,})!"
                else:
                    if balance < amount:
                        return "DO NOT TRY TO TRANSFER MORE THAN YOUR BALANCE!"
                    cursor.execute("UPDATE users SET balance = (balance + ?) WHERE username = ?", (amount, receiver))
                    success = cursor.rowcount
                    cursor.execute("UPDATE users SET balance = (balance - ?) WHERE username = ?", (amount, username))
                    success += cursor.rowcount
                    if success != 2:
                        connection.rollback()
                        return "TRANSACTION FAILED!"
                    else:
                        connection.commit()
                        return True
        else:
            return "DO NOT ENTER NEGATIVE NUMBER, OR ZERO!"
    except TypeError:
        return "INVALID TRANSFER AMOUNT!"
    except ValueError:
        return "INVALID TRANSFER AMOUNT!"
    except OverflowError:
        return "AMOUNT IS TOO LARGE!"
    except sqlite3.OperationalError as error:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        if error.sqlite_errorcode == sqlite3.SQLITE_BUSY:
            return "DATABASE IS BUSY. PLEASE TRY AGAIN."
        return "THE TRANSACTION COULD NOT BE PROCESSED AT THIS TIME. PLEASE TRY AGAIN SHORTLY."
    except sqlite3.Error:
        if connection is not None:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
        return "TRANSFER FAILED DUE TO A DATABASE ERROR!"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
if __name__ == "__main__":
    """=== MAINTENANCE MODE ==="""

    # ADDING AND DELETING CLIENT ACCOUNTS:
    # print(f"Status: {add_user("admin", "admin1234")}")
    # print(f"Status: {delete_user("admin")}")
    
    # CHANGING CLIENT USERNAME AND PASSWORD:
    # print(f"Status: {update_username_password(True, "admin", "admin2")}")

    # VERIFY WHETHER THE USERNAME AND PASSWORD EXIST:
    # print(f"Status: {verification("admin")}")
    
    # CHECKING IF A USERNAME EXISTS:
    # print(f"Username has been found: {search_username("admin")}")

    # VIEWING A CLIENT'S BALANCE:
    # print(f"Balance admin: {view_balance("admin")}")

    # INCREASING AND DECREASING CLIENT BALANCES:
    # print(f"Status: {add_balance("admin", 1000)}")
    # print(f"Status: {decrease_balance("admin", 1000)}")

    # TRANSFER FUNDS TO ANOTHER CLIENT:
    # print(f"Status: {transfer_balance("admin", 0, "admin2")}")

    """
    ===== ⚠DANGER⚠ =====
    NEVER RUN THIS COMMAND UNLESS THERE IS AN EMERGENCY, SUCH AS:
    - CORRUPTED DATABASE CONTENT
    - INACCESSIBLE DATABASE
    USE THIS WITH EXTREME CAUTION.
    """
    # delete_table()
    # create_table()