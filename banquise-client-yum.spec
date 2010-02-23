Name:		banquise-client-yum
Version:	0.5
Release:	5%{?dist}
License:	GPLv3
Group:		System
Summary:	Client yum backend of banquise package system
URL:		http://www.lefred.be
Packager:	Frederic Descamps
Source0:	%{name}-%{version}.tgz
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:	noarch
Requires:	python, yum, banquise-client
Provides:	banquise-client-backend   

%description
Yum Backend for client part of the banquise project

%prep
%setup 

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/banquise/
cp yumbackend.py $RPM_BUILD_ROOT/%{_datadir}/banquise/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_datadir}/banquise/*

%changelog
* Tue Feb 23 2010 - Frederic Descamps <lefred@inuits.be> 0.5-5
- version 0.5-5 metabug info added and memory usage optimized
* Thu Feb 18 2010 - Frederic Descamps <lefred@inuits.be> 0.5-4
- version 0.5-4 adding metadata and sync release number with server
* Thu Feb 11 2010 - Frederic Descamps <lefred@inuits.be> 0.5-1 
- Initial build
