Name:		banquise-client
Version:	0.5
Release:	8%{?dist}
License:	GPLv3
Group:		System
Summary:	Client of banquise package system
URL:		http://www.banquise.be
Packager:	Frederic Descamps
Source0:	%{name}-%{version}.tgz
Source1:	banquise
Patch0:		%{name}-centos.patch
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:	noarch

%description
Client part of the banquise project

%package 	core
Summary:	Client backend of banquise package system
Requires:	python, yum, banquise-client-backend   
%if 0%{?fedora} > 1
%else
Requires:	python-hashlib, python-simplejson  
%endif
Group:		System

%description    core
Client core backend part of the banquise project

%package	yum
Summary:	Client yum backend of banquise package system
Requires:       python, yum, banquise-client-core
%if 0%{?fedora} > 1
Requires:	 yum-plugin-security
%else
Requires:	 yum-security
%endif
Provides:       banquise-client-backend
Group:		System

%description	yum
Client yum backend part of the banquise project

%package	smart
Summary:	Client smart backend of banquise package system
Requires:       python, smart, banquise-client-core
Provides:       banquise-client-backend
Group:		System

%description	smart
Client smart backend part of the banquise project


%prep
%setup 
%if 0%{?fedora}  > 1
echo IN FEDORA %{fedora}
%else
echo NOT IN FEDORA 
%patch0 
%endif

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/cron.daily/
mkdir -p $RPM_BUILD_ROOT%{_bindir}/
cp %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/cron.daily
cp banquise.py $RPM_BUILD_ROOT%{_bindir}/banquise
cp banquise.conf-example $RPM_BUILD_ROOT%{_sysconfdir}/banquise.conf

mkdir -p $RPM_BUILD_ROOT/%{_datadir}/banquise/
cp yumbackend.py $RPM_BUILD_ROOT/%{_datadir}/banquise/
cp smartbackend.py $RPM_BUILD_ROOT/%{_datadir}/banquise/




%clean
#rm -rf $RPM_BUILD_ROOT

%files core
%defattr(-,root,root,-)
%{_bindir}/*
%{_sysconfdir}/cron.daily/banquise
%config(noreplace) %{_sysconfdir}/banquise.conf

%files yum
%defattr(-,root,root,-)
%{_datadir}/banquise/yum*

%files smart
%defattr(-,root,root,-)
%{_datadir}/banquise/smart*

%changelog
* Mon Nov 15 2010 - Frederic Descamps <lefred.descamps@gmail.com> 0.5-7
- version 0.5-7 new rpms
* Tue Feb 23 2010 - Frederic Descamps <lefred@inuits.be> 0.5-5
- version 0.5-5 metabug info added and memory usage optimized
* Thu Feb 18 2010 - Frederic Descamps <lefred@inuits.be> 0.5-4
- version 0.5-4 adding a cronjob, adding metadata and sync release number with
  server
* Thu Feb 11 2010 - Frederic Descamps <lefred@inuits.be> 0.5-1
- version 0.5-1 first test release of 0.5
* Tue Jan 12 2010 - Frederic Descamps <lefred@inuits.be> 0.4-2 
- version 0.4 of the client but to run on centos
* Mon Jan 11 2010 - Frederic Descamps <lefred@inuits.be> 0.4-1 
- version 0.4 of the client adding install and repo
* Sun Jan 10 2010 - Frederic Descamps <lefred@inuits.be> 0.3-1 
- version 0.3 of the client
* Wed Jan 06 2010 - Frederic Descamps <lefred@inuits.be> 0.1-1 
- Initial build
