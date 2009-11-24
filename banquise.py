#!/usr/bin/python

from xml.etree import ElementTree
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


##global md5str='098f6bcd4621d373cade4e832627b4f6'
global md5str
global server_url
global type
global pidfile

def parseConfig():
    global md5str
    global server_url
    global type
    global pidfile

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
    #check md5str
    md5str=getmd5str(config)
    return True

def getmd5str(config):
    try: 
      value=config.defaults()['md5']
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
    return urllib.urlopen(server_url+'/setup/',params).read()

def call_test(md5str):
    if check_validity(md5str):
          print "Communication with server ok"

def check_validity(md5str):
    xml = request({'method': "test", 'arg1': md5str})
    doc = ElementTree.fromstring(xml)
    for children in doc.getiterator():
       if children.tag.find("msg") != -1:
          if children.text == 'Id not found':
            print "Error: client key is invalid or expired !"
            exitClient()
          return True
    # TODO check the contract validity

def call_setup():
    global md5str
    if not md5str == None:
     print "Error: client already configured with the server !"
     exitClient()
    print "configuring the server to use banquise..."
    hostname = socket.gethostname()     
    hash = hashlib.md5()
    randstr="a"
    for i in range(5):
      randstr=randstr+string.ascii_lowercase[random.randint(0,25)]
    hash.update(hostname+randstr)
    md5str=hash.hexdigest()
    # TODO: retrieve the ip's
    priv_ip="127.0.0.1"
    pub_ip="127.0.0.1"
    print "You need a valid license key." 
    license=raw_input("license key : ")
    xml = request({'method': "call_setup", 'arg1': license, 'arg2': hostname})
    print xml
    exit
    doc = ElementTree.fromstring(xml)
    for children in doc.getiterator():
       if children.tag.find("msg") != -1:
          print "%s" % (children.text)
       if children.tag.find("status") != -1:
          if children.text == '1':
    	    config=[]
	    config.append("md5="+md5str+"\n")
	    FILE = open("/etc/banquise.conf","a")   
	    FILE.writelines(config)
	    FILE.close()

def set_release():
    check_validity(md5str)
    # TODO : use lsb_release
    fobj = open("/etc/redhat-release",'r')
    try:
      release = fobj.readline()[:-1]
    finally:
      fobj.close
    xml = request({'method': "set_release", 'arg1': md5str, 'arg2': release})
    doc = ElementTree.fromstring(xml)
    for children in doc.getiterator():
       if children.tag.find("msg") != -1:
          print "%s" % (children.text)

def send_updates(): 
    check_validity(md5str)
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
    xml = request({'method': "send_updates", 'arg1': md5str, 'arg2': str[:-1]})
    doc = ElementTree.fromstring(xml)
    for children in doc.getiterator():
       if children.tag.find("msg") != -1:
          print "%s" % (children.text)
       if children.tag.find("toinstall") != -1:
          print "do this : yum update "+children.text
          myPckList=children.text.split(' ')
          for element in myPckList:
             var=element.split(':')
             mylist = my.pkgSack.searchNevra(name=var[0],ver=var[1],rel=var[2])
             for po in mylist:
               my.update(po)
             #os.system("yum update "+children.text) 
             #xml = request({'method': "updates done", 'arg1': md5str, 'arg2': children.text})
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
      str=""
      for (hdr, path) in cleanupList(myValues):
        print "%s - %s - %s - %s" % (hdr['name'], hdr['arch'],hdr['version'], hdr['release'])
        #str=str+hdr['name']+","+hdr['arch']+","+children['version']+","+children['release']+"|"
        str="%s%s,%s,%s,%s|" % (str,hdr['name'], hdr['arch'],hdr['version'], hdr['release'])
      xml = request({'method': "packs_done", 'arg1': md5str, 'arg2': str[:-1]})
      doc = ElementTree.fromstring(xml)
      for children in doc.getiterator():
          if children.tag.find("msg") != -1:
               print "%s" % (children.text)

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
        set_release()
  else: 
     if sys.argv[1]   == 'test':
        call_test(md5str);
     elif sys.argv[1] == 'setrel':
        set_release()
     elif sys.argv[1] == 'update':
        send_updates()
     else:
        print "Error: %s command not found !" % (sys.argv[1])
exitClient()
