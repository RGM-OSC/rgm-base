#!/bin/bash

# default string lenght is 32 chars
LEN="32"
CHARSET=

function print_usage () {
    cat <<EOF
generates a random string

usage: random.sh -l <str lenght> -h -a

  -l : output string lenght
  -h : output hexadecimal string
  -a : output string with all charset
  -c : sepcify your own charset (eg. 'a-z0-9')

EOF
    exit 1
}

while getopts l:c:ha arg; do
	case "$arg" in
		l) LEN="$OPTARG";;
		a) CHARSET='\055_.!#@a-zA-Z0-9';;
		h) CHARSET='a-f0-9';;
		c) CHARSET="$OPTARG";;
		*) print_usage;;
	esac
done

if [ -z $CHARSET ]; then
    print_usage
fi

if [ ! -z "$LEN" ]; then
    if [[ ! $LEN =~ [0-9]+ ]]; then
        print_usage
    fi
fi

if [ $LEN -lt 8 ]; then
    LEN=8
else
    if [ $LEN -gt 255 ]; then
        LEN=255
    fi
fi

STR=$(cat /dev/urandom | tr -dc "$CHARSET" | fold -w $LEN | head -n 1)
echo $STR
