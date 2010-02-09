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
    
        for children in self.backend.up.getUpdatesList():
            matches = self.search(name=children[0], arch=children[1], epoch=children[2],
                                           ver=children[3], rel=children[4])
            packages_to_update.append("%s,%s,%s,%s,%s" % (children[0],children[1],children[3],children[4],matches[0].repo))
        
        return packages_to_update
    
    
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
    
    
    def getKeys(self):
        myValues = self.backend.ts.ts.getKeys()
        if myValues == None:
            return None
        else:  
            packages_updated = []
            for (hdr, path) in cleanupList(myValues):
                print "%s - %s - %s - %s" % (hdr['name'], hdr['arch'],hdr['version'], hdr['release'])
                packages_updated.append("%s,%s,%s,%s" % (hdr['name'], hdr['arch'],hdr['version'], hdr['release']))
            return packages_updated