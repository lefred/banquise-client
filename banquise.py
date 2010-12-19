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
import random
import os
import getpass
import fcntl
import struct
import commands
import re
import errno
from ConfigParser import ConfigParser
from StringIO import StringIO

sys.path.append("/usr/share/banquise")

global uuid
global server_url
global typecall
global pidfilename
global config
global postscript

def show_version():
    return "0.5"

def parse_config():
    global uuid
    global server_url
    global typecall
    global pidfilename
    global config
    global login
    global passwd
    global postscript
    global backend
    global myBackend
    global proxy

    if not os.path.exists(r'/etc/banquise.conf'):
        print "Error: client configuration file missing !"
        exit_client()
    config = read_config()
    #check server url
    if not config.defaults()['server_url']:
        print "Error: client configuration, server_url is not set !"
        exit_client()
    server_url = config.defaults()['server_url']
    #check client type
    if not config.defaults()['type']:
        print "Error: client configuration, client type is not set !"
        exit_client()
    if config.defaults()['type'] != 'REST' \
    and config.defaults()['type'] != 'XMPP':
        print "Error: client configuration, client type value is wrong, \
                it should be REST or XMPP !"
        exit_client()
    typecall = config.defaults()['type']

    #check backend
    if not config.defaults()['backend']:
        print "Error: client configuration, client backend is not set !"
        exit_client()
    if config.defaults()['backend'] != 'yum' \
       and config.defaults()['backend'] != 'smart':
        print "Error: client configuration, client backend value is wrong,\
                it should be YUM or SMART !"
        exit_client()
    backend = config.defaults()['backend']

    myBackend = __import__(backend + "backend")

    #check pid file
    if not config.defaults()['pid']:
        print "Error: client configuration, pid setting not defined !"
        exit_client()
    pidfilename = config.defaults()['pid']
    try:
        login = config.defaults()['login']
    except:
        login = ""
    try:
        passwd = config.defaults()['passwd']
    except:
        passwd = ""
    try:
        postscript = config.defaults()['postscript']
    except:
        postscript = ""
    try:
        proxy = config.defaults()['proxy']
    except:
        proxy = ""
    #check uuid
    uuid = getuuid(config)
    return True

def getuuid(config):
    try:
        value = config.defaults()['uuid']
    except KeyError:
        value = None
    return value


def check_pid():
    if globals().has_key('pidfilename'):
        if os.path.exists(pidfilename):
            pidfile = open(pidfilename,"r")
            line = pidfile.read()
            try:
                os.kill(int(line), 0)
            except OSError, err:
                if err.errno == errno.ESRCH:
                    print "Warning: PID file exists " \
                          "but client died unexpectedly !"
            else:
                print "Error: client already running (pid file exists) !"
                sys.exit(4)
        pidfile = open(pidfilename,"w")
        pidfile.write(str(os.getpid()))
        pidfile.close()

def exit_client():
    if globals().has_key('pidfilename'):
        os.remove(pidfilename)
    sys.exit(1)

def read_config():
    config = ConfigParser()
    if not os.path.exists(r'/etc/banquise.conf'):
        print "Error: client configuration file is missing !"
        exit_client()
    config.read('/etc/banquise.conf')
    return config


def request(args):
    global server_url
    params = urllib.urlencode(args)

    if (proxy != ""):
        proxies = {proxy[:proxy.find('://')]: proxy}
    else:
        proxies = None

    methods = {
      "call_setup": "/setup/",
      "call_test" : "/test/",
      "call_send_update" : "/update/",
      "call_send_changelog" : "/changelog/",
      "call_send_ask_update" : "/askupdate/",
      "call_send_sync" : "/sync/",
      "set_release": "/set_release/",
      "call_packs_done": "/packdone/",
      "call_send_list" : "/addpack/",
      "call_send_install" : "/install/",
      "call_send_metainfo" : "/metainfo/",
      "call_send_metabug" : "/metabug/",
    }
    timeout = 600
    socket.setdefaulttimeout(timeout)
    return urllib.urlopen(server_url+methods.get(args.get('method')), \
                          params, proxies).read()

def call_test(uuid):
    if check_validity(uuid):
        print "Communication with server ok"

