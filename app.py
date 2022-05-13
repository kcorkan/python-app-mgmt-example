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
import yaml

uri_host = 'https://rally1.rallydev.com'

uri_make_page = '{0}/slm/wt/edit/create.sp?cpoid=729766&key={1}'
uri_auth = '{0}/slm/webservice/v2.0/security/authorize'
uri_make_app = '{0}/slm/dashboard/addpanel.sp?cpoid=232318459988&_slug=/custom/{1}&key={2}'
uri_install_app = '{0}/slm/dashboard/changepanelsettings.sp?cpoid=10909656256&_slug=/custom/{1}&key={2}'
uri_page_layout = '{0}/slm/dashboardSwitchLayout.sp?dashboardName={1}}&layout={2}&oid={3}'
uri_pref_put = '{0}/slm/webservice/v2.0/Preference/create?key={1}'
uri_pref_get = '{0}/slm/webservice/v2.0/Preference?query=(AppId = \"{1}\")&fetch=Name'

#These are hardcoded, do not change
params_make_page_cpoid = 729766
params_app_cpoid = 10909656256
params_app__slug = '/custom/{0}' #page oid
params_dashboard_name = "myhome{0}"
verify_cert_path = False 

def main():
    
    requests.packages.urllib3.disable_warnings() 
    p = argparse.ArgumentParser()
    p.add_argument('-c', '--cfg')

    options = p.parse_args()
    cfg_file = options.cfg
    cfg = read_config(options.cfg)
    #print (cfg)
    
    pwd = cfg['connection']['password']
  
    ##### prompt for password if we don't want to store in a file 
    if pwd == None or pwd == '': 
        pwd = getpass.getpass("Rally password: ")
      
    ###### authenticate rally 
    uri = uri_auth.format(uri_host)
    s = requests.Session()
    
    user = cfg['connection']['user']
    
    response = s.get(uri,verify=verify_cert_path,auth=HTTPBasicAuth(user, pwd))
    if response.status_code > 299:
        print ('Error authenticating %s' % response.status_code)
        return 
    response_payload = json.loads(response.text)
    token = response_payload['OperationResult']['SecurityToken']
    
    page_oid = cfg['page']['oid']
    if page_oid == 0 or page_oid == None:
        page_oid = create_page(s,token,user,pwd,cfg['page']['title'])
        cfg['page']['oid'] = page_oid


    #print (cfg['apps'])
    for a in cfg['apps']:
            app_oid = a['oid']
            if app_oid == 0 or app_oid == None:
                print ('> Creating app [{0}]\n'.format(a['title']))
                app_oid = create_app(s, token, user, pwd,page_oid,a['title'],a['raw_url'])
                a['oid'] = app_oid

            print(app_oid)
            for c in a['configs']:
                print ('>> Configuring app [{0}]\n'.format(a['title']))
                pref_name = c['name']
                pref_value = c['value']
                #print (type(pref_value))
                if type(pref_value != str):
                    print ('>>> Serializing preference [{0}]\n'.format(pref_name))
                    pref_value = json.dumps(pref_value, separators=(',', ':'))
                #print (type(pref_value))    
                
                create_or_update_pref(s,token,user,pwd,app_oid,pref_name,pref_value)
                


    save_config(cfg_file,cfg)            

def read_config(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)

def save_config(file_path, cfg_obj):
    with open(file_path, 'w') as file:
        documents = yaml.dump(cfg_obj, file)

def create_page(session, token, username, password, pagename):
    uri = uri_make_page.format(uri_host,token)   
   
    payload = {
        'name': "*" + pagename,
        'editorMode': 'create',
        'pid': 'myhome',
        'oid': 6440917,
        'timeboxFilter':'none'
    }
   
    print('> Creating page: %s\n' % pagename);
    post_response = session.post(uri,auth=HTTPBasicAuth(username, password),data=payload,verify=verify_cert_path)
    ## print('post request: %s' % post_response.text)
    if post_response.status_code > 299:
        print("Error creating page %s " % post_response.status_code)
        print(post_response.text)

    ## <input type="hidden" name="oid" value="633252931351"/>
    oid_search = re.search('<input type=\"hidden\" name=\"oid\" value=\"(.*)\"/>', post_response.text, re.IGNORECASE)
  
    if oid_search:
        page_oid = oid_search.group(1)
    
    print('>> {0} page created with oid: {1}\n'.format(pagename, page_oid))
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
    #print('makeApp post request: %s' % post_response.text)
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

    print('>> App [{2}] installed successfully on page {0} to panel {1}.'.format(page_oid,panel_oid,app_title))

    ### TODO: Return the panel oid so that we can refer to it again for configuratoin
    return panel_oid

def create_or_update_pref (session, token, username, password, panel_oid, pref_name,pref_value):

    uri_get = uri_pref_get.format(uri_host,panel_oid)
    existing_prefs = session.get(uri_get,auth=HTTPBasicAuth(username, password))
   
    prefs = json.loads(existing_prefs.text)
    pref_uri = uri_pref_put.format(uri_host,token)
    if prefs['QueryResult']['TotalResultCount'] > 0:
        prefs = prefs['QueryResult']['Results']
        for p in prefs:
            if p['_refObjectName'] == pref_name:
                print ('Preference [{0}] found: {1}'.format(pref_name,p['_ref']))
                pref_uri = '{0}?key={1}'.format(p['_ref'],token)

    
    #headers = {"Content-Type":"application/json"}
    payload = {
        'Preference': {
                'Name': pref_name, 
                'Value': pref_value,
                'AppId': panel_oid
            } 
    }
    payload = json.dumps(payload)
    put_response = session.put(pref_uri,auth=HTTPBasicAuth(username, password),data=payload,verify=verify_cert_path)
    print ('... Preference [{1}] updated: \n\n{0}'.format(put_response.text,pref_name))

if (__name__ == "__main__"):
    main()
