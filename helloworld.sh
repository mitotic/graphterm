#!/bin/bash
# helloworld.sh: a Hello World program illustrating GraphTerm escape sequences

imgurl=https://github.com/mitotic/graphterm/raw/master/doc-images/helloworld1.png

esc=`printf "\033"`
gterm_code="1155"
gterm_cookie=${GRAPHTERM_COOKIE:-${LC_GRAPHTERM_COOKIE}}
echo -n "${esc}[?${gterm_code};${gterm_cookie}h"

# Display text with markup
echo '<b>Hello</b> <em style="color: red;">World!</em><p>'

# Display inline image
echo '<a href="https://github.com/mitotic/graphterm" target="_blank">'
echo '<img width="400" height="200" src="'$imgurl'"></img>'
echo '</a>'

echo -n "${esc}[?${gterm_code}l"
