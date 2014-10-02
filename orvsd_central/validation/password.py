# Defines functions for validating/getting user inputs which are unique + valid

from getpass import getpass

def is_valid_password(passwd):
    """
    Check that `passwd` is not empty.
    """
    return is_valid_string(passwd)
    # Room to add more.

def get_matching_passwords():
    """
    Returns valid matching passwords from the prompt.
    """
    matching = False
    while not matching:
        passwd = getpass("Password: ")
        if not passwd:
            print("Please enter a password.")
            continue

        confirm = getpass("Confirm: ")
        matching = passwd == confirm
        if not matching:
            print("Passwords do not match. Please try again.")

    return passwd
