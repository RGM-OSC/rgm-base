Summary:   base RGM utilities
Name:      rgm-base
Version:   1.0
Release:   0.rgm
Copyright: GPL
#Group: Amusements/Graphics
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
URL:       %rgm_web_site
Vendor:    SCC
Packager:  ebelhomme@fr.scc.com
Provides:  %{name}

BuildRequires:  rpm-macros-rgm

%description
Base package for common RGM utility scripts

%prep
%setup -q

%build

%install
install -o root -g %{rgm_group} -d sql %{BuildRoot}%{_datarootdir}/rgm
install -d doc %{BuildRoot}%%{_docdir}/rgm

%files
%{_datarootdir}/rgm
%{_docdir}/rgm

%post

%changelog
* Wed Mar 13 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-0.rgm
- initial release
