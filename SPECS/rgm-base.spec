Summary:   base RGM utilities
Name:      rgm-base
Version:   1.0
Release:   2.rgm
License:   GPL
BuildArch: noarch
URL:       %rgm_web_site
Vendor:    SCC
Packager:  ebelhomme@fr.scc.com

BuildRequires:  rpm-macros-rgm

Source: %name-%version.tar.gz

%description
Base package for common RGM utility scripts

%prep
%setup -q

%build


%install
install -Dp -m 0644 sql/manage_sql %{buildroot}%{_sysconfdir}/sysconfig/rgm/manage_sql
install -Dp -o root -g %{rgm_group} sql/manage_sql.sh %{buildroot}%{_datarootdir}/rgm/manage_sql.sh
install -Dp doc/readme.txt %{buildroot}%{_docdir}/rgm/readme.txt

%files
%{_sysconfdir}/sysconfig/rgm/*
%{_datarootdir}/rgm/*
%{_docdir}/rgm/*

%pre
# create RGM system group if it doesn't already exists
/usr/sbin/groupadd -r %{rgm_group} >/dev/null 2>&1 || :

%post

%changelog
* Wed Mar 20 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-2.rgm
- fix sql cnx timeout because for mysqld startup delay
- global rewrite of sql_manage.sh
- add the ability to override sql_manage config with /etc/sysconfig/rgm/sql_manage
- creates RGM group as this packages is marked as a dependency for almost
  all RGM packages

* Fri Mar 15 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-1.rgm
- update script to handle getopts arguments

* Wed Mar 13 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-0.rgm
- initial release
