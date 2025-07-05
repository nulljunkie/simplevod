#!/bin/bash
set -e

DIR="helm/app/tls"

openssl genrsa -out $DIR/ca.key 4096
openssl req -x509 -new -nodes -key $DIR/ca.key -sha256 -days 3650 \
  -out $DIR/ca.crt \
  -subj "/C=US/ST=SomeState/L=SomeCity/O=SimpleVOD/OU=Dev/CN=simplevod-CA"

openssl genrsa -out $DIR/simplevod.key 2048
openssl req -new -key $DIR/simplevod.key -out $DIR/simplevod.csr -config $DIR/san.cnf

openssl x509 -req -in $DIR/simplevod.csr -CA $DIR/ca.crt -CAkey $DIR/ca.key -CAcreateserial \
  -out $DIR/simplevod.crt -days 365 -sha256 -extfile $DIR/san.cnf -extensions v3_req

echo "Certificates generated in $DIR"
