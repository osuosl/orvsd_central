from flask.ext.wtf import (DateTimeField, Email, Form, PasswordField, Required,
                           SelectField, SelectMultipleField, TextField)

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


class DistrictForm(Form):
    """
    Properties needed for a user to create a new District object
    """

    name = TextField(u"Name", validators=[Required()])
    # We may want to have the Model autogen the shortname on __init__
    shortname = TextField(u"Short Name", validators=[Required()])
    base_path = TextField(u"Base Path")
    state_id = SelectField(
        u"Associated State", validators=[Required()], choices=defaults
    )

class SchoolForm(Form):
    """
    Properties needed for a user to create a new School object
    """

    name = TextField(u"Name", validators=[Required()])
    # We may want to have the Model autogen the shortname on __init__
    shortname = TextField(u"Short Name", validators=[Required()])
    domain = TextField(u"Domain", validators=[Required()])
    license = SelectField(
        u"License",
        validators=[Required()],
        # This should be pulled out and possibly be managed through the config
        # hardcoding is never OK.
        choices=[('None', '---'), ('FLVS', 'FLVS'), ('NROC', 'NROC')],
    )
    county = TextField(u"County", validators=[Required()])
    state_id = SelectField(
        u"Associated State", validators=[Required()], choices=defaults
    )


class SiteForm(Form):
    """
    Properties needed for a user to create a new Site object
    """

    name = TextField(u"Name", validators=[Required()])
    baseurl = TextField(u"URL", validators=[Required()])
    basepath = TextField(u"Base Path")
    cron = DateTimeField(u"Jenkins Cron Job")
    location = TextField(u"Host Machine")
    # may want to have the token field be disabled?
    tokens = TextField(u"Moodle Tokens", default="{}")
    school_id = SelectField(
        u"Associated School", validators=[Required()], choices=defaults
    )


class CourseForm(Form):
    """
    Properties needed for a user to create a new District object
    """

    name = TextField(u"Name", validators=[Required()])
    shortname = TextField(u"Short Name", validators=[Required()])
    source = TextField(u"Source")
    version = TextField(u"Version")
    filename = TextField(u"Filename", validators=[Required()])
    license = SelectField(
        u"School License",
        validators=[Required()],
        # This should be pulled out and possibly be managed through the config
        # hardcoding is never OK.
        choices=[('None', '---'), ('FLVS', 'FLVS'), ('NROC', 'NROC')],
    )
    moodle_version = SelectField(
        u"Moodle Version",
        choices=[('Any', 'Any'), ('2.7', 2.7), ('2.5', 2.5), ('2.2', 2.2)],
    )
    serial = TextField(u"Serial", validators=[Required()])
    state_id = SelectField(
        u"Associated State", validators=[Required()], choices=defaults
    )

