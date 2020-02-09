from flask_login import UserMixin
import sqlite3 as sql
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
    def load(self):
        #self.lists = load_lists()
        self.admins = get_admins()
            
    def load_vcloud(self):
        pass
    """ 
        cutshaw here's a class for your vcloud garbage
        so you dont have to init it each time you run the function
        - init vcloud
        - store object in dm.vcloud or something
        
    """
    
    def auth_user(self, username, password):
        """ 
        MICHAEL CUTSHAW MAGIC VCLOUD AUTH CODE HERE
        use dm.vcloud
        return True if valid username/pw combo
        """
        return True
        
    def check_user(self, username):
        """ 
        MICHAEL CUTSHAW MAGIC VCLOUD CODE HERE
        use dm.vcloud
        return True if valid user
        """
        return True


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
    
def get_admins():
    users = {}
    for uid, username in execute("SELECT id, username FROM lists WHERE list_name='admins'"):
        users[uid] = User(uid, username)
    return users

def get_admin(username):
    uid = execute("SELECT id FROM lists WHERE list_name='admins' and username=?",(username,))
    return uid

    
def reset():
    print("[INFO] Resetting database.")
    execute("DROP TABLE IF EXISTS `lists`;")
    execute("""CREATE TABLE `lists` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `list_name` VARCHAR(255),
                `username` VARCHAR(255)
            );""")
    execute("DROP TABLE IF EXISTS `tasks`;")
    execute("""CREATE TABLE `tasks` (
                `time` DATETIME DEFAULT CURRENT_TIMESTAMP,
                `type` INTEGER,
                `name` VARCHAR(255),
                `option` VARCHAR(255),
                `ran` BOOL
            );""")
            
