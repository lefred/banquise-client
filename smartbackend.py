from smart import init, initDistro, initPlugins, initPsyco
from smart.commands import *
from smart.transaction import *
from smart import *

class Backend:

    def __init__(self):
        self.ctrl = init()
        initDistro(self.ctrl)
        initPlugins()
        initPsyco()
        self.ctrl.reloadChannels()
        self.cache = self.ctrl.getCache()
        self.trans = Transaction(self.cache, PolicyInstall)


    def package_lists(self):
        """Get a list of all available packages."""
        packages_to_add = []

        for pkg in self.cache.getPackages():
            packages_to_add.append(self.format_package(pkg))

        return packages_to_add


    def get_change_log(self, name, arch, ver, rel):
        self.search(name=name, arch=arch,
                    ver=ver, rel=rel)
        return []


    def get_updates_list(self):
        """Get a list of all packages with a pending update."""
        packages_to_update = []
        metainfo_to_update = []
        metabug_to_update = []

        trans = Transaction(self.cache, PolicyUpgrade)

        for pkg in self.cache.getPackages():
            if pkg.installed:
                trans.enqueue(pkg, UPGRADE)

        for pkg in trans._queue:
            packages_to_update.append(self.format_package(pkg))

        return packages_to_update, metainfo_to_update, metabug_to_update


    def get_installed_list(self):
        """Get a list of all installed packages."""
        packages_installed = []

        for pkg in self.cache.getPackages():
            if pkg.installed:
                packages_installed.append(self.format_package(pkg))

        return packages_installed


    def install(self, pkg):
        """Install a package."""
        self.trans.enqueue(pkg, INSTALL)


    def update(self, pkg):
        """Update a package."""
        self.trans.enqueue(pkg, INSTALL)


    def build_transaction(self):
        """Build transaction"""
        self.trans.run()


    def process_transaction(self):
        """Run transaction"""
        self.ctrl.commitTransaction(self.trans, confirm=False)


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


    def get_keys(self):
        """List updated/installed packages to send back to the server."""
        if (self.trans.numTaskCompleted == 0):
            return None
        else:
            packages_updated = []
            for pkg in self.trans.getChangeSet().getPersistentState():
                ratio, results, suggestions =  self.ctrl.search( \
                                               pkg[1] + "-" + pkg[2], 
                                               addprovides=False)
                if not results:
                    return False
                else:
                    for obj in results:
                        if isinstance(obj, Package):
                            pkginfo = self.format_package(obj).split(',')
                packages_updated.append("%s,%s,%s,%s" % (pkginfo[0], 
                                                         pkginfo[1], 
                                                         pkginfo[2], 
                                                         pkginfo[3]))

            return packages_updated


    def format_package(self, pkg):
        """Helper function to correctly format package info"""
        seen = {}
        info = pkg.version

        arch = info[info.find('@') + 1:]
        version = info[:info.find('-')]
        release = info[info.find('-') + 1:info.find('@')]

        channels = []
        for loader in pkg.loaders:
            channels.append(loader.getChannel().getAlias())
            if loader not in seen:
                seen[loader] = True
                errata = loader.getErrata(pkg)
                if errata:
                    print "   ", _("Type:"), errata.getType()
        channels.sort()

        return "%s,%s,%s,%s,%s,%s,%s" % (pkg.name,
                                         arch,
                                         version,
                                         release,
                                         channels[0],
                                         '',
                                         '')


    def set_proxy(self, proxy):
        """Set proxy"""
        sysconf.set("http-proxy", proxy)
