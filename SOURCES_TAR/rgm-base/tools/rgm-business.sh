#!/bin/bash
#
# RGM business activation helper
#
# Copyright 2021 & onwards, SCC France

_help() {
    cat <<EOF

    $(basename $0) - RGM Business activation helper

    This tool helps enabling RGM Business mode by installing RGM customer certificate
    and activating Business repositories.

    Usage: $(basename $0) <PKCS#12 file>

EOF
    if [ -n "$1" ]; then
        echo "$1"
    fi
    exit 1
}

if [ "$UID" -ne 0 ]; then
    echo "Error: must run as root user"
    exit 1
fi
if [ -z "$1" ]; then _help "Error: No PKCS#12 file provided"; fi
if [ ! -e "$1" ]; then _help "Fatal: Unable to access PKCS#12 input file"; fi

while true; do
    echo -e "\nPlease provide PKCS#12 passphrase : "; read -rs P12PASS
    openssl pkcs12 -in "$1" -password "pass:${P12PASS}" -info -nokeys -noout &> /dev/null
    if [ $? -eq 0 ]; then
        break
    fi
    echo -e "Error: unable to unlock PKCS#12 file with that passphrase\n"
done

# extracts x509 cert & RSA private key from PKCS#12 container
TEMPDIR="$(mktemp -d)"
openssl pkcs12 -in "$1" -password "pass:${P12PASS}" -nodes -nokeys -cacerts -out /etc/pki/tls/certs/rgm-full.pem
openssl pkcs12 -in "$1" -password "pass:${P12PASS}" -nodes -nokeys -clcerts -out "${TEMPDIR}/client.pem"
COMMON_NAME=$(openssl x509 -in "${TEMPDIR}/client.pem" -noout -subject | sed -E 's~.*/CN=(.+)(/.*)|$~\1~')
mv "${TEMPDIR}/client.pem" "/etc/pki/tls/certs/${COMMON_NAME}.crt"
openssl pkcs12 -in "$1" -password "pass:${P12PASS}" -nodes -nocerts -out "/etc/pki/tls/private/${COMMON_NAME}.key"
chmod 0664 /etc/pki/tls/certs/noc-rgm.pem "/etc/pki/tls/certs/${COMMON_NAME}.crt"
chmod 0440 "/etc/pki/tls/private/${COMMON_NAME}.key"
rm -Rf "$TEMPDIR"
# split x509 CA certs from CA full-chain in system trusted certificates
awk 'split_after==1{n++;split_after=0} /-----END CERTIFICATE-----/ {split_after=1} {print > "/tmp/rgmpki" n ".pem"}' /etc/pki/tls/certs/rgm-full.pem
for cert in $(ls -1 /tmp/rgmpki*pem); do
    subject="$(openssl x509 -in "$cert" -noout -subject | sed -E 's|.*CN=(.*)/.*|\1|' | tr ' ' _ | tr '[:upper:]' '[:lower:]')"
    cp "$cert" "/etc/pki/ca-trust/source/anchors/${subject}.crt"
done
rm -f /tmp/rgmpki*pem
update-ca-trust
update-ca-trust extract

set -e

# enable RGM Business for Ansible playbook
if grep 'rgm_business_registration_id:' /etc/rgm/ansible/localhost.yml &> /dev/null; then
    sed -i "s|^\(#\s*\)*rgm_business_registration_id:.*$|rgm_business_registration_id: '${COMMON_NAME}'|" /etc/rgm/ansible/localhost.yml
else
    echo "rgm_business_registration_id: '${COMMON_NAME}'" >> /etc/rgm/ansible/localhost.yml
fi

# reconfigure Yum to activate rgm-business repositories
cd /root/rgm-installer
ansible-playbook rgm-installer.yml -t packages

# eventually install rgm-business-base package
yum install -y rgm-business-base

exit $?