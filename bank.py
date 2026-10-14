from bcrypt import checkpw
from auth import login, register, haveAccount, validation
from database import (verification, create_table, view_balance, search_username, delete_user,
                      update_username_password, add_balance, decrease_balance, transfer_balance)
from config import MAX_BALANCE, MAX_TRANSACTION, USERNAME_MAX_LENGTH, PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MAX_BYTES

class Bank:
    def __init__(self):
        self.username = ""
    def __parsing_money(self, condition):
        try:
            if condition:
                money = int(input("\nPlease input your of amount money: "))
                return money
            else:
                money = int(input("\nPlease input your of amount money: "))
                receiver = input("To who you want to transfer: ")
                return [receiver, money]
        except ValueError:
            return "\nENTER NUMBER ONLY OR DO NOT LEAVE IT BLANK!"
        except OverflowError:
            return "\nAMOUNT IS TOO LARGE!"

    def __parsing_username(self, username):
        if not isinstance(username, str):
            return "ENTER CHARACTERS ONLY!"
        length_user = len(username)
        if length_user == 0:
            return "\nDO NOT LEAVE THE USERNAME BLANK!"
        elif length_user > USERNAME_MAX_LENGTH:
            return f"\nYOUR USERNAME IS TOO LONG (Maximum {USERNAME_MAX_LENGTH} Characters)!"
        elif username.isalnum() is False:
            return "\nSYMBOLS ARE NOT ALLOWED!"
        else:
            return True

    def __parsing_password(self, password):
        if not isinstance(password, str):
            return "ENTER CHARACTERS ONLY!"
        length_pass = len(password)
        if length_pass == 0:
            return "\nDO NOT LEAVE THE PASSWORD BLANK!"
        elif length_pass < PASSWORD_MIN_LENGTH:
            return f"\nYOUR PASSWORD IS TOO SHORT (Minimum {PASSWORD_MIN_LENGTH} Characters)!"
        elif length_pass > PASSWORD_MAX_LENGTH:
            return f"\nYOUR PASSWORD IS TOO LONG (Maximum {PASSWORD_MAX_LENGTH} Characters)!"
        else:
            return True

    def __validation_money(self, money):
        return money > 0
    
    def __set_balance(self, status, username, money, receiver=""):
        if status == "TRANSFER":
            return transfer_balance(username, money, receiver)
        elif status == "DEPOSIT":
            return add_balance(username, money)
        elif status == "WITHDRAW":
            return decrease_balance(username, money)
        else:
            return "\nENTER VALID ACTION!"
    
    def get_balance(self, username):
        return view_balance(username)

    def delete(self, username):
        if search_username(username) is None:
            return ["\nUNKNOWN USERNAME!", False]
        balance = self.get_balance(username)
        if balance is None:
            return ["\nUNKNOWN BALANCE!", False]
        elif balance > 0:
            return ["\nWITHDRAW YOUR ENTIRE BALANCE FIRST!", False]
        else:
            print("\nARE YOU SURE?")
            print("THIS ACTION CANNOT BE UNDONE!")
            print("Type your \"USERNAME\" and \"PASSWORD\" before deleting this account")
            user = input("\nUSERNAME: ")
            pws = input("PASSWORD: ")
            valid = validation(user, pws)
            if isinstance(valid, str):
                return [valid, False]
            if valid is False or username != user:
                return ["\nENTER THE CORRECT USERNAME AND PASSWORD!", False]
            else:
                result = delete_user(username)
                if result is False:
                    return ["\nUNKNOWN USERNAME!", False]
                else:
                    return [f"\n\"{username}\" ACCOUNT HAS BEEN DELETED!", True]

    def change_username(self, username):
        if search_username(username) is None:
            return "\nUNKNOWN USERNAME!"
        password = input("\nInput password first: ")
        check = validation(username, password)
        if isinstance(check, str):
            return check
        new_username = input("Please enter your new username: ")
        valid = self.__parsing_username(new_username)
        if isinstance(valid, str):
            return valid
        if new_username == username:
            return "\nDO NOT USE THE SAME USERNAME!"
        if search_username(new_username) is not None:
            return "\nUSERNAME IS ALREADY TAKEN! PLEASE CHOOSE THE OTHER ONE!"
        # When the status value is "True", the changes lead to "Username". 
        result = update_username_password(True, username, new_username)
        if isinstance(result, str):
            return result
        elif result:
            return [True, new_username]
        else:
            return "\nUSERNAME CHANGE FAILED!"
    
    def change_password(self, username):
        password = input("\nInput password first: ")
        check = validation(username, password)
        if isinstance(check, str):
            return check
        else:
            if search_username(username) is not None:
                new_password = input("Please enter your new password: ")
                hashed_password = verification(username)
                if hashed_password is None:
                    return "\nUNKNOWN USERNAME!"
                stored_password = hashed_password.encode("utf-8")
                valid = self.__parsing_password(new_password)
                if isinstance(valid, str):
                    return valid
                bytes_password = new_password.encode("utf-8")
                if len(bytes_password) > PASSWORD_MAX_BYTES:
                    return "\nPASSWORD TOO LONG! PLEASE USE A SHORTER PASSWORD."
                if checkpw(bytes_password, stored_password) is False:
                    # When the status value is "False", the changes lead to "Password".
                    result2 = update_username_password(False, username, "", new_password)
                    if isinstance(result2, str):
                        return result2
                    elif result2:
                        return True
                else:
                    return "\nDO NOT USE THE SAME PASSWORD!"
            else:
                return "\nUNKNOWN USERNAME!"

    def deposit(self, username):
        result = self.__parsing_money(True)
        if isinstance(result, int):
            if not self.__validation_money(result):
                return f"\nDO NOT ENTER NEGATIVE, ZERO, OR LEAVE IT BLANK!"
            balance = self.get_balance(username)
            if balance is None:
                return "\nUNKNOWN BALANCE!"
            elif result > MAX_TRANSACTION:
                return f"\nEXCEEDED MAXIMUM MONEY TRANSACTION (MAX {MAX_TRANSACTION:,})!"
            elif (balance + result) > MAX_BALANCE:
                return f"\nEXCEEDED MAXIMUM BALANCE (MAX {MAX_BALANCE:,})!"
            else:
                status = self.__set_balance("DEPOSIT", username, result)
                if isinstance(status, str):
                    return status
                if status is True:
                    return f"\n{result:,} successfully deposited to your balance!"
                else:
                    return status
        else:
            return result
        
    def withdraw(self, username):
        result = self.__parsing_money(True)
        if isinstance(result, int):
            if not self.__validation_money(result):
                return "\nDO NOT ENTER NEGATIVE NUMBERS, ZERO, OR LEAVE IT BLANK!!"
            balance = self.get_balance(username)
            if balance is None:
                return "\nUNKNOWN BALANCE!"
            elif balance == 0:
                return "\nDO NOT TRY TO WITHDRAW WHILE BALANCE IS ZERO!"
            elif result > balance:
                return "\nDO NOT WITHDRAW MORE THAN YOUR BALANCE!"
            elif result > MAX_TRANSACTION:
                return f"\nEXCEEDED MAXIMUM MONEY TRANSACTION (MAX {MAX_TRANSACTION:,})!"
            else:
                status = self.__set_balance("WITHDRAW", username, result)
                if isinstance(status, str):
                    return status
                if status is True:
                    return f"\n{result:,} successfully withdrawn!"
                else:
                    return status
        else:
            return result
    def transfer(self, username):
        result = self.__parsing_money(False)
        if isinstance(result, list):
            if not self.__validation_money(result[1]):
                return "\nDO NOT ENTER NEGATIVE NUMBER, OR ZERO"
            balance = self.get_balance(username)
            if balance is None:
                return "\nUNKNOWN BALANCE!"
            elif balance == 0:
                return "\nDO NOT TRY TO TRANSFER WHILE BALANCE IS ZERO!"
            elif result[1] > balance:
                return "\nDO NOT TRY TO TRANSFER MORE THAN YOUR BALANCE!"
            elif result[1] > MAX_TRANSACTION:
                return f"\nEXCEEDED MAXIMUM MONEY TRANSACTION (MAX {MAX_TRANSACTION:,})!"
            receiver_username = search_username(result[0])
            if receiver_username is None:
                return "\nUNAVAILABLE RECEIVER ACCOUNT!"
            elif receiver_username == username:
                return "\nTRANSFER MONEY TO YOURSELF IS PROHIBITED!"
            else:
                receiver_balance = self.get_balance(receiver_username)
                if receiver_balance is None:
                    return "UNKNOWN RECEIVER BALANCE!"
                if (receiver_balance + result[1]) > MAX_BALANCE:
                    return f"\nEXCEEDED MAXIMUM BALANCE RECEIVER (MAX {MAX_BALANCE:,})!"
                else:
                    status = self.__set_balance("TRANSFER", username, result[1], receiver_username)
                    if isinstance(status, str):
                        return status
                    if status is True:
                        return f"\n{result[1]:,} successfully transferred to {result[0]}!"
                    else:
                        return status
        else:
            return result
            
    def info(self):
        return "\n|| [1] DEPOSIT                    ||\n|| [2] WITHDRAW                   ||\n|| [3] TRANSFER                   ||\n|| [4] CHANGE USERNAME & PASSWORD ||\n|| [5] LOGOUT                     ||\n|| [6] DELETE ACCOUNT             ||\n|| [7] QUIT                       ||"

