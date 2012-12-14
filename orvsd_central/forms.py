from flask.ext.wtf import Form, TextField, PasswordField, BooleanField
from flask.ext.wtf import Required, Email, EqualTo

class LoginForm(Form):
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])

class AddDistrict(Form):
    name = TextField('name', [Required()])
    shortname = TextField('shortname', [Required()])
    base_path = TextField('base_path', [Required()])