def check_validity(uuid):
    version = show_version()
    xml = request({'method': "call_test", 'uuid': uuid, 'version': version})
    if xml == "OK":
        return True
    elif xml == "VERSION":
        print "Client version not supported"
    elif xml == "ERROR2":
        print "ERROR: contract is expired for this host !"
    elif xml == "ERROR3":
        print "ERROR: host not found on the server !"
    else:
        print "ERROR: unexpected error on the server probably!"
    exit_client()

def get_ip_address(ifname):

    mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return socket.inet_ntoa(fcntl.ioctl(mysocket.fileno(), 0x8915,
                                        struct.pack('256s',
                                                    ifname[:15]))[20:24])

def call_setup():
    global uuid
    if not uuid == None:
        print "Error: client already configured with the server !"
        exit_client()
    print "configuring the server to use banquise..."
    hostname = socket.gethostname()
    try:
        priv_ip = get_ip_address('eth0')
    except:
        try:
            priv_ip = get_ip_address('eth1')
        except:
            try:
                priv_ip = get_ip_address('wlan0')
            except:
                priv_ip = get_ip_address('lo')
    print "You need a valid license key."
    license = raw_input("license key : ")
    release = get_release()
    try:
        xml = request({'method': "call_setup", 'license': license, 
                       'hostname': hostname, 'release': release, 
                       'priv_ip': priv_ip})
    except:
        print "ERROR: network problem or wrong url in banquise.conf !"
        exit_client()
    if xml == "ERROR0":
        print "ERROR: the entered license key is not valid !"
        exit_client()
    if xml == "ERROR1":
        print "ERROR: this host (or another with the same name) is " \
                "already linked to a valid contract!"
        exit_client()
    config.set("DEFAULT", "uuid", xml)
    with open("/etc/banquise.conf", "wb") as configfile:
        config.write(configfile)

def get_release():
    if os.path.exists('/usr/bin/lsb_release'):
        description = commands.getoutput("/usr/bin/lsb_release -ds")
        description = description.replace('"', "")
    else:
        description = "not found"

    return description

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
        exit_client()

def send_sync():
    check_validity(uuid)
    mybck = myBackend.Backend()
    installed_packages = mybck.get_installed_list()
    json_value = json.dumps(installed_packages)
    xml = request({'method': "call_send_sync", 'uuid': uuid, 
                   'packages': json_value})
    print str(xml)

def send_updates():
    check_validity(uuid)
    # search for local updates
    mybck = myBackend.Backend()
    if (proxy != ""):
        mybck.set_proxy(proxy)
    packages_to_update = []
    metainfo_to_update = []
    packages_skipped = []
    packages_to_update, metainfo_to_update, metabug_to_update = \
            mybck.get_updates_list()
    for metainfo in metainfo_to_update:
        json_value2 = json.dumps(metainfo)
        xml = request({'method': "call_send_metainfo", 'metainfo': json_value2})
    for metabug in metabug_to_update:
        json_value3 = json.dumps(metabug)
        xml = request({'method': "call_send_metabug", 'metabug': json_value3})
    for children in packages_to_update:
        tab = children.split(",")
        changelog = mybck.get_change_log(tab[0], tab[1], tab[2], tab[3])
        json_value = json.dumps(children)
        pack_id = request({'method': "call_send_update",
                           'uuid': uuid, 'packages': json_value})
        json_value = json.dumps(changelog)
        xml = request({'method': "call_send_changelog",
                       'pack_id': pack_id, 'changelog': json_value})
    xml = request({'method': "call_send_ask_update", 'uuid': uuid})
    print "to update : " +str(xml)
    for children in json.loads(xml):
        #print "do this : yum update "+children
        my_pck_list = children.split(',')
        mylist = mybck.search(name = my_pck_list[0], arch = my_pck_list[1],
                           ver = my_pck_list[2], rel = my_pck_list[3])
        if not mylist:
            print "skipping %s,%s,%s,%s" % (my_pck_list[0], my_pck_list[1],
                                            my_pck_list[2], my_pck_list[3])
            packages_skipped.append("%s,%s,%s,%s" % (my_pck_list[0],
                                                     my_pck_list[1],
                                                     my_pck_list[2],
                                                     my_pck_list[3]))
        else:
            for pobj in mylist:
                mybck.update(pobj)
    xml = request({'method': "call_send_install", 'uuid': uuid})
    print "to install : " +str(xml)
    for children in json.loads(xml):
        my_pck_list = children.split(',')
        mylist = mybck.search(name=my_pck_list[0], arch=my_pck_list[1],
                           ver=my_pck_list[2], rel=my_pck_list[3])
        if not mylist:
            print "skipping %s,%s,%s,%s" % (my_pck_list[0],
                                            my_pck_list[1],
                                            my_pck_list[2],
                                            my_pck_list[3])
            packages_skipped.append("%s,%s,%s,%s" % (my_pck_list[0],
                                                     my_pck_list[1],
                                                     my_pck_list[2],
                                                     my_pck_list[3]))
        else:
            for pobj in mylist:
                mybck.install(pobj)

    mybck.build_transaction()
    saveout = sys.stdout
    sys.stdout = StringIO()
    try:
        mybck.process_transaction()
    except:
        sys.stdout = saveout
        print "Error: unexpected error during transaction !"
        exit_client()
    sys.stdout = saveout
    #TODO retrieve the installed packages and notify the database
    #for children in my.ts.ts.getKeys():
    #  print children
    packages_updated = mybck.get_keys()
    if packages_updated == None:
        print "nothing set to update"
        if packages_skipped:
            json_value = json.dumps("")
            json_value_skip = json.dumps(packages_skipped)
            xml = request({'method': "call_packs_done",
                           'uuid': uuid, 'packages': json_value,
                           'packages_skipped': json_value_skip})
            print xml
    else:
        json_value = json.dumps(packages_updated)
        json_value_skip = json.dumps(packages_skipped)
        xml = request({'method': "call_packs_done", 'uuid': uuid,
                       'packages': json_value,
                       'packages_skipped': json_value_skip})
        print xml
        if postscript:
            status, output = commands.getstatusoutput(postscript)

