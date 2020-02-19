#!/usr/bin/python3

from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask import Flask, render_template, request, redirect, url_for
from urllib.parse import urlparse, urljoin
from scheduler import Scheduler
from forms import *
from json import loads, dumps
import configparser
import flask
import sys
import db

config_name = "web-deploy.conf"
config = configparser.ConfigParser()
config.read(config_name)

app = Flask(__name__)
app.secret_key = config['Web-Deploy']['Secret']
login_manager = LoginManager()
login_manager.init_app(app)

list_default =  config['Web-Deploy']['Default_List']
dm = db.DataModel(config)
print("[INFO] Loading vcloud object...")
dm.load_vcloud()

@login_manager.user_loader
def load_user(uid):
    dm.load()
    uid = int(ord(uid))
    if uid in dm.admins:
        return dm.admins[uid]
    return None

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(flask.url_for('login'))

def is_safe_url(target):
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

@app.route('/login', methods=['GET', 'POST'])
def login():
    dm.load()
    form = LoginForm(dm)
    error = None
    if request.method == 'POST':
        if form.validate_on_submit():
            uid = db.get_admin(form.username.data)
            user = load_user(chr(uid))
            login_user(user)
            flask.flash('Logged in successfully!')
            next = flask.request.args.get('next')
            if not is_safe_url(next):
                return flask.abort(400)
            return redirect(next or flask.url_for('join'))
        else:
            error = "Sorry, that's not gonna work."
    return render_template('login.html', form=form, error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(flask.url_for('join'))

@app.route('/')
@app.route('/join', methods=['GET', 'POST'])
def join():
    """
      - Allows users to join the default list
      - Takes a username and checks it against the list
      - Will run Org.getUser()
    """
    form = JoinForm(dm, list_default)
    error = None
    if request.method == 'POST':
        if "username" in request.form:
            list_data = db.get_list(list_default)
            for user in list_data:
                if user == request.form["username"]:
                    error = "Error! User is already on list."
                    return render_template('join.html', form=form, error=error)
            if form.validate_on_submit():
                flask.flash("User added to list!")
            else:
                error = "Error! User is invalid."

    return render_template('join.html', form=form, error=error)

@app.route('/lists', methods=['GET', 'POST'])
@login_required
def lists():
    """
      - Allows for the editing of userlists (removing/adding of users)
      - Allows for the creation of lists other than the main one
      - Allows for adding, removing, and exporting lists and users
    """
    error = None
    list_data = None
    list_selected = list_default

    # If POST, Add, Delete, Export
    if request.method == 'POST':
        if "list_name" in request.form:
            list_selected = request.form["list_name"]
            if "action" in request.form:
                action = request.form["action"]

                # Adding user or list
                if action == "Add":
                    if "username" in request.form:
                        form = JoinForm(dm, list_selected)
                        if form.validate_on_submit():
                            flask.flash("User added to " + list_selected + "!")
                        else:
                            error = "Error! User is invalid or already on list."
                    else:
                        db.create_list(list_selected)
                        flask.flash("List " + list_selected + " added!")

                # Deleting user or list
                elif action == "Delete":
                    if "username" in request.form:
                        db.delete_list(list_selected, request.form["username"])
                        flask.flash(request.form["username"] + " removed from " +  list_selected + "!")
                    else:
                        if list_selected == list_default:
                            error = "Sorry, you can't remove the default list."
                        else:
                            db.drop_list(list_selected)
                            flask.flash("Dropped list " + list_selected + "!")
                            list_selected = list_default

                # Export list as plaintext
                elif action == "Export":
                    list_data = db.get_list(list_selected)
                    list_string = '<br>'.join(list_data)
                    return(list_string)
            list_data = db.get_list(list_selected)
        else:
            error = "You need to supply a list if you're going to POST this page."

    # If GET, display a list
    else:
        if "list" in request.args:
            list_selected = request.args["list"]
        list_data = db.get_list(list_selected)

    # Grab default list if list_data is None
    if list_data == None:
        error = "The specified list doesn't exist."
        list_selected = list_default
        list_data = db.get_list(list_selected)

    lists = db.get_lists(list_default)
    form = JoinForm(dm, list_selected)

    return render_template('lists.html', form=form, error=error, list_name=list_selected, list_data=list_data, lists=lists)

@app.route('/deploy', methods=['GET', 'POST'])
@login_required
def deploy():
    """
      - Allows for creation of timed deploy tasks
      - Needs to choose a time, userlist and vapp
      - Will use Catalog.getTemplates() (validate template immediately)

    """
    form = DeployForm(dm)
    error = None
    task_name = "Create a new task..."
    task_selected = ("", "", "", ("", ""), "")
    error = None

    # If POST, Add, Edit, or Delete
    if request.method == 'POST':
        if "action" in request.form:
            action = request.form["action"]
            (error, result) = form.validate_on_submit()
            if "name" in request.form and "vapp" in request.form:
                task_selected = ("", "", request.form["name"], {"vapp_name": request.form["vapp"]}, "")
            if result and action == "Add":
                error = form.add_valid_task()
                if not error:
                    task_name = request.form["name"]
                    flask.flash("Task " + task_name + " added!")
            elif result and action == "Update":
                error = form.edit_valid_task()
                if not error:
                    task_name = request.form["name"]
                    flask.flash("Task " + task_name + " edited!")
            elif action == "Delete":
                if "name" in request.form:
                    error = db.delete_task(request.form["name"])
                    if not error:
                        flask.flash("Task deleted!")

    # Grab updated task list after possible post
    tasks = db.get_tasks()
    task_queue, task_history = [], []
    for task in tasks:
        if task[4] == 0:
            task_queue.append(task)
        else:
            if len(task_history) <= 5:
                task_history.append(task)
            else:
                db.delete_task(task[2])

    # If get, either display task requested or new deploy form
    if "task" in request.args or task_name != "Create a new task...":
        if "task" in request.args:
            task_name = request.args["task"]
        for task in tasks:
            if task_name == task[2]:
                task_selected = task
        if task_selected[0] == "":
            task_name = "Create a new task..."
            error = "Sorry, specified task does not exist."

    return render_template('deploy.html', form=form, task_queue=task_queue, task_history = task_history, task_name=task_name, task_selected=task_selected, error=error)

@app.route('/renew', methods=['GET', 'POST'])
@login_required
def renew():
    """
      - Allows for renewal of leases every X minutes
      - Needs to choose a time, renewal period, userlist and vapp

    """
    return "todo"

if __name__ == '__main__':

    # Reset/recreate DB with ./app.py nuke
    if "nuke" in sys.argv:
        db.reset()
        db.add_list("admins", config['Web-Deploy']['Init_Admin'])

    # start scheduler
    s = Scheduler(dm)
    s.start()

    app.run()
