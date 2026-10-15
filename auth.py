from bcrypt import checkpw
from getpass import getpass
from database import add_user, verification
from config import USERNAME_MAX_LENGTH, PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MAX_BYTES

def validation_format(name, password):
    if not isinstance(name, str):
        return "ENTER CHARACTERS ONLY!"
    if not isinstance(password, str):
        return "ENTER CHARACTERS ONLY!"
    name_length = len(name)
    password_length = len(password)
    if name_length == 0 or password_length == 0:
        return "Do not leave PASSWORD or USERNAME BLANK!"
    elif name_length > USERNAME_MAX_LENGTH:
        return f"Your USERNAME is too LONG (Maximum {USERNAME_MAX_LENGTH} Characters)!"
    elif password_length < PASSWORD_MIN_LENGTH:
        return f"Your PASSWORD is too SHORT (Minimum {PASSWORD_MIN_LENGTH} Characters)!"
    elif password_length > PASSWORD_MAX_LENGTH:
        return f"Your PASSWORD is too LONG (Maximum {PASSWORD_MAX_LENGTH} Characters)!"
    elif not name.isalnum():
        return "SYMBOLS are not ALLOWED!"
    return True

def validation(name, password):
    if not isinstance(name, str) or not isinstance(password, str):
        return "ENTER CHARACTERS ONLY!"
    bytes_password = password.encode("utf-8")
    if len(bytes_password) > PASSWORD_MAX_BYTES:
        return f"PASSWORD TOO LONG! PLEASE USE A SHORTER PASSWORD."
    hashed_password = verification(name)
    if hashed_password is None:
        return "UNKNOWN USERNAME!"
    if not isinstance(hashed_password, str):
        return "SAVED PASSWORD ERROR IN STORAGE!"
    try:
        if checkpw(bytes_password, hashed_password.encode("utf-8")) is True:
            return True
    except ValueError:
        return "SAVED PASSWORD ERROR IN STORAGE!"
    else:
        return "WRONG PASSWORD!"

def haveAccount():
    while True:
        x = input("\nDo you have account or not (yes/no): ")
        if x.lower() == "yes":
            return True
        elif x.lower() == "no":
            return False
        print("\nPlease enter APPROPRIATE ANSWER!")

def login():
    name = input("\nYour username: ")
    password = getpass("Password: ")
    valid = validation_format(name, password)
    if isinstance(valid, str):
        return f"\nLOGIN FAILED: {valid}"
    check = validation(name, password)
    if check is True:
        return name
    else:
        return f"\nLOGIN FAILED: {check}"

def register():
    name = input("\nYour username: ")
    password = getpass("Password: ")
    valid = validation_format(name, password)
    if isinstance(valid, str):
        return f"\nREGISTRATION FAILED: {valid}"
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > PASSWORD_MAX_BYTES:
        return "PASSWORD TOO LONG! PLEASE USE A SHORTER PASSWORD."
    result = add_user(name, password)
    if result is True:
        return f"\nREGISTRATION SUCCESSFUL: Account {name} has been SUCCESSFULLY REGISTERED!"
    else:
        return f"\nREGISTRATION FAILED: {result}"


if __name__ == "__main__":
    """=== MAINTENANCE MODE ==="""
    
    # TESTING AUTH.PY FROM SCRATCH!
    # haveAccount()

    # MANUALLY ADDING A NEW ACCOUNT:
    # print(f"Status: {register()}")

    # TESTING WHETHER THE ACCOUNT CAN LOG IN OR NOT:
    # print(f"Status: {login()}")

    # TESTING WHETHER THE FORMAT VALIDATION SYSTEM WORKS OR NOT:
    # print(f"Status: {validation_format("admin", "admin1234")}")

    # CHECK WHETHER THE USERNAME AND PASSWORD ARE CORRECT, INCORRECT, OR MISSING:
    # print(f"Status: {validation("admin", "admin1234")}")