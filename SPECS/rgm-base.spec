Name:       rgm-base
Version:    1.0
Release:    0.rgm
Summary:    base RGM utilities
License:    GPL
Source:     %{name}-%{version}.tar.gz

Packager:   Eric Belhomme <ebelhomme@fr.scc.com>
URL:        %rgm_web_site

BuildRequires:  rpm-macros-rgm
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root

###%package -n rpm-macros-rgm
BuildArch:      noarch


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
