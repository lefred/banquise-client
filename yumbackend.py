import yum
import sys

class Backend:

    def __init__(self):
        self.backend = yum.YumBase()
        #import ipdb; ipdb.set_trace()
        try:
            self.backend.doRepoSetup()
            yum.update_md.__name__
        except:
            print "Error: yum security plugin is not installed or not loaded !"
            sys.exit(1)


    def package_lists(self):
        packages_to_add = []

        ygh = self.backend.doPackageLists()
        old_repo = ""
        for children in ygh.available:
            if old_repo != str(children.repo):
                old_repo = str(children.repo)
                info = yum.update_md.UpdateMetadata((children.repo,))
            notice_update_id, notice_type, tup_update_id, tup_bug = \
            self.get_notice(children.pkgtup[0],
                           children.pkgtup[3],
                           children.pkgtup[4],
                           info)
            packages_to_add.append("%s,%s,%s,%s,%s,%s,%s" %
                                   (children.pkgtup[0],
                                    children.pkgtup[1],
                                    children.pkgtup[3],
                                    children.pkgtup[4],
                                    children.repo,
                                    notice_type,
                                    notice_update_id))

        return packages_to_add

    def get_change_log(self, name, arch, ver, rel):
        matches = self.search(name=name, arch=arch,
                              ver=ver, rel=rel)
        return matches[0].returnChangelog()


    def get_updates_list(self):
        packages_to_update = []
        metainfo_to_update = []
        metabug_to_update = []
        #changelog_to_update = []
        tup_update_id = {}

        self.backend.doRepoSetup()
        self.backend.doSackSetup()
        self.backend.doTsSetup()
        self.backend.doRpmDBSetup()
        old_repo = ""
        for children in self.backend.up.getUpdatesList():
            matches = self.search(name=children[0],
                                  arch=children[1],
                                  epoch=children[2],
                                  ver=children[3],
                                  rel=children[4])

            if old_repo != str(matches[0].repo):
                old_repo = str(matches[0].repo)
                info = yum.update_md.UpdateMetadata((matches[0].repo,))

            #tup_pack = (children[0], children[3], children[4])
            notice_update_id, notice_type, tup_update_id, tup_bug = \
                    self.get_notice(children[0], children[3], children[4], info)
            metainfo_to_update.append(tup_update_id)
            metabug_to_update.append(tup_bug)
            packages_to_update.append("%s,%s,%s,%s,%s,%s,%s" % (children[0],
                                                                children[1],
                                                                children[3],
                                                                children[4],
                                                                matches[0].repo,
                                                                notice_type,notice_update_id))

        return packages_to_update, metainfo_to_update, metabug_to_update

    def get_installed_list(self):
        packages_installed = []
        #metainfo_to_update = []
        #metabug_to_update = []

        self.backend.doRepoSetup()
        self.backend.doSackSetup()
        self.backend.doTsSetup()
        self.backend.doRpmDBSetup()

        #old_repo = ""

        for children in self.backend.doPackageLists("installed").installed:
            packages_installed.append("%s,%s,%s,%s,%s" % \
                                      (children.pkgtup[0],
                                       children.pkgtup[1],
                                       children.pkgtup[3],
                                       children.pkgtup[4],
                                       children.repo))
        return packages_installed

    def get_info(self, old_repo, repo, info=None):
        self.backend.doRepoSetup()
        if old_repo != repo:
            old_repo = repo
            repository = self.backend.repos.getRepo(repo)
            info = yum.update_md.UpdateMetadata((repository,))
        return info, old_repo

    def get_notice(self, package_name, package_version, package_release, info):
        tup_pack = (package_name, package_version, package_release)
        notice = info.get_notice(tup_pack)
        tup_update_id = {}
        tup_bug = None
        if notice:
            notice_type = notice.__getitem__('type')
            notice_update_id = notice.__getitem__('update_id')
            # TODO multiple bugs to add here
            tup_update_id[notice_update_id] = (notice.__getitem__('type'),
                                               notice.__getitem__('status'),
                                               notice.__getitem__('description'))
            tup_bug = (notice_update_id, notice.__getitem__('references'))
        else:
            notice_type = "normal"
            notice_update_id = "none"
        return notice_update_id, notice_type, tup_update_id, tup_bug

    def install(self, pobj):
        self.backend.install(pobj)


    def update(self, pobj):
        self.backend.update(pobj)


    def build_transaction(self):
        return self.backend.buildTransaction()


    def process_transaction(self):
        return self.backend.processTransaction()


    def search(self, name=None, epoch=None, ver=None, rel=None, arch=None):
        return self.backend.pkgSack.searchNevra(name, epoch, ver, rel, arch)


    def cleanup_list(self, field):
        if field:
            return [i for i in list(field) if i]
        else:
            return []

    def get_keys(self):
        myValues = self.backend.ts.ts.getKeys()
        if myValues == None:
            return None
        else:
            packages_updated = []
            for (hdr, path) in self.cleanup_list(myValues):
                print "%s - %s - %s - %s" % (hdr['name'],
                                             hdr['arch'],
                                             hdr['version'],
                                             hdr['release'])
                packages_updated.append("%s,%s,%s,%s" % \
                                        (hdr['name'],
                                         hdr['arch'],
                                         hdr['version'],
                                         hdr['release']))
            return packages_updated


    def set_proxy(self, proxy):
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
