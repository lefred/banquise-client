#!/usr/bin/python
# banquise client : client program to send packages updates and retrieve
# a list of package to install
#    Copyright (C) 2010  Frederic Descamps - www.lefred.be
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
import fcntl
import struct
import getpass
import commands


global uuid
global server_url
global type
global pidfile
global config
global postscript

def showVersion():
    return "0.5"

def parseConfig():
    global uuid
    global server_url
    global type
    global pidfile
    global config
    global login
    global passwd
    global postscript

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
    try:
        login=config.defaults()['login']
    except:
        login=""
    try:
        passwd=config.defaults()['passwd']
    except:
        passwd=""
    try:
        postscript=config.defaults()['postscript']
    except:
        postscript=""
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
      "call_send_list" : "/addpack/",
      "call_send_install" : "/install/",
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
        print "ERROR: unexpected error on the server probably!" 
    exitClient()

def get_ip_address(ifname):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

def call_setup():
    global uuid
    if not uuid == None:
     print "Error: client already configured with the server !"
     exitClient()
    print "configuring the server to use banquise..."
    hostname = socket.gethostname()     
    try:
        priv_ip=get_ip_address('eth0')
    except:
        try:
            priv_ip=get_ip_address('eth1') 
        except:
            try:
                priv_ip=get_ip_address('wlan0')
            except:
                priv_ip=get_ip_address('lo')
    print "You need a valid license key." 
    license=raw_input("license key : ")
    release=get_release()
    xml = request({'method': "call_setup", 'license': license, 'hostname': hostname, 'release': release, 'priv_ip': priv_ip})
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
    packages_to_update=[]
    packages_skipped=[]
    for children in my.up.getUpdatesList():
        matches=my.pkgSack.searchNevra(name=children[0], arch=children[1], epoch=children[2],
                                       ver=children[3], rel=children[4])
        packages_to_update.append("%s,%s,%s,%s,%s" % (children[0],children[1],children[3],children[4],matches[0].repo))
    json_value = json.dumps(packages_to_update)
    xml = request({'method': "call_send_update", 'uuid': uuid, 'packages': json_value})
    print "to update : " +str(xml)
    for children in json.loads(xml):
          #print "do this : yum update "+children
          myPckList=children.split(',')
          mylist = my.pkgSack.searchNevra(name=myPckList[0],arch=myPckList[1],ver=myPckList[2],rel=myPckList[3])
          if not mylist:
              print "skipping %s,%s,%s,%s" % (myPckList[0], myPckList[1],myPckList[2], myPckList[3])
              packages_skipped.append("%s,%s,%s,%s" % (myPckList[0], myPckList[1],myPckList[2], myPckList[3]))
          else:
             for po in mylist:
                my.update(po)
    xml = request({'method': "call_send_install", 'uuid': uuid})
    print "to install : " +str(xml)
    for children in json.loads(xml):
          myPckList=children.split(',')
          mylist = my.pkgSack.searchNevra(name=myPckList[0],arch=myPckList[1],ver=myPckList[2],rel=myPckList[3])
          if not mylist:
              print "skipping %s,%s,%s,%s" % (myPckList[0], myPckList[1],myPckList[2], myPckList[3])
              packages_skipped.append("%s,%s,%s,%s" % (myPckList[0], myPckList[1],myPckList[2], myPckList[3]))
          else:
             for po in mylist:
                my.install(po)
    my.buildTransaction()
    saveout = sys.stdout
    sys.stdout = StringIO()
    try:
        my.processTransaction()
    except: 
        sys.stdout = saveout
        print "Error: unexpected error during transaction !" 
        exitClient()
    sys.stdout = saveout
    #TODO retrieve the installed packages and notify the database
    #for children in my.ts.ts.getKeys():
    #  print children
    myValues =  my.ts.ts.getKeys()
    if myValues == None:
       print "nothing set to update"
       if packages_skipped:
          json_value = json.dumps("")
          json_value_skip = json.dumps(packages_skipped)
          xml = request({'method': "call_packs_done", 'uuid': uuid, 'packages': json_value, 'packages_skipped': json_value_skip})
          print xml
    else:
      packages_updated=[]
      for (hdr, path) in cleanupList(myValues):
        print "%s - %s - %s - %s" % (hdr['name'], hdr['arch'],hdr['version'], hdr['release'])
        packages_updated.append("%s,%s,%s,%s" % (hdr['name'], hdr['arch'],hdr['version'], hdr['release']))
      json_value = json.dumps(packages_updated)
      json_value_skip = json.dumps(packages_skipped)
      xml = request({'method': "call_packs_done", 'uuid': uuid, 'packages': json_value, 'packages_skipped': json_value_skip})
      print xml
      if postscript:
          status,output = commands.getstatusoutput(postscript) 
          
def send_list(): 
    global login
    global passwd
    check_validity(uuid)
    my = yum.YumBase()
    packages_to_add=[]
    packages_skipped=[]
    print "You need an admin login to perform this operation."
    if not login:
        login=raw_input("Login : ")
    if not passwd:
        passwd=getpass.getpass()
    
    ygh = my.doPackageLists()
    for children in ygh.available:
        packages_to_add.append("%s,%s,%s,%s,%s" % (children.pkgtup[0],children.pkgtup[1],children.pkgtup[3],children.pkgtup[4],children.repo))
    json_value = json.dumps(packages_to_add)
    xml = request({'method': "call_send_list", 'login': login, 
                   'passwd': passwd, 'uuid': uuid, 'packages': json_value})
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
     elif sys.argv[1] == 'list':
        send_list()
     elif sys.argv[1] == 'version':
        print showVersion()
     else:
        print "Error: %s command not found !" % (sys.argv[1])
exitClient()
