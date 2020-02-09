# web-deploy

A web GUI that assists with routine vCloud vApp deployments for DSU's Defensive Security Club.

## Pages

1. join
  - Allows users to join the default list
  - Takes a username and checks it against the list
  - Will run Org.getUser()
2. lists
  - Allows for the editing of userlists (removing/adding of users)
  - Allows for the creation of lists other than the main one (optional)
  - admin list
      - Allows admins to add more admins
      - Only needs to store ialab usernames
      - Will use vcloud.checkAuth()
3. task
  - Allows for creation of timed deploy tasks
  - Needs to choose a time, userlist and vapp
  - Will use Catalog.getTemplates() (validate template immediately)
