Name:       rgm-base
Version:    1.0
Release:    0.rgm
Summary:    base RGM utilities
License:    GPL
BuildArch:  noarch
Packager:   Eric Belhomme <ebelhomme@fr.scc.com>
URL:        %rgm_web_site
Source0:    sql/manage_sql.sh
Source1:    doc/readme.txt

%description
Base package for common RGM utility scripts

%prep

%build

%install
rm -rf %{buildroot}

install -o root -g %{rgm_group} %{SOURCE0} %{_datarootdir}/rgm/sql
install %{SOURCE1} %{_docdir}/rgm

%files
%{_datarootdir}/rgm
%{_docdir}/rgm

%post

%changelog
* Wed Mar 13 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-0.rgm
- initial release
