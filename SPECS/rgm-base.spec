Summary:   base RGM utilities
Name:      rgm-base
Version:   1.0
Release:   6.rgm
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
install -Dp -o root -g root tools/rgmupdate %{buildroot}%{_sbindir}/rgmupdate
install -Dp -m 0644 sql/manage_sql %{buildroot}%{_sysconfdir}/sysconfig/rgm/manage_sql
install -Dp -o root -g %{rgm_group} sql/manage_sql.sh %{buildroot}%{_datarootdir}/rgm/manage_sql.sh
install -Dp -o root -g %{rgm_group} sql/lilac_dumper.sh %{buildroot}%{_datarootdir}/rgm/lilac_dumper.sh
install -Dp -o root -g %{rgm_group} sql/lilac_inspect.sh %{buildroot}%{_datarootdir}/rgm/lilac_inspect.sh
install -Dp -o root -g %{rgm_group} sql/lilac_manage_auto_increments.sh %{buildroot}%{_datarootdir}/rgm/lilac_manage_auto_increments.sh
install -Dp doc/readme.txt %{buildroot}%{_docdir}/rgm/readme.txt

%files
%attr(0540,root,root) %{_sbindir}/rgmupdate
%{_sysconfdir}/sysconfig/rgm/*
%{_datarootdir}/rgm/*
%{_docdir}/rgm/*

%pre
# create RGM system group if it doesn't already exists
/usr/sbin/groupadd -r %{rgm_group} >/dev/null 2>&1 || :

%post

%changelog
* Fri May 03 2019 Michael Aubertin <maubertin@fr.scc.com> - 1.0-5.rgm
- Fix minor loglevel issue

* Thu Apr 25 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-5.rgm
- add feature on manage-sql.sh script (-a opption)
- bug fix on lilac_* scripts (autoconfig issue after lilac 3 upgrade)

* Fri Apr 19 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-4.rgm
- introduce rgmupdate command

* Thu Mar 28 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-3.rgm
- add Lilac management scripts

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
