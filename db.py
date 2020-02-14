from flask_login import UserMixin
from vcloud import vcloud
import sqlite3 as sql
import configparser
from multiprocessing import Pool
import json

db = "web-deploy.db"

####################
# DATA MODEL CLASS #
# OHHHHH YEAHHHHHH #
####################

class User(UserMixin):
    def __init__(self, uid, username):
        self.uid = uid
        self.username = username

    def get_id(self):
        return chr(self.uid)


class DataModel(object):

    def __init__(self, config):
        super().__init__()
        self.config = config

    def load(self):
        self.admins = get_admins()

    def load_vcloud(self):
        print("[VCLOUD] Authenticating...")
        self.vcloud = vcloud.vcloud(self.config)

        print("[VCLOUD] Retrieving Org...")
        self.org = self.vcloud.getOrg(self.config['Main']['Org'])
        print("[VCLOUD] Retrieving Catalog...")
        self.catalog = self.vcloud.getCatalog(self.config['Main']['Catalog'])
        print("[VCLOUD] Retrieving VDC...")
        self.vdc = self.vcloud.getVdc(self.config['Main']['Vdc'])
        print("[VCLOUD] Retrieving Role...")
        self.role = self.org.getRole(self.config['Main']['Role'])

        if 'Proc_Count' in self.config['Web-Deploy']:
            self.proc_count = int(self.config['Web-Deploy']['Proc_Count'])
        else:
            self.proc_count = 8

    def auth_user(self, username, password):
        return self.vcloud.checkAuth(username, password)

    def check_user(self, username):
        if self.org.getUser(username) is None:
            return False
        else:
            return True

    def check_vapp(self, vapp_name):
        templates = self.catalog.getTemplates(filter=vapp_name)
        if not templates:
            return False
        else:
            return True

    def deployall(self, usernames, vapp_name):
        templates = self.catalog.getTemplates(vapp_name)
        if templates is not None:
            template = templates[0]
        else:
            print("[ERROR] vApp", vapp_name, "not found, dying...")
            return(1)
        
        resolved_users = []
        for username in usernames:
            resolved_users.append(self.org.getUser(username))

        deploy_tups = []
        for user in resolved_users:
            deploy_tups.append((user, template))

        p = Pool(self.proc_count)
        p.map(self.deployone, deploy_tups)
        p.close()

    def deployone(self, deploy_tup):
        user = deploy_tup[0]
        template = deploy_tup[1]
        if user is None:
            return
        vapp = template.deploy(self.vdc,name=user.name+'_'+template.name)
        if vapp is None:
            return
        endvapp = vapp.changeOwner(user, timeout=300, checkTime=5)
        if endvapp is not None:
            print(f"[INFO] {user.name}_{template.name} deployed successfully deployed to {user.name}")


#############################
# HUGE LIST OF DB FUNCTIONS #
# IT'S SO OOP(tm) IT HURTS  #
#############################

def execute(cmd, values=None, one=None):
    with sql.connect(db) as conn:
        cur = conn.cursor()
        if values:
            cur.execute(cmd, values)
        else:
            cur.execute(cmd)
        if one:
            return cur.fetchone()
        return cur.fetchall()

def get_default():
    config_name = "web-deploy.conf"
    config = configparser.ConfigParser()
    config.read(config_name)
    return(config['Web-Deploy']['Default_list'])

def drop_list(list_name):
    print("[INFO] Removing list", list_name)
    execute("DELETE FROM `lists` WHERE list_name=?", (list_name,))

def create_list(list_name):
    print("[INFO] Creating list", list_name)
    add_list(list_name, "_PLACEHOLDER_")

def add_list(list_name, username):
    print("[INFO] Adding username", username, "to the list", list_name)
    execute("INSERT INTO `lists` ('list_name', 'username') VALUES (?, ?)", (list_name, username))

def delete_list(list_name, username):
    print("[INFO] Removing username", username, "from the list", list_name)
    execute("DELETE FROM `lists` WHERE list_name=? and username=?", (list_name, username))

def get_lists(list_default):
    lists = {}
    list_data = execute("SELECT list_name, username FROM lists")
    for list_item in list_data:
        if list_item[0] in lists:
            lists[list_item[0]].append(list_item[1])
        else:
            lists[list_item[0]] = [list_item[1]]
    if list_default not in lists:
        lists[list_default] = []
    return lists

def get_list(list_name):
    try:
        list_data = execute("SELECT username FROM lists WHERE list_name=?", (list_name,))
        list_data_formatted = []
        for list_item in list_data:
            if list_item[0] != "_PLACEHOLDER_":
                list_data_formatted.append(list_item[0])
        list_data = list_data_formatted
    except:
        list_data = None
    return list_data

def add_task(time, task_type, name, option):
    print("[INFO] Adding task: ", name)
    execute("INSERT INTO `tasks` ('time', 'type', 'name', 'option', 'ran') VALUES (?, ?, ?, ?, ?)", (time, task_type, name, option, False))

def get_top_task():
    tasks_data = execute("SELECT time, type, name, option, ran FROM tasks where ran=0 ORDER BY time")
    if len(tasks_data) > 0:
        return tasks_data[0]
    else:
        return []

def expire_task(name):
    print("[INFO] Expiring task: ", name)
    execute("UPDATE tasks set ran=2 where name=?", (name,))

def setran_task(name):
    print("[INFO] Set running on task: ", name)
    execute("UPDATE tasks set ran=1 where name=?", (name,))

def get_tasks():
    tasks = execute("SELECT time, type, name, option, ran FROM tasks ORDER BY time")
    for i, task in enumerate(tasks):
        tasks[i] = (task[0], task[1], task[2], json.loads(task[3]), task[4])
    return tasks
    
def edit_task(time, task_type, task_name, option):
    print("[INFO] Updating task info for", task_name)
    execute("UPDATE `tasks` SET 'time'=?, 'type'=?, 'option'=? WHERE name=?", (time, task_type, option, task_name))

def delete_task(task_name):
    print("[INFO] Removing task", task_name)
    execute("DELETE FROM `tasks` WHERE name=?", (task_name,))

def get_admins():
    users = {}
    for uid, username in execute("SELECT id, username FROM lists WHERE list_name='admins'"):
        users[uid] = User(uid, username)
    return users

def get_admin(username):
    uid = execute("SELECT id FROM lists WHERE list_name='admins' and username=?",(username,))
    return uid[0][0]

def reset():
    print("[INFO] Resetting database...")
    execute("DROP TABLE IF EXISTS `lists`;")
    execute("""CREATE TABLE `lists` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `list_name` VARCHAR(255),
                `username` VARCHAR(255)
            );""")
    execute("DROP TABLE IF EXISTS `tasks`;")
    execute("""CREATE TABLE `tasks` (
                `time` DATETIME,
                `type` INTEGER,
                `name` VARCHAR(255),
                `option` VARCHAR(255),
                `ran` BOOL
            );""")
            
