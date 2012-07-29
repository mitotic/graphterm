#!/bin/csh

if ( $#argv < 1 ) then
   echo "Usage: create_server_cert.csh <hostname> [<serverorg> [<passwd>]]"
   exit 1
endif

set hostname=$1

set serverorg=GraphTerm
if ( $# > 1 ) then
    set serverorg="$3"
endif

set password=""
if ( $# > 2 ) then
    set password="$3"
endif

set expdays=1024

echo openssl genrsa -out $hostname.key 1024
openssl genrsa -out $hostname.key 1024

echo openssl req -new -key $hostname.key -out $hostname.csr -batch -subj "/O=$serverorg/CN=$hostname"
openssl req -new -key $hostname.key -out $hostname.csr -batch -subj "/O=$serverorg/CN=$hostname"

echo openssl x509 -req -days $expdays -in $hostname.csr -signkey $hostname.key -out $hostname.crt
openssl x509 -req -days $expdays -in $hostname.csr -signkey $hostname.key -out $hostname.crt

echo openssl x509 -noout -fingerprint -in $hostname.crt
openssl x509 -noout -fingerprint -in $hostname.crt

echo "Created $hostname.key, $hostname.crt"
