#!/bin/csh

if ( $#argv < 2 ) then
   echo "Usage: cert_to_p12.csh <certfile> <keyfile> <password>"
   exit 1
endif

set password=password
if ( $# > 2 ) then
    set password=$3
endif

set name=$1:t
set name=$name:r

echo openssl pkcs12 -export -in $1 -inkey $2 -out $name.p12 -passout pass:$password
openssl pkcs12 -export -in $1 -inkey $2 -out $name.p12 -passout pass:$password
