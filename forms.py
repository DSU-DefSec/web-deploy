from flask_wtf import FlaskForm
from wtforms import *
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

        list_data = db.get_list(self.list_name)
        for user in list_data:
            if user == self.username.data:
                return False
            
        db.add_list(self.list_name, self.username.data)
        return True

        
class TaskForm(FlaskForm):
    vapp = StringField('vApp', validators=[InputRequired()])
    list_name = StringField('List Name', validators=[InputRequired()])
    cmd = StringField('Command', validators=[InputRequired()])


    def __init__(self, dm):
        super().__init__()
        self.dm = dm

    def validate(self):
        if not super(JoinForm, self).validate():
            return False
            
        # taskform yayeeet
        return True