def send_list():
    """
    Send list of all available packages in the repositories
    """
    global login
    global passwd
    check_validity(uuid)
    mybck = myBackend.backend()
    packages_to_add = []
    print "You need an admin login to perform this operation."
    if not login:
        login = raw_input("Login : ")
    if not passwd:
        passwd = getpass.getpass()
    json_value = json.dumps(packages_to_add)
    xml = request({'method': "call_send_list", 'login': login,
                   'passwd': passwd, 'uuid': uuid, 'packages': json_value})
    if re.search('incorrect', xml):
        print xml
    else:
        print "Warning: this operation can be very long ! (+/- 1h)"
        packages_to_add = mybck.package_lists()
        json_value = json.dumps(packages_to_add)
        old_repo = ""
        info = None
        for pack in packages_to_add:
            my_pack_list = pack.split(',')
            info, old_repo = mybck.get_info(old_repo, my_pack_list[4], info)
            notice_update_id, notice_type, tup_update_id,
            tup_bug = my.getNotice(my_pack_list[0],
                                   my_pack_list[2], my_pack_list[3], info)

            # send here the data per package
            # TODO
            json_value2 = json.dumps(tup_update_id)
            xml = request({'method': "call_send_metainfo",
                           'metainfo': json_value2})
            json_value3 = json.dumps(tup_bug)
            xml = request({'method': "call_send_metabug", 
                           'metabug': json_value3})
        xml = request({'method': "call_send_list", 'login': login, 
                   'passwd': passwd, 'uuid': uuid, 'packages': json_value})
        print xml

#if __main__ ==
# Main program
if len(sys.argv) != 2:
    print "Error: a command is needed"
    sys.exit(1)
else:
    parse_config()
    check_pid()
    if sys.argv[1]  == 'setup':
        call_setup()
    else: 
        if sys.argv[1]  == 'test':
            call_test(uuid)
        elif sys.argv[1] == 'setrel':
            set_release()
        elif sys.argv[1] == 'update':
            send_updates()
        elif sys.argv[1] == 'sync':
            send_sync()
        elif sys.argv[1] == 'list':
            send_list()
        elif sys.argv[1] == 'version':
            print show_version()
        elif sys.argv[1] == 'help':
            print "banquise <command>"
            print "    where command is :"
            print "        - setup : configure the client with the license"
            print "        - test : test communication with the server"
            print "        - setrel : push the release of the distribution " \
                    "to the server"
            print "        - update : update the packages and send the new " \
                    "available packages to update"
            print "        - sync : sync the package to the server db (new, " \
                    "deleted, sync)"
            print "        - list : send all the package from the repo to " \
                    "the server's db (very intensive + admin user needed)"
            print "        - version : display the version"
        else:
            print "Error: %s command not found !" % (sys.argv[1])
exit_client()
