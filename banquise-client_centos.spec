Name:		banquise-client
Version:	0.5
Release:	4%{?dist}
License:	GPLv3
Group:		System
Summary:	Client of banquise package system
URL:		http://www.lefred.be
Packager:	Frederic Descamps
Source0:	%{name}-%{version}.tgz
Source1:	banquise
Patch0:		%{name}-centos.patch
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:	noarch
Requires:	python, yum, python-hashlib, banquise-client-backend   

%description
Client part of the banquise project

%prep
%setup 
%patch0 

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/etc/cron.daily/
mkdir -p $RPM_BUILD_ROOT%{_bindir}/
cp %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/etc/cron.daily
cp banquise.py $RPM_BUILD_ROOT%{_bindir}/banquise
cp banquise.conf-example $RPM_BUILD_ROOT%{_sysconfdir}/banquise.conf


%clean
#rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_bindir}/*
%{_sysconfdir}/etc/cron.daily/banquise
%config(noreplace) %{_sysconfdir}/banquise.conf

%changelog
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
