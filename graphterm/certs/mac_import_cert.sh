#!/bin/sh

if [ $# -eq 0 ]; then
   echo "Usage: mac_import_cert.sh <cert_file> [clientname]"
   exit 1
fi

certfile=$1
clientname=gterm-local
if [ $# -gt 1 ]; then
   clientname=$2
fi

keychain=$HOME/Library/Keychains/login.keychain

if security find-certificate -c $clientname; then
   security delete-certificate -c $clientname
fi

echo security import $certfile -k $keychain -P password
security import $certfile -k $keychain -P password
