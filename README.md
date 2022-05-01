# Example App Management scriptt 

This script contains examples for how to:
* create a dashboard page in Rally 
* add an app to a dashboard page and install html based on a github urls

### Usage

For all commands, you will be asked to enter your password for Rally.  

#### Create a new dashboard page (page will be created on the home tab): 

Run the command: 
```
python3 app.py create page  -u user@rallydev.com -n MyNewPageName
```

This command outputs a page oid which is needed to run the command to add apps to the page.  Output: 

```
MyNewPageName page created with oid: 634754493393.  Use the following command to add apps to this page: 

  python3 app.py create app -u username -p password -o 634754493393 -t apptitle -a appurl
```

#### Add an app to a custom page

Run the command: 

```
python3 app.py create app -u user@company.com -o <page_oid> -t MyAppTitle -a <url to app e.g. github raw url>
```
This command outputs a similiar message to the following if successful:

```
App installed successfully on page 634754399639 to panel 634755195361.  Make note of this information to make changes to configuration.```








