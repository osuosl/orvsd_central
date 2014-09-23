# Defines functions for validating database inputs are unique/valid

# Justin Brown speaks "I wrote this to make init_db
# a bit cleaner."

import re

from orvsd_central.models import User
from orvsd_central.constants import USER_PERMS

from getpass import getpass

__all__ = [
'get_valid_username',
'get_valid_email',
'get_matching_passwords',
]

def is_valid_string(string):
    """
    Check that `string` is a string, and not empty.
    """
    if not isinstance(string, str):
        print "input should be a string."
        return False
    if not len(string):
        print "Input string should not be empty."
        return False

    return True

# -- - -- - -- - -- - -- - -- - -- - -- -
# USERNAME
# -- - -- - -- - -- - -- - -- - -- - -- -

def is_valid_username(username):
    """
    Check that `username` is a string, and not empty.
    """
    return is_valid_string(username)
    # Room to add more.

def is_unique_username(username):
    """
    Check that `username` is valid, and unique.
    """
    unique = None == User.query.filter_by(name=username).first()
    if not unique:
        print "Username is taken."
        return False
    return True

def get_valid_username():
    """
    Prompts for a valid username that does not already exist
    in the database.

    Returns: a valid and unique username.
    """
    valid = False
    while not valid:
        username = raw_input("Username: ")

        # lets check valid before using in query
        valid = is_valid_username(username) and \
                is_unique_username(username)

    return username

# -- - -- - -- - -- - -- - -- - -- - -- -
# E-MAIL
# -- - -- - -- - -- - -- - -- - -- - -- -

def is_valid_email(email):
    """
    Check that `email` is a string, not empty, and looks like an e-mail.
    """
    if not is_valid_string(email):
        return False

    if not re.match(
        '^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$',
        email,
    ):
        print "Input string does not look like an e-mail address."
        return False

    return True

def is_unique_email(email):
    """
    Check that `email` is valid, and unique.
    """
    unique = None == User.query.filter_by(email=email).first()
    if not unique:
        print "Username is taken."
        return False
    return True

def get_valid_email():
    """
    Prompts for an email that does not already exist
    in the database.

    Returns: a valid and unique email.
    """
    valid = False
    while not valid:
        email = raw_input("E-mail: ")

        # lets check valid before using in query
        valid = is_valid_email(email) and \
                is_unique_email(email)

    return email

# -- - -- - -- - -- - -- - -- - -- - -- -
# MATCHING PASSWORDS
# -- - -- - -- - -- - -- - -- - -- - -- -

def is_valid_password(passwd):
    """
    Check that `passwd` is a string, and not empty.
    """
    return is_valid_string(passwd)
    # Room to add more.

def get_matching_passwords():
    """
    Returns valid matching passwords from the prompt.
    """
    matching = valid = False
    while not matching or not valid:
        passwd = getpass("Password: ")
        valid = is_valid_password(passwd)
        confirm = getpass("Confirm: ")
        matching = passwd == confirm
        if not matching:
            print "Passwords do not match. Please try again."

    return passwd