create_table()
session = False
acc = Bank()

print("\n===============================")
print("========= SARIDI Bank =========")
print("===============================\n")
print("Hello, welcome to Saridi.Bank!")

while True:
    try:
        if not session:
            if haveAccount():
                acc.username = login()
                if isinstance(acc.username,str):
                    if acc.username.startswith("\nLOGIN FAILED:"):
                        print(acc.username)
                    else:
                        session = True
                        print(f"\n=-=-= WELCOME {acc.username} =-=-=")
                else:
                    print("\nINCORRECT USERNAME OR PASSWORD!")
            else:
                result = register()
                print(result)
        else:
            balance = acc.get_balance(acc.username)
            if balance is not None:
                print(f"\n|| {acc.username} Balance: Rp {balance:,} ||")
            else:
                print(f"\n|| {acc.username} Balance: Rp {balance} ||")
            print("\n====================================", end="")
            print(acc.info())
            print("====================================")
            try:
                choose = int(input("Choose [1-7]: "))
                match choose:
                    case 1:
                        print(acc.deposit(acc.username))
                    case 2:
                        print(acc.withdraw(acc.username))
                    case 3:
                        print(acc.transfer(acc.username))
                    case 4:
                        print("\n========================")
                        print("||[1] CHANGE USERNAME ||")
                        print("||[2] CHANGE PASSWORD ||")
                        print("========================")
                        try:
                            choose = int(input("Choose [1-2]: "))
                            match choose:
                                case 1:
                                    result = acc.change_username(acc.username)
                                    if isinstance(result, str):
                                        print(result)
                                    elif result[0] is True:
                                        acc.username = result[1]
                                        print("\nCHANGED USERNAME SUCCESSFULLY!")
                                case 2:
                                    result = acc.change_password(acc.username)
                                    if isinstance(result, str):
                                        print(f"\n{result}")
                                    elif result is True:
                                        print("\nCHANGED PASSWORD SUCCESSFULLY!")
                                case _:
                                    print("\nSorry, we did not have that feature.")
                                    print("Please choose around 1 until 2!")
                        except ValueError:
                            print("\nNUMBER ONLY OR DO NOT LEAVE IT BLANK!")
                    case 5:
                        x = (input("\nAre you sure you want to logout your account (yes/no)? ")).lower()
                        if x == "yes":
                            acc.username = ""
                            session = False
                    case 6:
                        x = acc.delete(acc.username)
                        if x[1]:
                            print(x[0])
                            session = False
                        elif x[1] is False:
                            print(x[0])
                    case 7:
                        x = (input("\nAre you sure want to quit this bank(yes/no): ")).lower()
                        if x == "yes":
                            print("\n==========================================")
                            print("==== THANK YOU FOR USING SARIDI.BANK! ====")
                            print("==========================================\n")
                            break
                    case _:
                        print("\nSorry, we did not have that feature.")
                        print("Please choose around 1 until 7!")
            except ValueError:
                print("\nNUMBER ONLY OR DO NOT LEAVE IT BLANK!")
    except KeyboardInterrupt:
        x = (input("\n\nAre you sure want to quit this bank(yes/no): ")).lower()
        if x == "yes":
            print("\n==========================================")
            print("==== THANK YOU FOR USING SARIDI.BANK! ====")
            print("==========================================\n")
            break