Summary:   base RGM utilities
Name:      rgm-base
Version:   1.0
Release:   21.rgm
License:   GPL
BuildArch: noarch
URL:       %rgm_web_site
Vendor:    SCC
Packager:  ebelhomme@fr.scc.com

Requires: python36
Requires: python36-mysql
Requires: restic

BuildRequires: rpm-macros-rgm
BuildRequires: python3-devel
#BuildRequires: python3
#BuildRequires: python3-libs
#BuildRequires: python3-setuptools
#BuildRequires: python36-mysql

Source: %{name}.tar.gz

# force rpmbuild to byte-compile using Python3
%global __python %{__python3}

%description
Base package for common RGM utility scripts

%prep
%setup -q -n %{name}

%build


%install
install -Dp -m 0754 -o root -g root migration/rgm_migrator_lilac.py %{buildroot}%{_sbindir}/rgm-lilac-migrator
install -Dp -m 0754 -o root -g %{rgm_group} sql/lilac_inspect.sh %{buildroot}%{_sbindir}/rgm-lilac-inspect
install -Dp -m 0754 -o root -g %{rgm_group} sql/lilac_manage_auto_increments.sh %{buildroot}%{_sbindir}/rgm-lilac-manage-auto-increments
install -Dp -m 0754 -o root -g %{rgm_group} backup/rgm-restic %{buildroot}%{_bindir}/rgm-restic

install -Dp -m 0644 sql/manage_sql %{buildroot}%{_sysconfdir}/sysconfig/rgm/manage_sql
install -Dp -o root -g %{rgm_group} sql/manage_sql.sh %{buildroot}%{_datarootdir}/rgm/manage_sql.sh
install -Dp -o root -g %{rgm_group} tools/random.sh %{buildroot}%{_datarootdir}/rgm/random.sh
install -Dp doc/readme.txt %{buildroot}%{_docdir}/rgm/readme.txt
# RGM Business
install -Dp -o root -g %{rgm_group} tools/rgm-business.sh %{buildroot}%{_sbindir}/rgm-business
# RGM backup
#install -m 0750 -o %{rgm_user_nagios} -g %{rgm_group} -d %{buildroot}%{rgm_path}/backup
#install -m 0750 -o %{rgm_user_nagios} -g %{rgm_group} -d %{buildroot}%{rgm_path}/backup/bin
install -Dp -m 0750 -o root -g %{rgm_group} backup/rgm-backup.sh %{buildroot}%{rgm_path}/backup/bin/rgm-backup.sh
install -Dp -m 0640 -o root -g %{rgm_group} backup/environment %{buildroot}%{rgm_path}/backup/environment
install -Dp -m 0640 -o root -g %{rgm_group} backup/include %{buildroot}%{_sysconfdir}/rgm/backup/include
install -Dp -m 0640 -o root -g %{rgm_group} backup/exclude %{buildroot}%{_sysconfdir}/rgm/backup/exclude
install -Dp -m 0644 backup/rgmbackup.cron  %{buildroot}%{_sysconfdir}/cron.d/rgm_backup
install -Dp -m 0644 backup/rgm-restic.completion %{buildroot}%{_datarootdir}/bash-completion/completions/rgm-restic


%files
%attr(0750,root,%{rgm_group}) %{_sbindir}/rgm-lilac-migrator
%attr(0754,root,%{rgm_group}) %{_sbindir}/rgm-lilac-inspect
%attr(0754,root,%{rgm_group}) %{_sbindir}/rgm-lilac-manage-auto-increments
%attr(0754,root,%{rgm_group}) %{_sbindir}/rgm-business
%attr(0754,root,%{rgm_group}) %{_bindir}/rgm-restic
%{_datarootdir}/bash-completion/completions/rgm-restic
%{_sysconfdir}/sysconfig/rgm/*
%{_datarootdir}/rgm/*
%{_docdir}/rgm/*
%attr(0750,root,%{rgm_group}) %{rgm_path}/backup/bin/*
%attr(0660,root,%{rgm_group}) %{rgm_path}/backup/environment
%config(noreplace) %{_sysconfdir}/cron.d/rgm_backup
%config(noreplace) %attr(0664,root, %{rgm_group}) %{_sysconfdir}/rgm/backup/include
%config(noreplace) %attr(0664,root, %{rgm_group}) %{_sysconfdir}/rgm/backup/exclude


%pre
# create RGM system group if it doesn't already exists
/usr/sbin/groupadd -r %{rgm_group} >/dev/null 2>&1 || :

%post

%changelog
* Fri Jan 6 2023 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-21.rgm
- add --core arg on rgm-lilac-manage-auto-increments

* Fri Oct 29 2021 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-20.rgm
- fix rgm backups getting full by adding a dummy file to avoid restic to getting the FS full

* Tue Aug 24 2021 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-19.rgm
- introduce rgm-business activation helper

* Wed Jul 28 2021 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-18.rgm
- enhance restic backup

* Mon Jul 26 2021 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-17.rgm
- move executables to system sbin dir, and prefix all with 'rgm-'
- add restic helper

* Fri Oct 30 2020 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-16.rgm
- add rgm backup

* Thu Jan 16 2020 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-15.rgm
- add lilac_repair.py: a tool for Lilac DB maintenance

* Mon Jan 13 2020 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-14.rgm
- add lilac_rgm_upgrade.py: a tool for upgrading RGM core records on Lilac DB

* Thu Jan 09 2020 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-13.rgm
- Ansible git repos now on Github
- add MySQL backup feature on rgmupdate

* Wed Dec 18 2019 Michael Aubertin <maubertin@fr.scc.com> - 1.0-12.rgm
- Apply Vincent Fricou patch

* Fri Dec 06 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-11.rgm
- add rgm_migrator_lilac script

* Thu Oct 03 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-10.rgm
- update rgmupdate with updated Git repo URL, and new branching policy

* Wed Sep 18 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-9.rgm
- add -o option on rgmupdate

* Thu Sep 12 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-8.rgm
- fix return code for manage_sql.sh script

* Thu Jun 13 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-7.rgm
- update rgm update to handle Git retrieval of roles

* Mon May 06 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-6.rgm
- introduce random.sh command

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
