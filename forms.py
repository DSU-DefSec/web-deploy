from flask_wtf import FlaskForm
from wtforms import *
from wtforms.fields.html5 import DateTimeField
from wtforms.validators import *
import bcrypt
import flask_login
import db
from json import dumps
from datetime import datetime, timedelta

class LoginForm(FlaskForm):
    username = StringField('IALab Username', validators=[InputRequired()])
    password = PasswordField('IALab Password', validators=[InputRequired()])

    def __init__(self, dm):
        super().__init__()
        self.dm = dm
        self.admins = dm.admins

    def validate(self):
        if not super(LoginForm, self).validate():
            return False
        for admin in self.admins.values():
            if self.username.data == admin.username:
                return self.dm.auth_user(self.username.data, self.password.data)
        return False


class JoinForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])

    def __init__(self, dm, list_name):
        super().__init__()
        self.dm = dm
        self.list_name = list_name

    def validate(self):
        #this should prob be done using regexes at some point
        # if it aint broke...
        for c in self.username.data:
            if c != "." and not c.isalnum():
                return False

        if not self.dm.check_user(self.username.data):
            return False

        db.add_list(self.list_name, self.username.data)
        return True

class DeployForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    vapp = StringField('vApp Template', validators=[InputRequired()])
    deploy_time = DateTimeField('Deployment Time', default=datetime.now, validators=[InputRequired()])
    deploy_list = SelectField('List', choices=[], validators=[InputRequired()], default=db.get_default())

    def __init__(self, dm):
        super().__init__()
        lists = db.get_lists(db.get_default())
        deploy_choices = []
        for list_name in lists.keys():
            deploy_choices.append((list_name, list_name))
        self.deploy_list.choices = deploy_choices
        # self.deploy_time.default = datetime.now()
        # self.deploy_list.process()
        self.dm = dm

    def parse_data(self):
        error = None
        for c in self.name.data:
            if c != "_" and c != " " and not c.isalnum():
                error = "Task name validation failed. Only a-zA-Z_ allowed."
                return (error, False)

        for c in self.vapp.data:
            if c != "_" and c != " " and c != "." and c != "-" and not c.isalnum():
                error = "vApp name validation failed. Only a-zA-Z_-. allowed."
                return (error, False)

        if not self.dm.check_vapp(self.vapp.data):
            error = "vApp template validation failed. Did you type the template name correctly?"
            return (error, False)

        if  self.deploy_time.data < datetime.now() - timedelta(minutes=5):
            error = "Datetime verification failed."
            return (error, False)

        return (error, True)

    def validate(self):
        print("[DEPLOY] Deploy request intitiated...")
        return self.parse_data()

    def add_valid_task(self):
        error = None
        for task in db.get_tasks():
            if self.name.data == task[2]:
                error = "Deploying task failed, already in database."
                return error
        options = dumps({'vapp_name': self.vapp.data, 'list': self.deploy_list.data})
        db.add_task(self.deploy_time.data, 0, self.name.data, options)
        return error

    def edit_valid_task(self):
        error = None
        options = dumps({'vapp_name': self.vapp.data, 'list': self.deploy_list.data})
        db.edit_task(self.deploy_time.data, 0, self.name.data, options)
        return error
