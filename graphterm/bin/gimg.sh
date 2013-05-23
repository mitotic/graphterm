#!/bin/bash
# gimg.sh: display PNG file inline

esc=`printf "\033"`
gterm_code="1155"
gterm_cookie=${GTERM_COOKIE:-${LC_GTERM_COOKIE}}

# Create blob
blob_id="${RANDOM}${RANDOM}"
echo -n "${esc}[?${gterm_code};${gterm_cookie}h"
echo -n '<!--gterm data blob='${blob_id}'-->image/png;base64,'
base64 $1
echo -n "${esc}[?${gterm_code}l"

# Display blob
echo -n "${esc}[?${gterm_code};${gterm_cookie}h"
echo -n '<!--gterm pagelet display-block blob='${blob_id}'--><div class="gterm-blockhtml"><img class="gterm-blockimg" src="/_blob/local/'${blob_id}'"></div>'
echo -n "${esc}[?${gterm_code}l"

