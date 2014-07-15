#!/bin/bash
# gimg.sh: display PNG file inline

esc=`printf "\033"`
gterm_code="1155"
gterm_cookie=${GTERM_COOKIE:-${LC_GTERM_COOKIE}}

# Display image
blob_id="${RANDOM}${RANDOM}"
echo -n "${esc}[?${gterm_code};${gterm_cookie}h"
echo -n '<!--gterm data-->image/png;base64,'
base64 $1
echo -n "${esc}[?${gterm_code}l"
