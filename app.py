#!/usr/bin/env python
import sys
import argparse
import os
import re
from psutil import NIC_DUPLEX_HALF
import requests
import json 
from urllib import parse
from requests.auth import HTTPBasicAuth
import getpass


uri_host = 'https://rally1.rallydev.com'

uri_make_page = '{0}/slm/wt/edit/create.sp?cpoid=729766&key={1}'
uri_auth = '{0}/slm/webservice/v2.0/security/authorize'
uri_make_app = '{0}/slm/dashboard/addpanel.sp?cpoid=232318459988&_slug=/custom/{1}&key={2}'
uri_install_app = '{0}/slm/dashboard/changepanelsettings.sp?cpoid=10909656256&_slug=/custom/{1}&key={2}'
uri_page_layout = '{0}/slm/dashboardSwitchLayout.sp?dashboardName={1}}&layout={2}&oid={3}'

#These are hardcoded, do not change
params_make_page_cpoid = 729766
params_app_cpoid = 10909656256
params_app__slug = '/custom/{0}' #page oid
params_dashboard_name = "myhome{0}"
verify_cert_path = False 

def main():
    
    p = argparse.ArgumentParser()
    p.add_argument('-u', '--user', help="Rally username")
    p.add_argument('-p', '--password', help="Rally password")
    p.add_argument('-n', '--pagename', default="New Page", help="Rally Custom Page Name")
    p.add_argument('-o', '--pageoid', default=None, help="Page Oid if adding an app to an existing page")
    p.add_argument('-t','--apptitle', default="New App Title", help="Rally App Title")
    p.add_argument('-a','--appurl', default=None, help="URL to raw app html")
    p.add_argument('-l', '--layout', default='SINGLE', help='Page layout options: SINGLE (default), TWO_SPLIT, TWO_WEIGHTED_LEFT, TWO_WEIGHTED_RIGHT, THREE_WEIGHTED_CENTER')
    p.add_argument('command',nargs=2,help="Command to execute: [create|config] [app|page]")
    
    options = p.parse_args()

    hardcoded_password = getpass.getpass("Rally password: ")
    ## print(hardcoded_password)
    
    ###### authenticate rally 
    uri = uri_auth.format(uri_host)
    s = requests.Session()
    
    response = s.get(uri,verify=verify_cert_path,auth=HTTPBasicAuth(options.user, hardcoded_password))
    if response.status_code > 299:
        print ('Error authenticating %s' % response.status_code)
        return 
    response_payload = json.loads(response.text)
    token = response_payload['OperationResult']['SecurityToken']

    if options.command[0] != 'create':
        print ('{0} {1} command is not valid. Usage: [create] [app|page]'.format(options.command[0],options.command[1]))
        return 

    if options.command[1] != 'page' and options.command[1] != 'app':
        print ('{0} {1} command is not valid. Usage: [create] [app|page]'.format(options.command[0],options.command[1]))
        return 

    if options.command[1] == 'page':
        ## TODO validation pagename was provided 
        #make the page 
        page_oid = create_page(s,token,options.user,hardcoded_password,options.pagename)
        return page_oid 
    
    if options.command[1] == 'app':
        ## TODO validate app_title, app_path is provided 
        # load desired app
        app_oid = create_app(s, token, options.user, hardcoded_password,options.pageoid,options.apptitle,options.appurl)
        return app_oid 
     

def create_page(session, token, username, password, pagename):
    uri = uri_make_page.format(uri_host,token)   
   
    payload = {
        'name': "*" + pagename,
        'editorMode': 'create',
        'pid': 'myhome',
        'oid': 6440917,
        'timeboxFilter':'none'
    }
   
    print('Creating page: %s' % pagename);
    post_response = session.post(uri,auth=HTTPBasicAuth(username, password),data=payload,verify=verify_cert_path)
    ## print('post request: %s' % post_response.text)
    if post_response.status_code > 299:
        print("Error creating page %s " % post_response.status_code)
        print(post_response.text)

    ## <input type="hidden" name="oid" value="633252931351"/>
    oid_search = re.search('<input type=\"hidden\" name=\"oid\" value=\"(.*)\"/>', post_response.text, re.IGNORECASE)
  
    if oid_search:
        page_oid = oid_search.group(1)
    
    print('{0} page created with oid: {1}.  Use the following command to add apps to this page: \n\n  python3 app.py createt app -u username -o {1} -t MyAppTitle -a https://github.com/url/to/app.txt'.format(pagename, page_oid))
    return page_oid 

def create_app(session, token, username, password, page_oid, app_title, app_url):
    
    # make app panel on page
    dashboard_name = params_dashboard_name.format(page_oid)
    uri = uri_make_app.format(uri_host,page_oid,token)
    payload = {
        'panelDefinitionOid':431632107,
        'col':0,
        'index':0,
        'dashboardName': dashboard_name
    }
    post_response = session.post(uri,auth=HTTPBasicAuth(username, password),data=payload,verify=verify_cert_path)
    print('makeApp post request: %s' % post_response.text)
    make_app_response = json.loads(post_response.text)
        
    # extract panel oid 
    panel_oid = make_app_response['oid']

    ### TODO: if no panel oid, exit in error or handle error properly if the oid isn't on the object above

    #load app code 
    url = app_url
    app_code_response = requests.get(url,verify=False)
    app_html = app_code_response.text
    #print ('app html: %s ' % app_html)

    #install app 
    settings = json.dumps({
        "title": app_title,
        "project": None,
        "content": app_html,
        "autoResize": True
    }) 

    uri = uri_install_app.format(uri_host,page_oid,token)
    payload = {
        'oid': panel_oid,
        'settings': settings,
        'dashboardName': dashboard_name
    }
    post_response = session.post(uri,auth=HTTPBasicAuth(username, password),data=payload,verify=verify_cert_path)
    if post_response.status_code > 299:
        print('Error installing app %s' % post_response.text)
        return 

    print('App installed successfully on page {0} to panel {1}.  Make note of this information to make changes to configuration.'.format(page_oid,panel_oid))

    ### TODO: Return the panel oid so that we can refer to it again for configuratoin
    return panel_oid

if (__name__ == "__main__"):
    main()
