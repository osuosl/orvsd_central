from flask.ext.wtf import Form, TextField, PasswordField, BooleanField, SelectField
from flask.ext.wtf import Required, Email

class LoginForm(Form):
    username = TextField('username', [Required()])
    password = PasswordField('password', [Required()])

class AddUser(Form):
    user = TextField('user', [Required()])
    password = PasswordField('password', [Required()])
    confirm_pass = PasswordField('confirm_pass', [Required()])
    email = TextField('username', [Required(), Email()])
    perm = SelectField('perm', choices=[('steve', 'Steve'),
        ('helpdesk', 'Helpdesk'),('admin', 'Admin')])

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
