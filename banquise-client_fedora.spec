Name:		banquise-client
Version:	0.5
Release:	1%{?dist}
License:	GPLv3
Group:		System
Summary:	Client of banquise package system
URL:		http://www.lefred.be
Packager:	Frederic Descamps
Source0:	%{name}-%{version}.tgz
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:	noarch
Requires:	python, yum, banquise-client-backend   

%description
Client part of the banquise project

%prep
%setup 

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/
mkdir -p $RPM_BUILD_ROOT%{_bindir}/
#mkdir -p $RPM_BUILD_ROOT/%{_defaultdocdir}/%{name}-%{version}/
cp banquise.py $RPM_BUILD_ROOT%{_bindir}/banquise
cp banquise.conf-example $RPM_BUILD_ROOT%{_sysconfdir}/banquise.conf


%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_bindir}/*
%{_sysconfdir}/*

%changelog
* Thu Feb 11 2010 - Frederic Descamps <lefred@inuits.be> 0.5-1 
- version 0.5-1 first test release of 0.5
* Tue Jan 11 2010 - Frederic Descamps <lefred@inuits.be> 0.4-2 
- version 0.4-2 fixing a typo
* Mon Jan 11 2010 - Frederic Descamps <lefred@inuits.be> 0.4-1 
- version 0.4 of the client adding install and repo
* Sun Jan 10 2010 - Frederic Descamps <lefred@inuits.be> 0.3-1 
- version 0.3 of the client
* Wed Jan 06 2010 - Frederic Descamps <lefred@inuits.be> 0.1-1 
- Initial build