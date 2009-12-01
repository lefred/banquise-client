#!/usr/bin/python

import json
import urllib
import socket
import sys
import hashlib
import string
import random
import os
import getpass
from ConfigParser import *
import yum
from StringIO import StringIO


global uuid
global server_url
global type
global pidfile
global config

def parseConfig():
    global uuid
    global server_url
    global type
    global pidfile
    global config

    if not os.path.exists(r'/etc/banquise.conf'):
      print "Error: client configuration file missing !" 
      exitClient()
    config=readConfig()
    #check server url
    if not config.defaults()['server_url']: 
     print "Error: client configuration, server_url is not set !" 
     exitClient()
    server_url=config.defaults()['server_url']
    #check client type
    if not config.defaults()['type']: 
     print "Error: client configuration, client type is not set !" 
     exitClient()
    if config.defaults()['type'] != 'REST' and config.defaults()['type'] != 'XMPP': 
     print "Error: client configuration, client type value is wrong, it should be REST or XMPP !" 
     exitClient()
    type=config.defaults()['type']
    #check pid file
    if not config.defaults()['pid']: 
     print "Error: client configuration, pid setting not defined !" 
     exitClient()
    pidfile=config.defaults()['pid']
    #check uuid
    uuid=getuuid(config)
    return True

def getuuid(config):
    try: 
      value=config.defaults()['uuid']
    except KeyError:
      value=None
    return value
  
 
def checkPid():
    if globals().has_key('pidfile'):
    	if os.path.exists(pidfile):
     		print "Error: client already running or dies unexpectly (pid file exists) !" 
     		sys.exit(4)
    	FILE = open(pidfile,"w")   
    	FILE.write(str(os.getpid()))
    	FILE.close()

def exitClient():
    if globals().has_key('pidfile'):
    	os.remove(pidfile)
    sys.exit(1)
   
def cleanupList(f):
    if f:
     return [i for i in list(f) if i] 
    else:
     return []

def readConfig():
    config = ConfigParser()
    if not os.path.exists(r'/etc/banquise.conf'):
      print "Error: client configuration file is missing !"
      exitClient()
    config.read('/etc/banquise.conf')
    return config


def request(args):
    global server_url
    params = urllib.urlencode(args)
    METHOD = {
      "call_setup": "/setup/",
      "call_test" : "/test/",
      "call_send_update" : "/update/",
      "set_release": "/set_release/",
      "call_packs_done": "/packdone/",
    }
    return urllib.urlopen(server_url+METHOD.get(args.get('method')),params).read()

def call_test(uuid):
    if check_validity(uuid):
          print "Communication with server ok"

def check_validity(uuid):
    xml = request({'method': "call_test", 'uuid': uuid})
    if xml == "OK":
        return True
    elif xml == "ERROR2":
        print "ERROR: contract is expired for this host !"
    elif xml == "ERROR3":
        print "ERROR: host not found on the server !"
    else:
        print "ERROR: unexpected error !" 
    exitClient()

def call_setup():
    global uuid
    if not uuid == None:
     print "Error: client already configured with the server !"
     exitClient()
    print "configuring the server to use banquise..."
    hostname = socket.gethostname()     
    # TODO: retrieve the ip's
    priv_ip="127.0.0.1"
    pub_ip="127.0.0.1"
    print "You need a valid license key." 
    license=raw_input("license key : ")
    release=get_release()
    xml = request({'method': "call_setup", 'license': license, 'hostname': hostname, 'release': release})
    if xml == "ERROR1":
        print "ERROR: this host (or another with the same name) is already linked to a valid contract!"
        exitClient()
    print xml
    config.set("DEFAULT","uuid",xml)
    with open("/etc/banquise.conf","wb") as configfile:    
     config.write(configfile)

def get_release():
    # TODO : use lsb_release
    fobj = open("/etc/redhat-release",'r')
    try:
      release = fobj.readline()[:-1]
    finally:
      fobj.close
    return release

def set_release():
    global uuid
    release = get_release()
    check_validity(uuid)
    xml = request({'method': "set_release", 'uuid': uuid, 'release': release})
    if xml == "OK":
        print "Release set to " + release
        return True
    else:
        print "ERROR: unexpected error!"
        exitClient()
        
def send_updates(): 
    check_validity(uuid)
    # search for local updates
    my = yum.YumBase()
    my.doRepoSetup()
    my.doSackSetup()
    my.doTsSetup()
    my.doRpmDBSetup()
    str=""
    for children in my.up.getUpdatesList():
        #print("name: %s  arch: %s version: %s release: %s") % (children[0],children[1],children[3],children[4])
        str=str+children[0]+","+children[1]+","+children[3]+","+children[4]+"|"
    xml = request({'method': "call_send_update", 'uuid': uuid, 'packages': str[:-1]})
    print xml
    for children in json.loads(xml):
          print "do this : yum update "+children
          myPckList=children.split(',')
          mylist = my.pkgSack.searchNevra(name=myPckList[0],arch=myPckList[1],ver=myPckList[2],rel=myPckList[3])
          for po in mylist:
             my.update(po)
    my.buildTransaction()
    saveout = sys.stdout
    sys.stdout = StringIO()
    my.processTransaction()
    sys.stdout = saveout
    #TODO retrieve the installed packages and notify the database
    #for children in my.ts.ts.getKeys():
    #  print children
    myValues =  my.ts.ts.getKeys()
    if myValues == None:
       print "nothing set to update"
    else:
      packages_updated=[]
      for (hdr, path) in cleanupList(myValues):
        print "%s - %s - %s - %s" % (hdr['name'], hdr['arch'],hdr['version'], hdr['release'])
        packages_updated.append("%s,%s,%s,%s" % (hdr['name'], hdr['arch'],hdr['version'], hdr['release']))
        json_value = json.dumps(packages_updated)
        xml = request({'method': "call_packs_done", 'uuid': uuid, 'packages': json_value})
        print xml

#if __main__ == 
# Main program
if len(sys.argv) != 2:
   print "Error: a command is needed"
   sys.exit(1)
else:
  parseConfig()
  checkPid()
  if sys.argv[1]   == 'setup':
        call_setup()
  else: 
     if sys.argv[1]   == 'test':
        call_test(uuid);
     elif sys.argv[1] == 'setrel':
        set_release()
     elif sys.argv[1] == 'update':
        send_updates()
     else:
        print "Error: %s command not found !" % (sys.argv[1])
exitClient()
