from flask.ext.wtf import Form, TextField, PasswordField, BooleanField
from flask.ext.wtf import Required, Email, EqualTo

class LoginForm(Form):
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])

class AddDistrict(Form):
    name = TextField('name', [Required()])
    shortname = TextField('shortname', [Required()])
    base_path = TextField('base_path', [Required()])

class AddSchool(Form):
    district_id = TextField('district_id', [Required()])
    name = TextField('name', [Required()])
    shortname = TextField('shortname', [Required()])
    domain = TextField('domain', [Required()])
    license = TextField('license', [Required()])
