Summary:   base RGM utilities
Name:      rgm-base
Version:   1.0
Release:   0.rgm
License:   GPL
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
URL:       %rgm_web_site
Vendor:    SCC
Packager:  ebelhomme@fr.scc.com

BuildRequires:  rpm-macros-rgm

Source0: doc/readme.txt
Source1: sql/manage_sql.sh

%description
Base package for common RGM utility scripts

%prep
%setup -c -T

%build

%install
install -Dp -o root -g %{rgm_group} %{SOURCE1} %{BuildRoot}%{_datarootdir}/rgm/%{SOURCE1}
install -Dp %{SOURCE0} %{BuildRoot}%%{_docdir}/rgm/%{SOURCE0}

%files
%{_datarootdir}/rgm
%{_docdir}/rgm

%post

%changelog
* Wed Mar 13 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-0.rgm
- initial release
