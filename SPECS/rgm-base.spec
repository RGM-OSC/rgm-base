Summary:   base RGM utilities
Name:      rgm-base
Version:   1.0
Release:   1.rgm
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
install -Dp -o root -g %{rgm_group} sql/manage_sql.sh %{buildroot}%{_datarootdir}/rgm/manage_sql.sh
install -Dp doc/readme.txt %{buildroot}%{_docdir}/rgm/readme.txt

%files
%{_datarootdir}/rgm/*
%{_docdir}/rgm/*

%post

%changelog
* Fri Mar 15 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-1.rgm
- update script to handle getopts arguments

* Wed Mar 13 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-0.rgm
- initial release
