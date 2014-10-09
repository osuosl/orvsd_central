import re

from getpass import getpass

def is_valid_email(email):
    """
    Check that `email` is not empty and looks like an e-mail.
    """
    if not email:
        return False

    if not re.match(
        '^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$',
        email,
    ):
        return False

    return True

def prompt_valid_email():
    """
    Prompts for an email that does not already exist
    in the database.

    Returns: a valid and unique email.
    """
    email = raw_input("E-mail: ")
    while not is_valid_email(email):
        print("E-mail appears to be invalid.")
        email = raw_input("E-mail: ")

    return email

def prompt_valid_username():
    """
    Prompts for a valid username
    Returns: string : a valid username.
    """
    username = raw_input("Username: ")
    while not username:
        print("Please enter a username.")
        username = raw_input("Username: ")

    return username

def prompt_matching_passwords():
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
