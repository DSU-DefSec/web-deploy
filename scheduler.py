from multiprocessing import Process
import db
import time
from datetime import datetime, timedelta
from json import loads

class Scheduler:

    def __init__(self, dm):
        self.dm = dm

    def start(self):
        self.p = Process(target=self.cycle)
        self.p.start()

    def cycle(self):
        while(True):
            time.sleep(10)
            now_time = datetime.now()
            task = db.get_top_task()
            if len(task) > 0:

                task_date = datetime.strptime(task[0], '%Y-%m-%d %H:%M:%S')
                task_name = task[2]
                task_options = task[3]

                if now_time > task_date:
                    if now_time > task_date + timedelta(hours=1):
                        db.delete_task(task_name)
                    else:
                        if task[1] == 0:
                            print("[INFO] Running task: ", task_name)
                            db.setran_task(task_name)
                            self.deploy(task_options)
                        
    def stop(self):
        pass

    def deploy(self, json_options):
        option_dict = loads(json_options)
        usernames = db.get_list(option_dict['list'])
        vapp_name = option_dict['vapp_name']
        if usernames is None or usernames == []:
            print(f"[ERROR] No users in list {option_dict['list']}, dying...")
            return 1
        self.dm.deployall(usernames, vapp_name)
        

