# Defines functions for validating users as unique/valid 

from orvsd_central.models import User

def is_unique_username(username):
    """
    Check that `username` is valid, and unique.
    """
    return None == User.query.filter_by(name=username).first()

def get_valid_username():
    """
    Prompts for a valid username that does not already exist
    in the database.

    Returns: a valid and unique username.
    """
    unique = False
    while not unique:
        username = raw_input("Username: ")

        # check valid before using in query
        if not username:
            print("Please enter a username.")
            continue # skip query

        unique = is_unique_username(username)
        if not unique:
            print("Username is taken.")

    return username

