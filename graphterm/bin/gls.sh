#!/bin/bash
# gls: a GraphTerm shell wrapper for the UNIX "ls" command
# Usage: gls

# TEMPORARY: Ignores all arguments except -f and last directory

options=""
dir=""
display="block"
for arg in $*; do
   if [ "$arg" == "-f" ]; then
      display="fullpage"
   elif [[ "$arg" == -* ]]; then
      options="$options $arg"
   else
      dir="$arg"
   fi
done

if [ "$dir" != "" ]; then
   cd $dir
fi

if [ "$options" != "" ]; then
    # Options encountered; default "ls" behaviour
    /bin/ls $*
    exit
fi

ncols=4

echocmd1="echo -n"
##echocmd1="/bin/echo -e"
echocmd2="echo"

rowimg=""
rowtxt=""

if [ -z $GRAPHTERM_PROMPT ]; then
   glscmd="~/meldr-hg/xmlterm/bin/gls"
   gvicmd="~/meldr-hg/xmlterm/bin/gvi"
else
   glscmd="gls"
   gvicmd="gvi"
fi

output=""
clickcmd="cd %(path); $glscmd -f"
files='.. . ~'
for file in $files; do
   fileicon="/static/images/tango-folder.png"
   filetype="specialfile"

   if [ "$file" == ".." ]; then
      fullpath=$(dirname "$PWD")
   elif [ "$file" == "." ]; then
      fullpath="$PWD"
   elif [ "$file" == '~' ]; then
      fullpath="$HOME"
   fi

   rowimg="${rowimg}<td><a class='gterm-link gterm-imglink' href='file://${fullpath}' data-gtermmime='x-graphterm/${filetype}' data-gtermcmd='${clickcmd}'><img class='gterm-img' src='$fileicon'></img></a>"

   rowtxt="${rowtxt}<td><a class='gterm-link' href='file://${fullpath}' data-gtermmime='x-graphterm/${filetype}' data-gtermcmd='${clickcmd}'>${file}</a>"

done

if [ "$rowtxt" != "" ]; then
   output="$output <tr class='gterm-rowimg'>$rowimg"
   output="$output <tr class='gterm-rowtxt'>$rowtxt"
   rowimg=""
   rowtxt=""
fi

ifile=0
for file in *; do
   fullpath="$PWD/$file"
   if [ -d "$file" ]; then       #directory
      filetype="directory"
      fileicon="/static/images/tango-folder.png"
      clickcmd="cd %(path); $glscmd -f"
   elif [ -x "$file" ]; then  #executable
      filetype="executable"
      fileicon="/static/images/tango-application-x-executable.png"
      clickcmd=""
   else                       #plain file
      filetype="plainfile"
      fileicon="/static/images/tango-text-x-generic.png"
      clickcmd="$gvicmd"
   fi

   rowimg="${rowimg}<td><a class='gterm-link gterm-imglink' href='file://${fullpath}' data-gtermmime='x-graphterm/${filetype}' data-gtermcmd='${clickcmd}'><img class='gterm-img' src='$fileicon'></img></a>"

   rowtxt="${rowtxt}<td><a class='gterm-link' href='file://${fullpath}' data-gtermmime='x-graphterm/${filetype}' data-gtermcmd='${clickcmd}'>${file}</a>"

   (( ifile++ ))

   if [ $(( ifile % ncols )) -eq 0 ]; then
      output="$output <tr class='gterm-rowimg'>$rowimg"
      output="$output <tr class='gterm-rowtxt'>$rowtxt"
      rowimg=""
      rowtxt=""
   fi

done

output="$output <tr class='gterm-rowimg'>$rowimg"
output="$output <tr class='gterm-rowtxt'>$rowtxt"

headers='{"content_type": "text/html", "x_gterm_response": "pagelet", "x_gterm_parameters": {"display": "'"${display}"'", "scroll": "top", "current_directory": "'"${PWD}"'"}}'

esc=`printf "\033"`
nl=`printf "\012"`
graphterm_code="1155"
$echocmd1 "${esc}[?${graphterm_code};${GRAPHTERM_COOKIE}h"

$echocmd1 "$headers"
$echocmd2 ""
$echocmd2 ""

$echocmd2 '<table frame=none border=0>'
$echocmd2 "<colgroup colspan=$ncols width=1*>"

$echocmd2 $output
$echocmd2 '</table>'
$echocmd1 "${esc}[?${graphterm_code}l"
echo
