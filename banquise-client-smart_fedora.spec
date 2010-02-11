Name:		banquise-client-smart
Version:	0.5
Release:	1%{?dist}
License:	GPLv3
Group:		System
Summary:	Client smart backend of banquise package system
URL:		http://www.lefred.be
Packager:	Frederic Descamps
Source0:	%{name}-%{version}.tgz
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:	noarch
Requires:	python, banquise-client, smart
Provides:	banquise-client-backend   

%description
Smart Backend for client part of the banquise project

%prep
%setup 

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/banquise/
#mkdir -p $RPM_BUILD_ROOT/%{_defaultdocdir}/%{name}-%{version}/
cp smartbackend.py $RPM_BUILD_ROOT/%{_datadir}/banquise/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_datadir}/banquise/*

%changelog
* Thu Feb 11 2010 - Frederic Descamps <lefred@inuits.be> 0.5-1 
- Initial build
