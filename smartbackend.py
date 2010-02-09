from smart import init, initDistro, initPlugins, initPsyco
from smart.commands import *
from smart.transaction import *
from smart import *

class backend:
    
    def __init__(self):
        self.ctrl = init()
        initDistro(self.ctrl)
        initPlugins()
        initPsyco()
        self.ctrl.reloadChannels()
        self.cache = self.ctrl.getCache()
        self.itrans = Transaction(self.cache, PolicyInstall)
        self.utrans = Transaction(self.cache, PolicyUpgrade)
        self.iaction = False
        self.uaction = False
        
    
    def packageLists(self):
        """Get a list of all available packages."""
        packages_to_add = []
        
        for pkg in self.cache.getPackages():
            packages_to_add.append(self.formatPackage(pkg))
            
        return packages_to_add
    
    
    def getUpdatesList(self):
        """Get a list of all packages with a pending update."""
        packages_to_update = []
        
        trans = Transaction(self.cache, PolicyUpgrade)
        
        for pkg in self.cache.getPackages():
            if pkg.installed:
                trans.enqueue(pkg, UPGRADE)
        
        for pkg in trans._queue:   
            packages_to_update.append(self.formatPackage(pkg))
        
        return packages_to_update
    
    
    def install(self, pkg):
        """Install a package."""
        print "install"
        self.itrans.enqueue(pkg, INSTALL)
        self.iaction = True
        
        
    def update(self, pkg):
        """Update a package."""
        self.utrans.enqueue(pkg, UPGRADE)
        self.uaction = True
        
    
    def buildTransaction(self):
        """Build transaction"""
        if (self.uaction):
            self.utrans.run()
        if (self.iaction):
            self.itrans.run()
                
    
    def processTransaction(self):
        """Run transaction"""
        print "processTransaction"
        self.ctrl.commitTransaction(self.utrans, confirm=False)
        self.ctrl.commitTransaction(self.itrans, confirm=False)
        
    
    def search(self, name=None, epoch=None, ver=None, rel=None, arch=None):
        """Search for a package with the provided keys."""
        packages = []
        pkg = name + '-' + ver + '-' + rel + '@' + arch
        
        ratio, results, suggestions = self.ctrl.search(pkg, addprovides=False)
        if not results:
            return False
        else:
            for obj in results:
                if isinstance(obj, Package):
                    packages.append(obj)
        
        return packages
    
    
    def getKeys(self):
        """List updated/installed packages to send back to the server."""
        if (self.update.numTaskCompleted == 0) and (self.install.numTaskCompleted == 0):
            return None
        else:
            packages_updated = []          
            for pkg in self.update.getPersistentState:
                print "keys: " + pkg
                info = self.formatPackage(pkg).split(',')
                packages_updated.append("%s,%s,%s,%s" % (info[0], info[1], info[2], info[3]))
            return packages_updated
                  
    
    def formatPackage(self, pkg):
        """Helper function to correctly format package info"""
        info = pkg.version
            
        arch = info[info.find('@') + 1:]
        version = info[:info.find('-')]
        release = info[info.find('-') + 1:info.find('@')]
            
        channels = []
        for loader in pkg.loaders:
            channels.append(loader.getChannel().getAlias())
        channels.sort()
        
        return "%s,%s,%s,%s,%s" % (pkg.name, arch, version, release, channels[0])