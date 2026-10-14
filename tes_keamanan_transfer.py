import sqlite3
from config import DATABASE_PATH

def transfer_balance(username, amount, receiver, database_path_perusak="DB/bank.db", sqlite3_perusak=False):
    if username == receiver:
        return "DO NOT TRY TO TRANSFER TO YOURSELF!"
    connection = None
    cursor = None
    try:
        amount = int(amount)
        if amount > 0:
            connection = sqlite3.connect(database_path_perusak)
            cursor = connection.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
            balance = cursor.fetchone()
            if balance is not None:
                balance = balance[0]
            cursor.execute("SELECT balance FROM users WHERE username = ?", (receiver,))
            balance_receiver = cursor.fetchone()
            if balance_receiver is not None:
                balance_receiver = balance_receiver[0]
            cursor.execute("UPDATE users SET balance = (balance + ?) WHERE username = ?", (amount, receiver))
            success = cursor.rowcount
            
            print(f"LANGKAH TRANSAKSI 1, SUKSES = {success}")

            if sqlite3_perusak == True:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, 1234))
            
            cursor.execute("UPDATE users SET balance = (balance - ?) WHERE username = ?", (amount, username))
            success += cursor.rowcount
            
            print(f"LANGKAH TRANSAKSI 2, SUKSES = {success}")
            
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

sender = input("Sender: ")
receiver = input("Receiver: ")
amount = int(input("\nAmount: "))
database_path_perusak = input("\nEnter the right database path: ")
sqlite3_perusak = input("Do you want to close the database connection while transaction (yes/no): ")

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

cursor.execute("SELECT balance FROM users WHERE username = ?", (sender,))
balance = cursor.fetchone()
if balance is not None:
    balance = balance[0]

cursor.execute("SELECT balance FROM users WHERE username = ?", (receiver,))
balance_receiver = cursor.fetchone()
if balance_receiver is not None:
    balance_receiver = balance_receiver[0]

print(f"\n{sender} balance = {balance}")
print(f"{receiver} balance = {balance_receiver}\n")


if len(database_path_perusak) != 0:
    print(transfer_balance(sender, amount, receiver, database_path_perusak))
elif sqlite3_perusak.lower() == "yes":
    print(transfer_balance(sender, amount, receiver, sqlite3_perusak=True))
else:
    print(transfer_balance(sender, amount, receiver))

cursor.execute("SELECT balance FROM users WHERE username = ?", (sender,))
balance = cursor.fetchone()
if balance is not None:
    balance = balance[0]

cursor.execute("SELECT balance FROM users WHERE username = ?", (receiver,))
balance_receiver = cursor.fetchone()
if balance_receiver is not None:
    balance_receiver = balance_receiver[0]

print(f"\n{sender} balance after transaction = {balance}")
print(f"{receiver} balance after transaction = {balance_receiver}")