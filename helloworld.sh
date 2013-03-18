#!/bin/bash
# helloworld.sh: a Hello World program illustrating GraphTerm escape sequences

imgurl=https://github.com/mitotic/graphterm/raw/master/doc-images/helloworld1.png

esc=`printf "\033"`
graphterm_code="1155"
echo -n "${esc}[?${graphterm_code};${GRAPHTERM_COOKIE}h"

# Display text with markup
echo '<b>Hello</b> <em style="color: red;">World!</em><p>'

# Display inline image
echo '<a href="https://github.com/mitotic/graphterm" target="_blank">'
echo '<img width="400" height="200" src="'$imgurl'"></img>'
echo '</a>'

echo -n "${esc}[?${graphterm_code}l"
