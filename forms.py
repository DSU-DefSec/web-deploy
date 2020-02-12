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
        for c in self.username.data:
            if not c == "." and not c.isalnum():
                return False

        if not self.dm.check_user(self.username.data):
            return False

        db.add_list(self.list_name, self.username.data)
        return True

class DeployForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    vapp = StringField('vApp Template', validators=[InputRequired()])
    deploy_time = DateTimeField('Deployment Time', default=datetime.now(), validators=[InputRequired()])
    lists = db.get_lists(db.get_default())
    deploy_choices = []
    for list_name in lists.keys():
        deploy_choices.append((list_name, list_name))
    deploy_list = SelectField('List', choices=deploy_choices, validators=[InputRequired()], default=db.get_default())

    def __init__(self, dm):
        super().__init__()
        self.dm = dm

    def validate(self):
        for c in self.name.data:
            if not c == "_" and not c == " " and not c.isalnum():
                return False
        
        for c in self.vapp.data:
            if not c == "_" and not c == " " and not c.isalnum():
                return False

        if not self.dm.check_vapp(self.vapp.data):
            return False

        for task in db.get_tasks():
            if self.name.data == task[2]:
                return False
        if  self.deploy_time.data < datetime.now() - timedelta(minutes=5):
            return False

        options = dumps({'vapp_name':self.vapp.data, 'list':self.deploy_list.data})
        db.add_task(self.deploy_time.data, 0, self.name.data, options )
        # taskform yayeeet
        return True
