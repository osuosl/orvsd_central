# Defines functions for validating/getting email which is unique and valid

import re

from orvsd_central.models import User

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

def is_unique_email(email):
    """
    Check that `email` is valid, and unique.
    """
    return None == User.query.filter_by(email=email).first()

def get_valid_email():
    """
    Prompts for an email that does not already exist
    in the database.

    Returns: a valid and unique email.
    """
    valid, unique = (False, False)
    while not (valid and unique):
        email = raw_input("E-mail: ")

        # lets check valid before using in query
        valid = is_valid_email(email)
        if not valid:
            print("E-mail appears to be invalid.")
            continue # skip query
        unique = is_unique_email(email)
        if not unique:
            print("E-mail is taken.")

    return email

