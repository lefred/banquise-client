how to create the source archive to build the rpm :

git archive master --format tar --prefix banquise-client-0.5/ | gzip > ~/rpmbuild/SOURCES/banquise-client-0.5.tgz
