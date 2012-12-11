from flask.ext.wtf import Form, TextField, PasswordField, BooleanField
from flask.ext.wtf import Required, Email, EqualTo

class LoginForm(Form):
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])

#Things to add:
#   Register Form
#   Possibly invite form
