import yum

class backend:
    
    def __init__(self):
        self.backend = yum.YumBase()
        
    
    def packageLists(self):
        packages_to_add = []
        
        ygh = self.backend.doPackageLists()
    
        for children in ygh.available:
            packages_to_add.append("%s,%s,%s,%s,%s" % (children.pkgtup[0],children.pkgtup[1],children.pkgtup[3],children.pkgtup[4],children.repo))
    
        return packages_to_add
    
    
    def getUpdatesList(self):
        packages_to_update = []
        
        self.backend.doRepoSetup()
        self.backend.doSackSetup()
        self.backend.doTsSetup()
        self.backend.doRpmDBSetup()   
        old_repo=""
        for children in self.backend.up.getUpdatesList():
            matches = self.search(name=children[0], arch=children[1], epoch=children[2],
                                           ver=children[3], rel=children[4])
            
            if old_repo != str(matches[0].repo):
                old_repo=str(matches[0].repo)
                info = yum.update_md.UpdateMetadata((matches[0].repo,))
            tup_pack=(children[0],children[3],children[4])
            notice=info.get_notice(tup_pack)
            if notice:
                notice_type=notice.__getitem__('type')
                notice_update_id=notice.__getitem__('update_id')
            else:
                notice_type="normal"
                notice_update_id="none"
            packages_to_update.append("%s,%s,%s,%s,%s,%s,%s" % (children[0],children[1],children[3],children[4],matches[0].repo,notice_type,notice_update_id))
        
        return packages_to_update

    def getInstalledList(self):
        packages_installed = []
        
        self.backend.doRepoSetup()
        self.backend.doSackSetup()
        self.backend.doTsSetup()
        self.backend.doRpmDBSetup()   
   
        for children in self.backend.doPackageLists("installed").installed:
            packages_installed.append("%s,%s,%s,%s,%s" % (children.pkgtup[0],children.pkgtup[1],children.pkgtup[3],children.pkgtup[4],children.repo))
        return packages_installed

    
    def install(self, po):
        self.backend.install(po)
        
        
    def update(self, po):
        self.backend.update(po)
        
    
    def buildTransaction(self):
        return self.backend.buildTransaction()
    
    
    def processTransaction(self):
        return self.backend.processTransaction()
    
    
    def search(self, name=None, epoch=None, ver=None, rel=None, arch=None):
        return self.backend.pkgSack.searchNevra(name, epoch, ver, rel, arch)
    
    
    def cleanupList(self,f):
        if f:
            return [i for i in list(f) if i]
        else:
            return []
        
    def getKeys(self):
        myValues = self.backend.ts.ts.getKeys()
        if myValues == None:
            return None
        else:  
            packages_updated = []
            for (hdr, path) in self.cleanupList(myValues):
                print "%s - %s - %s - %s" % (hdr['name'], hdr['arch'],hdr['version'], hdr['release'])
                packages_updated.append("%s,%s,%s,%s" % (hdr['name'], hdr['arch'],hdr['version'], hdr['release']))
            return packages_updated
   
 
    def setProxy(self, proxy):
        """Set proxy"""
        
        if (proxy.find('@') != -1):
            """Username and password are in the proxy url"""
            protocol = proxy[:proxy.find('://')]
            name = proxy[proxy.find('@') + 1:]
            url = protocol + '://' + name
            creds = proxy[proxy.find('://') + 1:proxy.find('@')].split(':')
            username = creds[0]
            password = creds[1]
                   
            self.backend.conf.proxy = url
            self.backend.conf.proxy_password = password
            self.backend.conf.proxy_username = username
            
        else:
            self.backend.conf.proxy = proxy