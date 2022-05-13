# Example App Management scriptt 

This script contains examples for how to:
* create a dashboard page in Rally 
* add an app to a dashboard page and install html based on a github urls
* configure the app 

### Usage

```
python3 app.py -c config_file.yaml 
```

#### Pre-requisites

1.  Rally username/password
2.  Raw url to an app to install
3.  Settings names for configurations in app

#### Configuration file 
Create a yaml configuration file for your dashboard that has the following structure:
```
connection:
  host: https://rally1.rallydev.com
  password: null
  user: user@company.com
page:
  layout: SINGLE
  oid: 0
  title: My Page Title
apps:
- configs:
  - name: html
    value: there are {x} stories about Fred!
  - name: countVariables
    value:
    - artifactType: HierarchicalRequirement
      id: x
      query: (Name contains \"Fred\")
  oid: 0
  raw_url: https://raw.githubusercontent.com/RallyCommunity/query-counter/master/deploy/Ugly.txt
  title: Stories about Fred

```
##### connection
* host - rally url host name
* user - username to create the dashboard with 
* password (optional) - password for user above.  If not indicated in the file, then you will be prompted when you run the script

##### page
* layout - page layout for the dashboard - options are:  SINGLE, ...
* oid - if the page you want to add/modify apps exists already, then add that oid here.  If you are creating a new page, this should be 0
* title - Title of the dashboard page that is being created.  If the page already exists, the title will NOT be updated

**TODO**
* add option for timebox scoped dashboard  
* add option for moving apps in layout
* add option for sharing across projects

##### apps (array)
represents an array of apps, so you can add more than app
For each app:
* oid - if the app already exists on the page, then add the oid here.  If you are adding a new app to the page, this should be 0
* title - title for the app.  If the app already exists, the title will NOT be updated 
* raw_url - url to the raw code on github (assuming it is publically available)
* configs - (array) configurations for the app

###### configs (array)
* name - setting name from the app code 
* value - setting value that you wish to set.  If value is an object, then this can be structured as an object  

NOTE: All configurations will be scoped to the app and saved as app preferences not scoped to a particular user, project or workspace







