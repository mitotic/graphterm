#!/bin/csh

if ( $#argv < 2 ) then
   echo "Usage: create_client_cert.csh <certfile> <clientname> [<clientorg> [<passwd>]]"
   exit 1
endif

set clientorg=GraphTerm
if ( $# > 2 ) then
    set clientorg="$3"
endif

set password=""
if ( $# > 3 ) then
    set password="$4"
endif

set certfile=$1
set certprefix=$certfile:r

set clientname=$2
set clientprefix="${certprefix:t}-$clientname"

set expdays=1024

echo openssl genrsa -out $clientprefix.key 1024
openssl genrsa -out $clientprefix.key 1024

echo openssl req -new -key $clientprefix.key -out $clientprefix.csr -batch -subj "/O=$clientorg/CN=$clientname"
openssl req -new -key $clientprefix.key -out $clientprefix.csr -batch -subj "/O=$clientorg/CN=$clientname"

echo openssl x509 -req -days $expdays -in $clientprefix.csr -CA $certprefix.crt -CAkey $certprefix.key -set_serial 01 -out $clientprefix.crt
openssl x509 -req -days $expdays -in $clientprefix.csr -CA $certprefix.crt -CAkey $certprefix.key -set_serial 01 -out $clientprefix.crt

echo openssl pkcs12 -export -in $clientprefix.crt -inkey $clientprefix.key -out $clientprefix.p12 -passout pass:$password
openssl pkcs12 -export -in $clientprefix.crt -inkey $clientprefix.key -out $clientprefix.p12 -passout pass:$password

echo "Created $clientprefix.key, $clientprefix.crt, $clientprefix.p12"
