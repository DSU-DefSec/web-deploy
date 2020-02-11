from flask_wtf import FlaskForm
from wtforms import *
frpm wtforms.fields.html5 import DateField
from wtforms.validators import *
import bcrypt
import flask_login
import db

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
    deploy_time = DateField('Deployment Time', validators=[InputRequired()])
    lists = db.get_lists(db.get_default())
    deploy_choices = []
    for list_name in lists.keys():
        deploy_choices.append((list_name, list_name))
    deploy_list = SelectField('List', choices=deploy_choices, validators=[InputRequired()])

    def __init__(self, dm):
        super().__init__()
        self.dm = dm

    def validate(self):
        if not super(JoinForm, self).validate():
            return False
            
        # taskform yayeeet
        return True

