#!/bin/bash
# A Hello World program using the GraphTerm API

prefix=https://raw.github.com/mitotic/graphterm
url=$prefix/master/graphterm/www/GTYY500.png
esc=`printf "\033"`
code="1155"
# Prefix escape sequence
echo "${esc}[?${code};${GRAPHTERM_COOKIE}h"
# Display text with HTML markup
echo '<b>Hello</b>'
echo '<b style="color: red;">World!</b><p>'
# Display inline image
echo "<a><img width="200" src=\"$url\"></a>"
# Suffix escape sequence
echo "${esc}[?${code}l"
