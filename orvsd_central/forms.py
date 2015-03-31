from flask.ext.wtf import (Form, TextField, PasswordField, SelectField,
                           SelectMultipleField, Required, Email)

defaults = [('None', '---')]

class LoginForm(Form):
    """
    Login form.
    """
    name = TextField('name', [Required()])
    password = PasswordField('password', [Required()])


class AddUser(Form):
    """
    Registration/Add User form.
    """
    user = TextField('user', [Required()])
    password = PasswordField('password', [Required()])
    confirm_pass = PasswordField('confirm_pass', [Required()])
    email = TextField('username', [Required(), Email()])
    role = SelectField('role', choices=[('viewonly', 'View Only'),
                                        ('helpdesk', 'Helpdesk'),
                                        ('admin', 'Admin')])


class InstallCourse(Form):
    """
    Form for installing course(s) to site(s).
    """
    site = SelectMultipleField('Site', choices=defaults)
    course = SelectMultipleField('Course', choices=defaults)
    filter = SelectField('Filter', choices=defaults)
