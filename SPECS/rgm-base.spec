Name:       rgm-base
Version:    1.0
Release:    0.rgm
Summary:    base RGM utilities
License:    GPL
BuildArch:  noarch
Packager:   Eric Belhomme <ebelhomme@fr.scc.com>
URL:        %rgm_web_site

Source: %{name}-%{version}.tar.gz

BuildRequires: rpm-macros-rgm

%description
Base package for common RGM utility scripts

%prep
%setup -q

%build

%install
install -o root -g %{rgm_group} -d sql %{_datarootdir}/rgm
install -d doc %{_docdir}/rgm

%files
%{_datarootdir}/rgm
%{_docdir}/rgm

%post

%changelog
* Wed Mar 13 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 1.0-0.rgm
- initial release
