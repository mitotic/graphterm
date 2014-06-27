// GraphTerm Page Commands

// CONVENTION: All pre-defined GraphTerm Javascript functions and global
//             variables should begin with an upper-case letter.
//             This would allow them to be easily distinguished from
//             user defined functions, which should begin with a lower case
//             letter.


// Global variables

var gUserAgent = navigator.userAgent.toLowerCase();
var gFirefoxBrowser = gUserAgent.indexOf('firefox') > -1;
var gWebkitBrowser = gUserAgent.indexOf('webkit') > -1;
var gChromeBrowser = gUserAgent.indexOf('chrome') > -1;
var gSafariBrowser = !gChromeBrowser && gUserAgent.indexOf('safari') > -1;
var gIExplorer = gUserAgent.indexOf("msie") > -1;  // Will not detect IE11, which behaves like WebKit
var gAndroid = gUserAgent.indexOf("android") > -1;
var gWinBrowser = gUserAgent.indexOf("windows") > -1;

var gTouchBrowser = gUserAgent.indexOf("touch") > -1  || 'ontouchstart' in window;

var gMobileBrowser = gWinBrowser ? (gUserAgent.indexOf("mobile") > -1 || gUserAgent.indexOf("arm;") > -1) : (gUserAgent.indexOf("mobile") > -1 || gAndroid || gTouchBrowser);

var gSafariIPad = gSafariBrowser && gUserAgent.indexOf('ipad') > -1;

var gWinPlatform = _.str.startsWith(window.navigator.platform, "Win") || _.str.startsWith(window.navigator.platform, "WOW");
var gMacPlatform = _.str.startsWith(window.navigator.platform, "Mac");

var gDefaultEditor = gMobileBrowser ? "ckeditor" : "ace";

var gAltPasteImpl = !gMobileBrowser;  // Alternative paste implemention (using hidden textarea)
var gPasteDebug = false;
var gPasteActive = false;

var gPasteSpecialKeycode = 15;  // Control-O shortcut for Paste Special

var MAX_LINE_BUFFER = 500;
var MAX_COMMAND_BUFFER = 100;

var REPEAT_MILLISEC = 500;
var POLL_SEC = 1.0;

var RELEASE_NOTES_URL = "http://code.mindmeldr.com/graphterm/release-notes.html";
var PYPI_URL = "http://pypi.python.org/pypi/graphterm";
var PYPI_JSON_URL = PYPI_URL + "/json?callback=?";

var WRITE_LOG = function (str) {};
var DEBUG_LOG = function (str) {};
var DEBUG_LOG = function (str) {console.log(str)};

var OSH_ECHO = true;

var ELLIPSIS = "...";
var HIDDEN_STR = "##Hidden";

var gRowHeight = 16;
var gColWidth  = 8;
var gBottomMargin = 14;

var gRows = 0;
var gCols = 0;
var gWebSocket = null;

var gAuthenticatingCookie = "";
var gAuthParams = null;
var gEditing = null;

var gChat = false;

var gScriptBuffer = [];

var gForm = null;
var gFormIndex = null;

var gExpectUpload = null
var gUploadFile = null;

var gControlQ = false;
var gShortcutMenus = null;
var gDebug = true;
var gDebugKeys = false;
var gDebugMessages = false;

var gTypeAhead = false;   // Does not work very well

var gAlwaysSplitScreen = gMobileBrowser;
var gSplitScreen = false;
var gShowingFinder = false;

var gDelayedPageExit = false;

var gShowingSplash = false;
var gAnimatingSplash = false;
var gProgrammaticScroll = false;
var gManualScroll = false;
var gMaxScrollOffset = 0;

var gTestBatchedScroll = false;   // TEMPORARY (for testing batched programmatic scrolling)

var gEntryIndex = 0;
var gCommandId = null;
var gCommandPrefix = "command";
var gCommandMatchIndex = null;
var gCommandMatchPrev = null;
var gCommandBuffer = null;
var gShellRecall = null;
var gCursorAtEOL = null;

var gPromptIndex = 0;
var gScrollTop = false;

var gControlActive = false;

var gPromptAction = null;
var gNotebook = null;
var gNotebookId = [0, 0];

var gTempId = 0;

var gParams = {};

var GTPrompt = "&gt; ";
var GTCurDirURI = "";

// Screen/scroll line array components
var JINDEX = 0;
var JOFFSET = 1;
var JDIR = 2;
var JPARAMS = 3;
var JLINE = 4;
var JMARKUP = 5;

var JTYPE = 0;
var JOPTS = 1;

function bind_method(obj, method) {
  return function() {
    return method.apply(obj, arguments);
  }
}

// Bind event to handler, with optional context (for "this" object in handler)
(function( $ ){
$.fn.rebind = function(eventType, handler, context) {
    this.unbind(eventType);
    if (context)
	handler = bind_method(context, handler)
    this.bind(eventType, handler);
  };
 })( jQuery);

// Bind click event to handler, with optional context (for "this" object in handler)
(function( $, clickEvent ){
$.fn.bindclick = function(handler, context) {
    this.unbind(clickEvent);
    if (context)
	handler = bind_method(context, handler)
    this.bind(clickEvent, handler);
  };
 })( jQuery, "click");

var MARKUP_TYPES = {markdown: 1};

var FILE_URI_PREFIX = "file:/"+"/"; // Split double slash for minification
var FILE_PREFIX = "/_file/";
var JSERVER = 0;
var JHOST = 1;
var JFILENAME = 2;
var JFILEPATH = 3;
var JQUERY = 4;

var AUTH_DIGITS = 12;      // Hex digits in form authentication HMAC
var HEX_DIGITS = 16;       // Hex digits in user authentication HMAC
var SIGN_HEXDIGITS = 16;   // Hex digits in user-entered keys

function undashify(s, digits) {
    s = s.replace(/\s+/g, "").replace(/-/g, "");
    if (digits)
	s = s.substr(0, digits);
    return s;
}

function compute_hmac(key, message) {
    //console.log("compute_hmac: ", key, message);
    return CryptoJS.algo.HMAC.create(CryptoJS.algo.SHA256, key).finalize(message).toString().substr(0,HEX_DIGITS);
}

function utf8_to_b64(utf8str) {
    return $.base64.encode(unescape(encodeURIComponent(utf8str)));
}

function b64_to_utf8(b64str) {
    return decodeURIComponent(escape($.base64.decode(b64str)));
}

function epoch_time(round) {
    // Returns seconds since epoch
    var time = (new Date).getTime()/1000;
    return round ? Math.round(time) : time;
}

function is_embedded_frame(exclude_same_host) {
    try {
	if (exclude_same_host)
	    return self.location.hostname != top.location.hostname;
	return window.frameElement && window.parent;
    } catch(err) {
	// If above fails due to cross-frame security
	return true;
    }
}

var gRawConverter = new Markdown.Converter();
var gConverter = new Markdown.getSanitizingConverter();

function cgi_unescape(escaped_str) {
  // Reverses python cgi.escape
    return escaped_str ? ("" +escaped_str).replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&") : escaped_str;
}

function split_lines(text) {
    // Split at line breaks; also replace no-break space (\xa0) with normal space
    return text.replace(/\xa0/g, " ").replace(/\r\n/g,"\n").replace(/\r/g,"\n").split("\n");
}

function md2html(mdText, safe, firstLine) {
    if (!mdText)
	return "";
    var converter = safe ? gConverter : gRawConverter;
    // Undo safe HTML escapes
    mdText = cgi_unescape(mdText);
    var lines = split_lines(mdText);
    if (firstLine)
	lines = lines.slice(0,1);
    var new_lines = [];
    for (var j=0; j<lines.length; j++) {
	// Strip out lines with !python pygments directive
	if (!lines[j].match(/^\s*!python\s*$/))
	    new_lines.push(lines[j]);
    }
    var html = converter.makeHtml(new_lines.join("\n")+"\n");
    if (html.substr(0,3) == "<p>" && html.substr(html.length-4) == "</p>") {
	html = html.substr(3, html.length-7);
    }
    return html;
}


var MATHCOMMENT = "<!--MathJax-->";
function math_md2html(mdText, safe, firstLine) {
  // Convert Markdown to HTML, preserving escaped math markup for MathJax processing
  // References:
  //   http://stackoverflow.com/questions/11228558/let-pagedown-and-mathjax-work-together
  //   http://www.math.union.edu/~dpvc/transfer/mathjax/mathjax-editing.js

  if (!gParams.mathjax)  // TEMPORARY (while MathJax implementation is being tested)
      return md2html(mdText, safe, firstLine);

  if (!mdText)
      return "";
  var blocks, start, end, last, braces; // used in searching for math
  var math;                             // stores math until markdone is done
  var inline = "$";     // the inline math delimiter

  var SPLIT = /(\$\$?|\\(?:begin|end)\{[a-z]*\*?\}|\\[\\{}$]|[{}]|(?:\n\s*)+|@@\d+@@)/i;

  function processMath(i,j) {
    var block = blocks.slice(i,j+1).join("")
      .replace(/&/g,"&amp;")                   // use HTML entity for &
      .replace(/</g,"&lt;")                    // use HTML entity for <
      .replace(/>/g,"&gt;")                    // use HTML entity for >
    ;
    if (gIExplorer) {block = block.replace(/(%[^\n]*)\n/g,"$1<br/>\n")}
    while (j > i) {blocks[j] = ""; j--}
    blocks[i] = "@@"+math.length+"@@"; math.push(block);
    start = end = last = null;
  }

  function removeMath(text) {
    start = end = last = null;       // for tracking math delimiters
    math = [];                       // stores math strings for latter

    blocks = text.replace(/\r\n?/g,"\n").split(SPLIT);
    for (var i = 1, m = blocks.length; i < m; i += 2) {
      var block = blocks[i];
      if (block.charAt(0) === "@") {
        //
        //  Things that look like our math markers will get
        //  stored and then retrieved along with the math.
        //
        blocks[i] = "@@"+math.length+"@@";
        math.push(block);
      } else if (start) {
        //
        //  If we are in math, look for the end delimiter,
        //    but don't go past double line breaks, and
        //    and balance braces within the math.
        //
        if (block === end) {
          if (braces) {last = i} else {processMath(start,i)}
        } else if (block.match(/\n.*\n/)) {
          if (last) {i = last; processMath(start,i)}
          start = end = last = null; braces = 0;
        } else if (block === "{") {braces++}
          else if (block === "}" && braces) {braces--}
      } else {
        //
        //  Look for math start delimiters and when
        //    found, set up the end delimiter.
        //
        if (block === inline || block === "$$") {
          start = i; end = block; braces = 0;
        } else if (block.substr(1,5) === "begin") {
          start = i; end = "\\end"+block.substr(6); braces = 0;
        }
      }
    }
    if (last) {processMath(start,last)}
    return blocks.join("");
  }
  
  function replaceMath(text) {
    text = text.replace(/@@(\d+)@@/g,function (match,n) {return math[n]});
    return text;
  }
  var mdHtml = md2html(removeMath(mdText), safe, firstLine);
  if (math.length)
      mdHtml = MATHCOMMENT+replaceMath(mdHtml);
  math = null;
  return mdHtml;
}

function createFileURI(uri) {
    if (uri.substr(0,FILE_URI_PREFIX.length) == FILE_URI_PREFIX)
	return uri;
    if (uri.substr(0,5) == "http:" || uri.substr(0,6) == "https:") {
	uri = uri.substr(uri.indexOf(":")+3);
	var j = uri.indexOf("/");
	if (j >= 0)
	    uri = uri.substr(j);
	else
	    uri = "/";
    }
	
    if (uri.substr(0,FILE_PREFIX.length) != FILE_PREFIX)
	return "";
    var path = uri.substr(FILE_PREFIX.length);
    var comps = path.split("/");
    if (comps[0] == "local")
	comps[0] = "";
    return FILE_URI_PREFIX + comps.join("/");
}

function makeFileURL(url) {
    if (url.substr(0,FILE_URI_PREFIX.length) == FILE_URI_PREFIX)
	return url;
    if (url.substr(0,5) == "http:" || url.substr(0,6) == "https:")
	return url;
    if (url.substr(0,FILE_PREFIX.length) == FILE_PREFIX)
	return window.location.protocol+"/"+"/"+window.location.host+url;
    return "";
}

// Returns [protocol://server[:port], hostname, filename, fullpath, query] for for file://host/path
//        or http://server:port/_file/host/path, or /_file/host/path URLs.
// If not file URL, returns null
function splitFileURL(url) {
    var hostPath;
    var serverPort = window.location.protocol+"/"+"/"+window.location.host;
    if (url.substr(0,FILE_URI_PREFIX.length) == FILE_URI_PREFIX) {
	hostPath = url.substr(FILE_URI_PREFIX.length);
    } else if (url.substr(0,FILE_PREFIX.length) == FILE_PREFIX) {
	hostPath = url.substr(FILE_PREFIX.length);
    } else {
	var protocol;
	if (url.indexOf("http:/"+"/") == 0)
	    protocol = "http";
        else if (url.indexOf("https:/"+"/") == 0)
            protocol = "https";
        else
            return null;

	var s = url.substr(protocol.length+3);
        var k = s.indexOf("/");
        if (k < 0)
            return null;
        serverPort = s.substr(0,k);
        var urlPath = s.substr(k);
	if (urlPath.substr(0,FILE_PREFIX.length) != FILE_PREFIX)
	    return null;
	hostPath = urlPath.substr(FILE_PREFIX.length);
    }

    var j = hostPath.indexOf("?");
    var query = "";
    if (j >= 0) {
	query = hostPath.substr(j)
	hostPath = hostPath.substr(0,j);
    }
    var comps = hostPath.split("/");
    return [serverPort, comps[0], comps[comps.length-1], "/"+comps.slice(1).join("/"), query]
}

function getCookie(name) {
    var raw_val = $.cookie(name, {raw: true});
    return raw_val ? unescape(raw_val) : "";
}

function setCookie(name, value, exp_days) {
    var cookie_value = escape(value);
    var options = {raw: true, path: '/'};
    if (exp_days)
	options.expires = exp_days;
    $.cookie(name, cookie_value, options);
}


function getAuth() {
    return getCookie("GRAPHTERM_AUTH").substr(0,AUTH_DIGITS);
}

function AuthPage(auth_params) {
    //console.log("AuthPage", auth_params);
    gAuthenticatingCookie = auth_params.cookie;
    gAuthParams = auth_params;
    $("#authcode").val("");
    $("#authcookie").val(gAuthenticatingCookie);

    if (!auth_params.hmac_auth)
	$("#authcodeprompt").html("Password")

    if (auth_params.need_user) {
	if (auth_params.need_user != "_")
	    $("#authuser").val(auth_params.need_user);
	$("#authusercontainer").show();
    } else {
	$("#authusercontainer").hide();
    }

    if (auth_params.need_code) {
	if (auth_params.need_code != "_")
	    $("#authcode").val(auth_params.need_code);
	$("#authcodecontainer").show();
    } else {
	$("#authcodecontainer").hide();
    }

    if (auth_params.goog_auth)
	$("#authgoogcontainer").show()
    else
	$("#authgoogcontainer").hide()
	
    $("#authmessage").html(auth_params.message || "");

    $("#terminal").hide();
    $("#session-container").hide();
    $("#authenticate").show();

    $(document).unbind("keydown");
    $(document).unbind("keypress");
    $("body").unbind("paste");

    $("#authenticate").rebind("submit", Authenticate);
    $("#authgoog").rebind("click", AuthGoogle);
    $("#authuser").focus();
}

function AuthGoogle(evt) {
    console.log("AuthGoogle: ", evt);
    var auth_code = $("#authcode").val() || "";
    var authHMAC = auth_code ? compute_hmac(undashify(auth_code, SIGN_HEXDIGITS), gAuthenticatingCookie) : "";
    window.location = window.location.protocol+"/"+"/"+window.location.host+"/_gauth/?"+$.param({gterm_cauth: gAuthenticatingCookie, gterm_code: authHMAC, gterm_user:$("#authuser").val()});
    gAuthParams = null;
    return false;
}

function Authenticate(evt) {
    console.log("Authenticate: ", evt);
    var hmac_auth = gAuthParams.hmac_auth;
    gAuthParams = null;
    if (!hmac_auth)
	return true

    var auth_code = $("#authcode").val() || "";
    auth_code = compute_hmac(undashify(auth_code, SIGN_HEXDIGITS), gAuthenticatingCookie);
    window.location = location.pathname+"?"+$.param({cauth: gAuthenticatingCookie, code: auth_code, user:$("#authuser").val()});
    return false;
}

var gEmailForm = '<form id="emailaddrform" method="get" action="/unknown"><span id="emailaddrcontainer">E-mail: <input id="emailaddr" name="save_email" type="text"/></span> <input id="emailsubmit" type="submit" value="Submit Email"/></form>';

function EmailSubmit(evt) {
    window.location = '/?'+$.param({qauth: getAuth(), save_email:$("#emailaddr").val()});
    return false;
}

function gtermListTerminals(connect_params, terminals) {
    $("#terminal").hide();
    $("#session-container").hide();

    var header = (connect_params.user ? 'User: <b>'+connect_params.user+'</b><br>\n' : '') + 'Host: <b>' + connect_params.host + '</b><p>\n';
    if (terminals.length) {
	$("#gterm-terminal-list-table").append('<tr><td><em>Sessions</em></td></tr>\n')
	for (var j=0; j<terminals.length; j++) {
            // [term_name, connectable, stealable, watch_count, idle_min]
	    var term_name = terminals[j][0];
	    var term_html = '<tr>';
	    term_html += '<td class="gterm-terminal-list-name">'+term_name+(terminals[j][3] > 1 ? ('('+terminals[j][3]+')') : '') + '</td> ';
	    if (terminals[j][2]) {
		// Stealable session
		term_html += '<td> <a href="/'+connect_params.host+'/'+term_name+'/?qauth='+getAuth()+'">watch</a></td>';
		term_html += '<td> <a href="/_steal/'+connect_params.host+'/'+term_name+'/?qauth='+getAuth()+'&cauth='+connect_params.cookie+'">steal</a></td>';
	    } else {
		// Not stealable; check if session is connectable
		term_html += '<td> <a href="/_watch/'+connect_params.host+'/'+term_name+'/?qauth='+getAuth()+'&cauth='+connect_params.cookie+'">watch</a></td>';
		if (terminals[j][1])
		    term_html += '<td> <a href="/'+connect_params.host+'/'+term_name+'/?qauth='+getAuth()+'">connect</a></td>';
	    }
	    term_html += '<td>idle '+terminals[j][4]+'min.</td>';
	    term_html += '</tr>';
	    $("#gterm-terminal-list-table").append(term_html);
	}
    } else if (!connect_params.allow_new) {
	header += 'No GraphTerm sessions currently accessible<br>';
    }
    $(document).unbind("keydown");
    $(document).unbind("keypress");
    $("body").unbind("paste");

    $("#gterm-terminal-list-header").html(header);
    $("#gterm-terminal-list").show();
    if (connect_params.allow_new)
	$("#gterm-terminal-list-open").show();
    else
	$("#gterm-terminal-list-open").hide();

    $("#gterm-terminal-list").rebind("submit", gtermOpenTerminal);
    $("#gterm-terminal-list-input").focus();
}

function gtermOpenTerminal(evt) {
    console.log("gtermOpenTerminal", evt);
    window.location = location.pathname+($("#gterm-terminal-list-input").val() || "new")+"/?qauth="+getAuth();
    return false;
}

function Connect(auth_user, auth_code, connect_cookie) {
    gWebSocket = new GTWebSocket(auth_user, auth_code, connect_cookie);
}

function SignOut() {
    setCookie("GRAPHTERM_AUTH", null);
    $("body").html('Signed out from GraphTerm.<p><a href="/">Sign in again</a>');
}

function resizeTerminal() {
    $("#session-testscreen").show();
    setTimeout(resizeTerminalAux, 100);
}

function resizeTerminalAux() {
    sizeupTerminal();
    setTimeout(resizeTerminalAux2, 100);
}

function resizeTerminalAux2() {
    $("#session-testscreen").hide();
    $("#session-log .curentry .input .command").focus();
    handle_resize();
}

function sizeupTerminal() {
    gRowHeight = $("#session-testscreen").height() / 25;
    gColWidth = 0.55 + (1.05*$("#session-testscreen-testrow").width() / 80);
    console.log("sizeupTerminal: ", $("#session-testscreen").height(), $("#session-testscreen-testrow").width(), gRowHeight, gColWidth);
}

function setupTerminal() {
    sizeupTerminal();
    $("#session-testscreen").hide();
    $("#session-term").hide();
    $("#session-altscreen").hide();
    $("#session-log .curentry .input .command").focus();
}

function handle_resize() {
    //console.log("handle_resize:");
    gRows = Math.max(2, Math.floor($(window).height()/gRowHeight)-1);
    gCols = Math.max(3, Math.floor($(window).width()/gColWidth)-1);
    if (gWebSocket && gParams.controller)
	gWebSocket.write([["set_size", [gRows, gCols, $(window).height(), $(window).width(), gParams.parent_term||""]]]);
    var isNarrow = $("#terminal").hasClass("gterm-narrow");
    try {
	$("#terminal").toggleClass("gterm-narrow", $("#menubar-first-item").width()/$(window).width() > 0.077);
    } catch(err) {
    }
    if (isNarrow == $("#terminal").hasClass("gterm-narrow"))
	handle_resize_aux();
    else
	setTimeout(handle_resize_aux, 100);
}

function handle_resize_aux() {
    $("#menubar-padding").css("height", $("#gterm-menu").height());
    $("#gterm-mid-padding").css("height", $("#gterm-menu").height());
}

function scrolledIntoView(elem, scroll) {
    var docViewTop = $(window).scrollTop();
    var elemHeight = $(elem).height();
    var winHeight = $(window).height();
    var docViewBottom = docViewTop + winHeight;
    var elemTop = $(elem).offset().top;
    var elemBottom = elemTop + elemHeight;

    var topVisible = (elemTop >= docViewTop) && (elemTop <= docViewBottom);
    var bottomVisible = (elemBottom >= docViewTop) && (elemBottom <= docViewBottom);

    if (!scroll)
	return topVisible || bottomVisible;

    // Scroll
    var topMargin = $("#gterm-header").height();
    var elemFits = elemHeight <= winHeight;
    if (!topVisible && (!bottomVisible || elemFits))
	$(window).scrollTop($(elem).offset().top-topMargin);
    else if (!bottomVisible)
	$(window).scrollTop($(elem).offset().top+elemHeight-winHeight);
    return true;
}

function openTerminal() {
    $("#session-term").show();
    $("#session-roll").hide();
    if (gWebSocket)
	gWebSocket.terminal = true;
}

function closeTerminal() {
    $("#session-term").hide();
    $("#session-roll").show();
    if (gWebSocket)
	gWebSocket.terminal = false;
}

function serverLog(msg) {
    if (gWebSocket)
	gWebSocket.write([["server_log", msg+""]]);
}

function GTNextEntry() {
    gEntryIndex += 1;
    gCommandId = gCommandPrefix+gEntryIndex;
    return '<div class="entry curentry"><div class="input"><span class="prompt" data-gtermuri="'+GTCurDirURI+'">'+GTPrompt+'</span><span id="'+gCommandId+'" class="command" autocapitalize="off" contentEditable="true">&nbsp;</span></div></div>';
}

function GTFirstEntryIndex() {
    var firstEntry, commandPrefix;
    if (gWebSocket && gWebSocket.terminal) {
	commandPrefix = "entry";
	firstEntry = $("#session-bufscreen .promptrow:first");
    } else {
	commandPrefix = gCommandPrefix;
	firstEntry = $("#session-log .entry .command:first");
    }
    if (!firstEntry.length)
	return 0;
    return parseInt(firstEntry.attr("id").substr(commandPrefix.length));
}

function GetCursorText() {
    var text = $("#gterm-pre0 .cursorloc").text();
    if ($.trim(text)) {
	$("#gterm-pre0 .cursorloc").text(" ");
	return text.substr(0,text.length-1);
    } else {
	return "";
    }
}

function GTGetCommandText(n) {
    var commandPrefix = (gWebSocket && gWebSocket.terminal) ? "entry" : gCommandPrefix;
    var cmd_id = "#"+commandPrefix+n;
    if (gWebSocket && gWebSocket.terminal) {
	var cmdText = $(cmd_id).text().substr($(cmd_id+" .gterm-cmd-prompt").text().length+1);
	if (cmdText && cmdText.charCodeAt(cmdText.length-1) == 10)
	    cmdText = cmdText.substr(0,cmdText.length-1); // Chop off the newline
	return cmdText.replace(/^\s+/, "");
    } else {
	return $(cmd_id).text().replace(/^\s+/, "");
    }
}

function GTGetCurCommandText() {
    if (gWebSocket && gWebSocket.terminal) {
	var curtext = $("#gterm-pre0").text().substr($("#gterm-pre0 .gterm-cmd-prompt").text().length+1);
	curtext = curtext.substr(0, curtext.length-$("#gterm-pre0 .cmd-completion").text().length-$("#gterm-pre0 .cursorloc").text().length-1);
	return curtext;
    } else {
	return $("#session-log .curentry .input .command").text();
    }
}

function GTSetCommandText(text, noClear) {
    // Set (unescaped) text for current command line
    if (gWebSocket && gWebSocket.terminal) {
	var curtext = GTGetCurCommandText().replace(/^\s+/, "");
	if (curtext == text.substr(0, curtext.length)) {
	    var tailtext = text.substr(curtext.length);
	    $("#gterm-pre0 .cmd-completion").text(tailtext);
	    if (tailtext)
		$("#gterm-pre0 .cursorloc").text("");
	    else
		$("#gterm-pre0 .cursorloc").text(" ");
	}
    } else {
	$("#session-log .curentry .input .command").text(text);
    }
    if (!noClear)
	gCommandBuffer = null;  // Clear command buffer
}

function GTCommandMatch(prefix, downward) {
    // Finds command with matching prefix in history
    // If null prefix, find any non-null command.
    // If downward, search downwards.
    // Returns non-null command string on success
    var curIndex = (gWebSocket && gWebSocket.terminal) ? gPromptIndex+1 : gEntryIndex;
    if (!gCommandMatchIndex) {
	gCommandMatchIndex = curIndex;
	gCommandatchPrev = null;
    }

    if (downward) {
	while (gCommandMatchIndex < curIndex) {
	    gCommandMatchIndex += 1;
	    if (gCommandMatchIndex >= curIndex)
		return gCommandBuffer;

	    var cmd = GTGetCommandText(gCommandMatchIndex);
	    if (cmd && cmd != gCommandMatchPrev) {
		if (cmd.substr(0,prefix.length) == prefix) {
		    gCommandMatchPrev = cmd;
		    return cmd;
		}
	    }
	}
    } else {
	var firstIndex = GTFirstEntryIndex();
	while (gCommandMatchIndex > firstIndex) {
	    gCommandMatchIndex -= 1;
	    var cmd = GTGetCommandText(gCommandMatchIndex);
	    if (cmd && cmd != gCommandMatchPrev) {
		if (cmd.substr(0,prefix.length) == prefix) {
		    gCommandMatchPrev = cmd;
		    return cmd;
		}
	    }
	    if (gCommandMatchIndex <= firstIndex)
		break;
	}
    }
    return null;
}

function GTStrip(text) {
    // Strip leading/trailing non-breaking spaces
    return text.replace(/^[\xa0]/,"").replace(/[\xa0]$/,"").replace(/[\xa0]/g," "); 
}

function GTPreserveLinebreaks(html) {
    return html.replace(/\r\n/g,"<br>").replace(/\r/g,"<br>").replace(/\n/g,"<br>");
}

function GTEscape(text, pre_offset, prompt_offset, prompt_id) {
    var prefix = "";
    if (prompt_offset) {
	var prompt_idattr = prompt_id ? ' id="'+prompt_id+'"' : '';
	prefix = '<span class="gterm-cmd-prompt gterm-link"'+prompt_idattr+'>' + text.substring(pre_offset, prompt_offset) + '</span>';
	text = text.substr(prompt_offset);
    }
    var text2 = prefix + text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return text2;
}

function GTEscapeSpan(text, style_list) {
    // Return styled (and escaped) SPAN string
    if (!text)
	return "";
    var span_escaped = GTEscape(text);
				
    if (style_list && style_list.length) {
	return '<span class="'+style_list.join(" ")+'">'+span_escaped+'</span>';
    } else {
	return span_escaped;
    }
}

function GTCursorSpan(cursor_char) {
    // Return SPAN string for cursor character
    if (!cursor_char)
	return "";
    var tag = gFirefoxBrowser ? "div" : "span"; // Can't paste into span in firefox
    //var innerEditable = !gFirefoxBrowser ? "true" : "false";
    var innerEditable = "true";

    return '<span class="typeahead"></span><span class="cmd-completion"></span><'+tag+' class="cursorspan" contentEditable="true" data-gtermcursorchar="'+cursor_char+'"><'+tag+' class="cursorloc" autocapitalize="off" contentEditable="'+innerEditable+'">'+GTEscape(cursor_char)+'</'+tag+'></'+tag+'>';
}

function GTGetFilePath(fileURI, parentURI) {
    // Returns unescaped file path, relative to parent URI (without trailing /) (if specified)
    parentURI = parentURI || "";
    if (fileURI == parentURI)
	return ".";
    var parentPrefix = parentURI ? parentURI + "/" : "";
    var newPath;
    if (parentPrefix && fileURI.substr(0,parentPrefix.length) == parentPrefix) {
	newPath = fileURI.substr(parentPrefix.length);
    } else {
	var filePrefix = fileURI + "/";
	if (parentURI && parentURI.substr(0,filePrefix.length) == filePrefix) {
	    var comps = parentURI.substr(filePrefix.length).split("/");
	    var relPath = "..";
	    for (var j=0; j<comps.length-1; j++)
		relPath += "/..";
	    if (relPath.length < fileURI.length)
		return relPath;
	}
	newPath = (splitFileURL(fileURI))[JFILEPATH];
    }

    return decodeURIComponent(newPath);
}

function GTReceivedUserInput(source) {
    gControlActive = false;
    if (gShowingSplash && !gAnimatingSplash)
	GTHideSplash(true);
    $("#headfoot-control").removeClass("gterm-headfoot-active");
    if (source != "select") {
	// Cancel command completion
	gCommandBuffer = null;
	if (source != "updownarrow")
	    gShellRecall = null;
	$("#gterm-pre0 .cmd-completion").text("");
    }
}

function GTUpdateController() {
    var label_text = gParams.host+"/"+gParams.term;
    if (gParams.user)
	label_text = gParams.user+"@"+label_text;
    $("#menubar-sessionlabel").text(label_text);
    if (gParams.controller)
	window.name = gParams.host+"/"+gParams.term;
    else
	window.name = "";
    GTMenuUpdateToggle("share_control", gParams.controller);
    $("#terminal").toggleClass("gterm-controller", gParams.controller);
    $("#terminal").toggleClass("gterm-superuser", gParams.super_user);
    handle_resize();
    gFrameDispatcher.updateControl(gParams.controller);
}

function GTClearTerminal() {
    $("#session-bufscreen").children().remove();
}

function GTAppendPagelet(parentElem, row_params, entry_class, classes, markup) {
    //console.log("GTAppendPagelet:", row_params);
    var row_opts = row_params[JOPTS];
    var overwrite = !!row_opts.overwrite;
    var pagelet_id = row_opts.pagelet_id || "";
    var scroll = row_opts.scroll || "";
    var current_dir = row_opts.current_dir|| "";
    var pagelet_display = row_opts.display || "";
    var scrollElemId = "gterm-scroll"+pagelet_id;
    var attrs = ' id="'+scrollElemId+'" data-gtermcurrentdir="'+current_dir+'" data-gtermpromptindex="'+gPromptIndex+'" ';

    if (pagelet_display.substr(0,4) == "full") {
	// Hide previous entries
	classes += " gterm-full";
	if (pagelet_display == "fullwindow" || pagelet_display == "fullscreen") {
	    classes += " gterm-fullwindow";
	}
	if (row_opts.form_input) {
	    StartFullpage(pagelet_display, false);
	    GTStartForm(row_opts, gPromptIndex);
	} else {
	    StartFullpage(pagelet_display, true);
	}
	var prevFullElem = parentElem.children("."+entry_class+" .gterm-full");
	if (prevFullElem.length != 1 || prevFullElem.attr("id") != scrollElemId) {
	    // Remove any previous full pagelets for this entry
	    prevFullElem.remove();
	}
	if ("scroll" in row_opts && row_opts.scroll != "down")
	    gScrollTop = true;
    } else if (!gNotebook) {
	// Non-full pagelet entry; show previous entries
	    EndFullpage();
    }
    // Use query authentication
    markup = markup.replace(/qauth=%\(qauth\)/g, "qauth="+getAuth());
    if (row_opts.iframe) {
	markup = gFrameDispatcher.createFrame(row_opts, markup, row_opts.url, "gterm-iframe"+pagelet_id);
    }
    var rowHtml = '<div class="'+classes+'" '+attrs+'>'+markup+'</div>\n';
    var rowElem = $(rowHtml);
    var innerBlockElem = rowElem.children(".gterm-blockhtml");
    // Look for previous element with same id
    var scrollElem = $("#"+scrollElemId);
    if (scrollElem.length) {
	// Found element with same id; overwrite
	if (scrollElem.find(".gterm-blockimg").length == 1 && innerBlockElem.length == 1 && innerBlockElem.find(".gterm-blockimg").length == 1) {
	    // Replace IMG src attribute of block element and return
	    scrollElem.find(".gterm-blockimg").attr("src", innerBlockElem.find(".gterm-blockimg").attr("src"));
	    return scrollElem;
	}
	// Replace entire element
	scrollElem.html(markup);

    } else {
	// Element with same id does not exist
	var prevBlockElem = parentElem.find(".pagelet:not(.oldentry) .gterm-blockhtml:not(.gterm-blockclosed)");

	if (overwrite && innerBlockElem.length == 1 && prevBlockElem.length == 1) {
	    // Modify single previous element
	    scrollElem = prevBlockElem.parent();
	    if (prevBlockElem.find(".gterm-blockimg").length == 1 && innerBlockElem.find(".gterm-blockimg").length == 1) {
		// Replace IMG src attribute
		prevBlockElem.find(".gterm-blockimg").attr("src", innerBlockElem.find(".gterm-blockimg").attr("src"));
	    } else {
		// Replace previous block element
		prevBlockElem.replaceWith(innerBlockElem);
	    }
	} else {
	    // Append new element (closing any previous elements)
	    prevBlockElem.addClass("gterm-blockclosed");
	    scrollElem = rowElem.appendTo(parentElem);
	}
    }

    if (row_opts.form_input) {
	scrollElem.find(".gterm-form-button").bindclick(GTFormSubmit);
	scrollElem.find(".gterm-help-link").bindclick(GTHelpLink);
    }

    if (row_opts.autosize)
	GTAutosizeIFrame(scrollElem);

    scrollElem.find('td .gterm-link:not(.gterm-download)').bindclick(gtermPageletClickHandler);
    scrollElem.find('td img').bind("dragstart", function(evt) {evt.preventDefault();});
    scrollElem.find('.gterm-togglelink').bindclick(gtermLinkClickHandler);
    scrollElem.find('.gterm-iframeclose').bindclick(CloseIFrame);
    scrollElem.find('.gterm-iframedelete').bindclick(CloseIFrame);
    scrollElem.find('.gterm-iframeexpand').bindclick(ExpandIFrame);
    GTDropBindings(scrollElem.find(' .droppable'));

    gDelayedPageExit = !!row_opts.exit_page;
    if (gDelayedPageExit)
	setTimeout(DelayedExitFullpage, 200);
    return scrollElem;
}

function DelayedExitFullpage() {
    if (!gDelayedPageExit)
	return;
    gDelayedPageExit = false;
    EndFullpage();
    ScrollTop(null);
}

function GTPreloadImages(urls) {
    if (!urls.length)
	return;
    var img = new Image();
    img.src = urls.shift();
    var remainingUrls = urls;
    //console.log("GTPreloadImages: Loading "+img.src);
    img.onload = function() {
	GTPreloadImages(remainingUrls);
    }
}

function GTBufferScript(content) {
    if (content) {
	gScriptBuffer = content.replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
	if (gScriptBuffer.length && !gScriptBuffer[gScriptBuffer.length-1])
	    gScriptBuffer = gScriptBuffer.slice(0, gScriptBuffer.length-1);
    } else {
	gScriptBuffer = [];
    }
}

function GTGetLocalFile(filepath, current_dir, callback) {
    if (!filepath)
	return;
    if (filepath.charAt(0) != "/")
	filepath = current_dir + "/" + filepath;
    var url =  window.location.protocol+"/"+"/"+window.location.host + FILE_PREFIX + "local" + filepath;
    url += "?hmac="+compute_hmac(getCookie("GRAPHTERM_HOST_LOCAL"), filepath);
    $.get(url, function(data, textStatus, jqXHR) {
	           callback(""+data) })
        .error(function(jqXHR, textStatus, errorThrown) {
            alert("Failed to load local file: "+filepath+": "+errorThrown);
        });
}

function GTWebSocket(auth_user, auth_code, connect_cookie) {
    this.failed = false;
    this.opened = false;
    this.closed = false;
    this.auth_user = auth_user || "";
    this.auth_code = auth_code || "";
    connect_cookie = connect_cookie || "";

    this.icons = false;
    this.terminal = false;

    this.webcast = false;
    this.theme = "light";
    this.fontsize = "medium";
    this.alt_mode = false;

    this.repeat_command = "";
    this.repeat_intervalID = null;

    var protocol = (window.location.protocol.indexOf("https") == 0) ? "wss" : "ws";
    this.ws_url = protocol+":/"+"/"+window.location.host+"/_websocket"+window.location.pathname; // Split the double slash to avoid confusing the JS minifier
    if (location.search)
	this.ws_url += location.search;
    var add_params = (this.auth_user || this.auth_code) ? {user: auth_user, code: auth_code} : {};
    if (is_embedded_frame(true))
	add_params.embedded = "1";
    if (connect_cookie)
	add_params.cauth = connect_cookie;
    if (!$.isEmptyObject(add_params))
	this.ws_url += (location.search ? "&" : "?") + $.param(add_params);
    console.log("GTWebSocket url: "+this.ws_url);
    this.ws = new WebSocket(this.ws_url);
    this.ws.onopen = bind_method(this, this.onopen);
    this.ws.onmessage = bind_method(this, this.onmessage);
    this.ws.onclose = bind_method(this, this.onclose);
    console.log("GTWebSocket.__init__: ");
}

GTWebSocket.prototype.term_input = function(text, type_ahead, command_line) {
    // Send text to terminal (clears current directory info)
    if (type_ahead && gTypeAhead && $(".gterm-cmd-line .typeahead").length == 1 && !$(".gterm-cmd-line .typeahead").attr("frozen")) {
	// Type ahead only works on the command line
        // (otherwise passwords will be echoed!)
	var aheadElem = $(".gterm-cmd-line .typeahead");
	var aheadText = aheadElem.text();
	for (var j=0; j<text.length; j++) {
	    if (text.charCodeAt(j) >= 32 && text.charCodeAt(j) < 127) {
		// Printable character
		aheadText += text.charAt(j);
	    } else if (text.charCodeAt(j) == 127 && aheadText.length) {
		// Backspace/DEL (with non-empty typeahead text)
		aheadText = aheadText.substr(0,aheadText.length-1);
	    } else {
		// Non-printable character
		aheadElem.attr("frozen", "true");
		break;
	    }
	}
	$(".typeahead").text(aheadText);
    }
    if (text == "\x1b[A" || text == "\x1b[B") 
	GTReceivedUserInput("updownarrow");
    else
	GTReceivedUserInput("key");

    if (command_line)
	this.write([["paste_command", text]]);
    else
	this.write([["keypress", text]]);
}

GTWebSocket.prototype.write = function(msg) {
    try {
	if (this.ws.readyState > WebSocket.OPEN)
	    throw "Websocket closed";
	this.ws.send(JSON.stringify(msg));
    } catch(err) {
	if (window.confirm("Error in websocket ("+err+"). Reload page?")) {
	    window.location.reload();
	}
    }
}

GTWebSocket.prototype.onopen = function(evt) {
  console.log("GTWebSocket.onopen: ");
}

function GTAutosizeIFrame(elem) {
    // After a delay, adjust size of all iframe child elements to match actual size
    setTimeout( function() { $(elem).find("iframe").each( function() {
	$(this).height($(this).contents().find('body').height() + 25);} ) }, 1000 );
}

function GTRepeatCommand() {
    if (gWebSocket && gWebSocket.repeat_command)
	gWebSocket.evalCommand(gWebSocket.repeat_command, true);
}

GTWebSocket.prototype.repeatCommand = function(command) {
    if (this.repeat_intervalID) {
	window.clearInterval(this.repeat_intervalID);
	this.repeat_intervalID = null;
    }

    if (command) {	
	this.repeat_command = command;
	this.repeat_intervalID = window.setInterval(GTRepeatCommand, REPEAT_MILLISEC);
    } else {
	this.repeat_command = "";
    }
}

GTWebSocket.prototype.evalCommand = function(command, repeat) {
    var stdout = "";
    var stderr = "";
    try {
	if (OSH_ECHO && !repeat)
	    console.log(command);
	var evalout = eval(command);
	stdout = evalout ? evalout+"" : "";
	if (OSH_ECHO && stdout && !repeat)
	    console.log(stdout);
    } catch (err) {
	stderr = err+"";
	if (OSH_ECHO && stderr)
	    console.log(stderr);
    }

    var osh_send = [];
    if (stderr)
	osh_send.push(["osh_stderr", !!this.repeat_intervalID, stderr]);
    osh_send.push(["osh_stdout", !!this.repeat_intervalID, stdout]);
    gWebSocket.write(osh_send);
}

GTWebSocket.prototype.onmessage = function(evt) {
    if (this.closed)
	return;

    var payload = evt.data;
    if (gDebugMessages)
	console.log("GTWebSocket.onmessage: "+payload);

    if (!this.opened) {
	// Validate
	this.opened = true;
    }
    try {
	var payload_obj = JSON.parse(payload);
	for (var j=0; j<payload_obj.length; j++) {
	    var command = payload_obj[j];
	    var action = command[0];

            if (action == "osh_stdin") {
		// Execute JS "command" from otrace console
		if (command[1] == "repeat") {
		    this.repeatCommand();
		} else if (command[1].substr(0,7) == "repeat ") {
		    this.repeatCommand(command[1].substr(7));
		} else {
		    this.repeatCommand();
		    this.evalCommand(command[1]);
		}

            } else if (action == "body") {
		$("body").unbind("paste");
		$("body").html(command[1]);

            } else if (action == "abort") {
		alert(command[1]);
		window.location = "/";

            } else if (action == "alert") {
		alert(command[1]);

            } else if (action == "authenticate") {
		if (getCookie("GRAPHTERM_AUTH"))
		    setCookie("GRAPHTERM_AUTH", null);
		AuthPage(command[1]);

            } else if (action == "open") {
		OpenNew(command[1], command[2]);

            } else if (action == "redirect") {
		window.location = command[1];
		if (command[2])
		    setCookie("GRAPHTERM_AUTH", command[2]);

            } else if (action == "join") {
		GTJoin(command[1], command[2]);

            } else if (action == "update_menu") {
		// Update menu
		GTMenuUpdate(command[1], command[2]);

            } else if (action == "setup") {
		$("#authenticate").hide();
		$("#gterm-terminal-list").hide();
		$("#terminal").show();
		$("#session-container").show();
		gParams = command[1];
		if (gParams.mathjax && !window.MathJax)
		    GTLoadMathJax();
		GTMenuStateUpdate(gParams.state_values);
		resizeTerminal();
		GTUpdateController();
		for (var k=0; k<gParams.watchers.length; k++)
		    GTJoin(gParams.watchers[k], true, true);
		gtermChatStatus(gParams.chat);

		if (gParams.host_secret)
		    setCookie("GRAPHTERM_HOST_"+gParams.normalized_host, ""+gParams.host_secret);

		if (gParams.state_id)
		    setCookie("GRAPHTERM_AUTH", gParams.state_id);
		if (!gParams.oshell)
		    openTerminal();
		if (gParams.controller && gParams.display_splash && gParams.term != "osh" && !is_embedded_frame())
		    GTShowSplash(true, true);

            } else if (action == "confirm_path") {
		if (command[1])
		    setCookie("GRAPHTERM_AUTH", command[1]);
		var conf_path = command[2];
		var conf_html = "<p>";
		conf_html += '<h3>Click to open: <a href="'+conf_path+'/?qauth='+getAuth()+'">'+conf_path+'</a></h3>';
		$("body").html(conf_html);

            } else if (action == "host_list") {
		if (command[1])
		    setCookie("GRAPHTERM_AUTH", command[1]);
		var user = command[2];
		var new_user_code = command[3];
		var new_user_email = command[4];
		var hosts = command[5];
		var host_html = '<h3>GraphTerm Hosts</h3>';
		if (user)
		    host_html += 'User: <b>'+user + '</b><p>\n';
		if (new_user_code) {
		    if (new_user_code == "activated") {
			host_html += 'Activated user. ';
		    } else {
			var mail_body = "User: "+user+"\nCode: "+new_user_code+"\nURL: "+window.location.protocol+"/"+"/"+window.location.host+"/\n";
			host_html += 'Created new user with authentication code:<br>&nbsp;<b>'+new_user_code+'</b><br>Copy this information for future use or <a href="mailto:?subject=Graphterm%20code&body='+encodeURIComponent(mail_body)+'">email it to yourself</a>.<p>';
		    }
		    host_html +='<a href="/">Click here</a> to open a terminal.';

		    if (new_user_email) {
			host_html += '<p>You can also authenticate yourself via your email login: '+new_user_email+'<br>';
		    } else {
			host_html += '<p>Optionally, you can enter an email address below. It will be used only for password recovery.<br>'+gEmailForm;
		    }
		} else if (!hosts.length) {
		    host_html += 'No GraphTerm Hosts currently available<br>';
		} else {
		    host_html += 'Available hosts:<p>';
		    host_html += '<ol>';
		    for (var j=0; j<hosts.length; j++)
			host_html += '<li><a href="/'+hosts[j]+'/?qauth='+getAuth()+'">'+hosts[j]+'</a></li>';
		    host_html += '</ol>';
		}
		host_html += '<p><a href="#" onclick="SignOut();">Sign out</a>';
		$("body").html(host_html);
		if (new_user_code) {
		    $("#emailaddrform").rebind("submit", EmailSubmit);
		    $("#emailaddr").focus();
		}

            } else if (action == "term_list") {
		var connect_params = command[1];
		if (connect_params.state_id)
		    setCookie("GRAPHTERM_AUTH", connect_params.state_id);
		gtermListTerminals(connect_params, command[2]); 

            } else if (action == "log") {
		var logPrefix = command[1];
		var logArgs = command[2];
		var logtype = logArgs[0] || "log";
		var prefix = (logtype.substr(0,3) != "web")  ? logtype.toUpperCase()+": " : "";
		if (logtype != "webrepeat") {
		    this.repeatCommand(); // Cancel any repeats, if not repeat web command output
		}
		//console.log(prefix+logArgs[2]);
		var logclasses = "gterm-log"
		if (logtype == "webrepeat") {
		    logclasses += " gterm-logrepeat";
		    $("#session-log .preventry .gterm-logrepeat").remove();
		}
		$(logPrefix+'<pre class="'+logclasses+'">'+prefix+logArgs[2]+'</pre>').appendTo("#session-log .preventry");
		$("#session-log .preventry .gterm-log .gterm-link").bindclick(otraceClickHandler);

            } else if (action == "receive_msg") {
		var fromUser = command[1];
		var toUser = command[2];
		var target = command[3];
		if (target == "frame") {
		    if (gFrameDispatcher)
			gFrameDispatcher.receive(fromUser, toUser, command[4], command[5]);
		} else if (target == "notebook") {
		    if (gNotebook)
			gNotebook.receive(fromUser, toUser, command[4], command[5]);
		} else if (target == "showclick") {
		    gtermShowClick(command[4]);
		}

            } else if (action == "updates_response") {
		feed_list = command[1];
		//if (feed_list.length)
		    //alert(feed_list[0].title+": "+feed_list[0].summary);

            } else if (action == "prompt") {
		GTPrompt = command[1];
		GTCurDirURI = command[2];

            } else if (action == "input") {
		var command_line = command[1];
		var alt_command_line = $("#session-log .curentry .prompt").attr("data-gtermaltcmd");
		if (alt_command_line)
		    command_line = alt_command_line;
		GTSetCommandText(command_line);  // Unescaped text

            } else if (action == "output" || action == "html_output") {
		var appendSelector = gParams.wildcard ? "#session-log .preventry" : "#session-log .curentry";
		if (action == "html_output") {
		    var pagelet_html = '<div class="pagelet">'+command[1]+'</div>\n';
		    var newElem = $(pagelet_html).appendTo(appendSelector);
		    $(appendSelector+" .pagelet .gterm-link").bindclick(otraceClickHandler);
		} else {
		    $(command[1]).appendTo(appendSelector);
		}

		if (!gParams.wildcard) {
		    $("#session-log .curentry .input .command").removeAttr("contentEditable");

		    if ($("#session-log .preventry .prompt").attr("data-gtermsaveduri") &&
			$("#session-log .curentry .prompt").attr("data-gtermsaveduri")) {
			// Remove previous entry for "cdls" consolidation
			$("#session-log .preventry").remove();
		    } else {
			$("#session-log .preventry").removeClass("preventry");
		    }
		    $("#session-log .curentry").addClass("preventry");
		    $("#session-log .curentry").removeClass("curentry");

		    $(GTNextEntry()).appendTo("#session-log");
		}

		var scroll_msec = 0;
		if (scroll_msec && $("#session-log .preventry").length) {
		    var scrollY = $("#session-log .preventry").offset().top + $("#session-log .preventry").height() - 20;
		    $("html:not(:animated), body:not(:animated)").animate({scrollTop: scrollY}, scroll_msec,
                               "linear", function() {$("#session-log .curentry .input .command").focus();});
		} else {
		    // Last prompt will appear at bottom of window
		    $("#session-log .curentry .input .command").focus();
		    ScrollTop(null);
		}

            } else if (action == "terminal") {
		if (!this.terminal)
		    openTerminal();
		var cmd_type = command[1];
		var cmd_arg = command[2];
		if (cmd_type == "alert") {
		    alert(cmd_arg[0]);

		} else if (cmd_type == "errmsg") {
		    GTPopAlert("ERROR: "+cmd_arg[0]);

		} else if (cmd_type == "save_status") {
		    if (gNotebook && cmd_arg[1]) {
			gNotebook.note_params.file = cmd_arg[0];
			gNotebook.note_params.name = cmd_arg[1];
			var nb_label = "NB: "+gNotebook.note_params.name;
			if (!gNotebook.note_params.autosave)
			    nb_label += " (no autosave)";
			$("#menubar-notelabel").text(nb_label)
		    }
		    GTPopAlert("File "+cmd_arg[0]+": "+(cmd_arg[2] || "saved"));

 		} else if (cmd_type == "frame_msg") {
		    try {
			var json_msg = JSON.parse(cmd_arg[2]);
			gFrameDispatcher.receive("", cmd_arg[0], cmd_arg[1], json_msg);
		    } catch (err) {
			console.log("ERROR in frame_msg:", err, content);
		    }

		} else if (cmd_type == "graphterm_chat") {
		    gtermChatStatus(cmd_arg);

		} else if (cmd_type == "graphterm_widget") {
		    var params = cmd_arg[0];
		    var content = cmd_arg[1];
		    if (content)
			content = b64_to_utf8(content);
		    //console.log("graphterm_widget", params, content);
		    var content_type = params.headers.content_type;
		    var response_type = params.headers.x_gterm_response;
		    var response_params = params.headers.x_gterm_parameters;
 		    if (response_type == "pagelet_json") {
			try {
			    var json_obj = JSON.parse(content);
			    GTPageletJSON($("#session-widget"), json_obj);
			} catch (err) {
			    console.log("ERROR in pagelet_json:", err, content);
			}
		    } else if (!response_type || response_type == "pagelet") {
			var widget_opacity = response_params.opacity || "1.0";
			var widget_html = (content_type == "text/html") ? '<div id="session-widget" class="widget" style="opacity: '+widget_opacity+';">'+content+'</div>\n' : '<pre class="plaintext">'+content+'</pre>\n';

			var newElem = $(widget_html).replaceAll("#session-widget");
			if (content)
			    $("#session-widgetcontainer").show();
			else
			    $("#session-widgetcontainer").hide();
		    }

		} else if (cmd_type == "graphterm_output") {
		    var entry_class = "entry"+gPromptIndex;
		    var classes = entry_class;
		    var params = cmd_arg[0];
		    var content = cmd_arg[1];
		    if (content)
			content = b64_to_utf8(content);
		    var content_type = params.headers.content_type;
		    var response_type = params.headers.x_gterm_response;
		    var response_params = params.headers.x_gterm_parameters;
		    if (response_params.classes)
			classes += " " + response_params.classes;
		    //console.log("graphterm_output: params: ", params);
		    if (response_type == "error_message") {
			GTPopAlert(content);
		    } else if (response_type == "clear_terminal") {
			GTClearTerminal();
		    } else if (response_type == "open_terminal") {
			gWebSocket.write([["open_terminal", [response_params.term_name,
							     response_params.command]]]);

		    } else if (response_type == "open_url") {
			var specList = ["location=no", "menubar=no", "toolbar=no"];
			if (response_params.width)
			    specList.push("width="+response_params.width);
			if (response_params.width)
			    specList.push("height="+response_params.height);
			window.open(response_params.url, (response_params.target || "_blank"), specList.join(","));

		    } else if (response_type == "menu_op") {
			GTMenuTrigger(response_params.target, response_params.value);

		    } else if (response_type == "preload_images") {
			GTPreloadImages(response_params.urls);

		    } else if (response_type == "display_finder") {
			ShowFinder(response_params, content);

		    } else if (response_type == "script_op") {
			if (response_params.action == "save") {
			    var commands = [];
			    $("#session-bufscreen .promptrow").each(function() {
				commands.push( $(this).text().substr($(this).find(".gterm-cmd-prompt").text().length+1) );
			    } );
			    var cmdText = commands.join("\n") + "\n";
			    gWebSocket.write([["save_data", {x_gterm_filepath: response_params.filepath,
							     x_gterm_popstatus: "alert",
							     x_gterm_encoding: "base64"}, utf8_to_b64(cmdText)]]);

			} else if (response_params.action == "buffer") {
			    if (response_params.modify) {
				EndFullpage();
				var editText = gScriptBuffer.length ? gScriptBuffer.join("\n")+"\n" : "";
				GTStartEdit(response_params, editText);
			    } else {
				GTBufferScript(content);
			    }
			}

		    } else if (response_type == "eval_js") {
			var output = "";
			try {
			    console.log(content);
			    output = eval(content) || "";
			} catch (err) {
			    output = err+"";
			}
			console.log("> "+output);
			if (response_params.echo == "terminal") {
			    gWebSocket.write([["keypress", output+"\n"]]);
			    if (gSharedCount <= 1)
				gWebSocket.write([["keypress", String.fromCharCode(4)]]);
			} else if (response_params.echo == "chat" && response_params.token) {
			    gWebSocket.write([["chat", response_params.path, response_params.token, output]]);
			}

		    } else if (response_type == "edit_file") {
			EndFullpage();
			GTStartEdit(response_params, content);

		    } else if (response_type == "upload_file") {
			EndFullpage();
			if (gUploadFile) {
			    GTTransmitFile(gUploadFile[0], gUploadFile[1], gUploadFile[2]);
			    gExpectUpload = null;
			} else {
			    var uploadContent = '<div> <b>Select file to upload:</b><input type="file" class="gterm-fileinput" name="gterm-fileinput"></input><div class="gterm-filedrop">or Drag and drop file here</div><input class="gterm-form-button gterm-form-cancel" type="button" value="Cancel"></input> </div>';
			    var uploadHtml = '<div class="pagelet entry '+classes+' gterm-upload" data-gtermpromptindex="'+gPromptIndex+'">'+uploadContent+'</div>\n'
			    gExpectUpload = {file_types: params.expect_type || "any", callback: null};
			    var newElem = $(uploadHtml).appendTo("#session-bufscreen");
			    newElem.find(".gterm-filedrop").rebind('dragover', GTFileDrag);
			    newElem.find(".gterm-filedrop").rebind('dragleave', GTFileDrag);
			    newElem.find(".gterm-filedrop").rebind('drop', GTDropHandler);
			    newElem.find(".gterm-fileinput").rebind("change", GTFileBrowse);
	                    newElem.find(".gterm-form-cancel").bindclick(GTUploadCancel);
			}

 		    } else if (response_type == "pagelet_json") {
			try {
			    var json_obj = JSON.parse(content);
			    GTPageletJSON($(".pagelet."+entry_class), json_obj);
			} catch (err) {
			    console.log("ERROR in pagelet_json:", err, content);
			}

		    } else if (!response_type || response_type == "pagelet" || response_type == "iframe") {
			var pagelet_display = response_params.display || "block";
			var pageletSelector = "#session-bufscreen .pagelet."+entry_class;
			if (pagelet_display.substr(0,4) == "full") {
			    // Hide previous entries, removing previous pagelets for this entry
			    if (pagelet_display == "fullwindow" || pagelet_display == "fullscreen")
				classes += " gterm-fullwindow";
			    if (response_params.form_input) {
				StartFullpage(pagelet_display, false);
				GTStartForm(response_params, gPromptIndex);
			    } else {
				StartFullpage(pagelet_display, true);
			    }
			    $(pageletSelector).remove();
			    if ("scroll" in response_params && response_params.scroll != "down")
				gScrollTop = true;
			} else {
			    // Non-full pagelet entry; show previous entries
			    EndFullpage();
			}
			var current_dir = ("current_directory" in params.headers) ? params.headers.current_directory : "";
			var is_plaintext = (response_type != "iframe") && (content_type != "text/html");
			var pagelet_content;
			if (response_type == "iframe") {
			    pagelet_content = gFrameDispatcher.createFrame(response_params, content);
			} else {
			    pagelet_content = content
			}
			var pagelet_html = is_plaintext ? '<pre class="plaintext entry '+classes+'">'+pagelet_content+'</pre>\n' : '<div class="pagelet entry '+classes+'" data-gtermcurrentdir="'+current_dir+'" data-gtermpromptindex="'+gPromptIndex+'">'+pagelet_content+'</div>\n';

			try {
			    var newElem = $(pagelet_html);
			    if (newElem.hasClass("gterm-blockseq")) {
				var prevBlock = $("#session-bufscreen .pagelet.gterm-blockseq:not(.gterm-toggleblock)");
				if (response_params.overwrite && prevBlock.length == 1 && prevBlock.is($("#session-bufscreen :last-child")) ) {
				    // Overwrite previous blockseq element
				    if (prevBlock.find(".gterm-blockimg").length == 1 && newElem.find(".gterm-blockimg").length == 1) {
					// Replace IMG src attribute
					prevBlock.find(".gterm-blockimg").attr("src", newElem.find(".gterm-blockimg").attr("src"))
				    } else {
					// Replace element
					prevBlock.replaceWith(newElem);
				    }
				    newElem = null;
				} else {
				    // Hide previous blockseq element
				    prevBlock.addClass("gterm-toggleblock").addClass("gterm-togglehide");
				}
			    }

			    if (newElem) {
				newElem = newElem.appendTo("#session-bufscreen");

				if (response_params.form_input) {
				    newElem.find(".gterm-form-button").bindclick(GTFormSubmit);
				    newElem.find(".gterm-help-link").bindclick(GTHelpLink);
				}

				if (response_params.autosize)
				    GTAutosizeIFrame(newElem);
			    }
			    $(pageletSelector+' td .gterm-link:not(.gterm-download)').bindclick(gtermPageletClickHandler);
			    $(pageletSelector+' td img').bind("dragstart", function(evt) {evt.preventDefault();});
			    $(pageletSelector+' .gterm-togglelink').bindclick(gtermLinkClickHandler);
			    $(pageletSelector+' .gterm-iframedelete').bindclick(CloseIFrame);
			    $(pageletSelector+' .gterm-iframeclose').bindclick(CloseIFrame);
			    $(pageletSelector+' .gterm-iframeexpand').bindclick(ExpandIFrame);
			    $(pageletSelector+' .tooltip').tooltipster();
			    GTDropBindings($(pageletSelector+' .droppable'));
			} catch(err) {
			    console.log("GTWebSocket.onmessage: Pagelet ERROR: ", err);
			}
		    }

		} else if (cmd_type == "note_open") {
		    if (!gNotebook) {
			var nb_params = cmd_arg[0];
			gNotebook = new GTNotebook(nb_params);
			$("#terminal").addClass("gterm-notebook");
			if (nb_params.submit && nb_params.form && (nb_params.form == "shared" || nb_params.form == "submitting") )
			    $("#terminal").addClass("gterm-notebook-submit");
			if (cmd_arg[1])
			    alert(cmd_arg[1]);
		    }

		} else if (cmd_type == "note_close") {
		    if (gNotebook)
			gNotebook.close();

		} else if (cmd_type == "note_add_cell") {
		    var cellIndex = cmd_arg[0];
		    var cellType = cmd_arg[1];
		    var beforeCellIndex = cmd_arg[2];
		    var cellInput = cmd_arg[3];
		    if (gNotebook)
			gNotebook.addCell(cellIndex, cellType, beforeCellIndex, cellInput.join("\n"));

		} else if (cmd_type == "note_select_cell") {
		    var cellIndex = cmd_arg[0];
		    if (gNotebook)
			gNotebook.selectCell(cellIndex);

		} else if (cmd_type == "note_select_page") {
		    var cellIndex = cmd_arg[0];
		    var lastIndex = cmd_arg[1];
		    var slide = cmd_arg[2];
		    if (gNotebook)
			gNotebook.selectPage(cellIndex, lastIndex, slide);

		} else if (cmd_type == "note_move_cell") {
		    var cellIndex = cmd_arg[0];
		    var moveUp = cmd_arg[1];
		    if (gNotebook)
			gNotebook.moveCell(cellIndex, moveUp);

		} else if (cmd_type == "note_update_type") {
		    var cellIndex = cmd_arg[0];
		    var cellType = cmd_arg[1];
		    if (gNotebook)
			gNotebook.updateType(cellIndex, cellType);

		} else if (cmd_type == "note_delete_cell") {
		    var deleteIndex = cmd_arg[0];
		    var switchIndex = cmd_arg[1];
		    if (gNotebook)
			gNotebook.deleteCell(deleteIndex, switchIndex);

		} else if (cmd_type == "note_cell_value") {
		    var inputData = cmd_arg[0];
		    var cellIndex = cmd_arg[1];
		    var render = cmd_arg[2];
		    if (gNotebook)
			gNotebook.cellValue(inputData, cellIndex, render);

		} else if (cmd_type == "note_erase_output") {
		    var cellIndex = cmd_arg[0];
		    if (gNotebook)
			gNotebook.eraseOutput(cellIndex);

		} else if (cmd_type == "note_row_update") {
		    gtermShowClickEnd();
                    var update_opts = cmd_arg[0];
		    var update_rows = cmd_arg[5];
		    var update_scroll = cmd_arg[6];
		    if (gNotebook)
			gNotebook.output(update_opts, update_rows, update_scroll);

		} else if (cmd_type == "row_update") {
		    gtermShowClickEnd();
                    var update_opts = cmd_arg[0];
                    var term_width  = cmd_arg[1];
                    var term_height = cmd_arg[2];
                    var cursor_x    = cmd_arg[3];
                    var cursor_y    = cmd_arg[4];
		    var update_rows = cmd_arg[5];
		    var update_scroll = cmd_arg[6];

		    gParams.update_opts = update_opts;

		    var delayed_scroll = false;
		    if (update_opts.alt_mode && !this.alt_mode) {
			this.alt_mode = true;
			if (gSplitScreen)
			    MergeScreen("alt_mode");
			$("#terminal").addClass("gterm-altmode");
			$("#session-screen").hide();
			$("#session-altscreen").show();
		    } else if (!update_opts.alt_mode && this.alt_mode) {
			this.alt_mode = false;
			$("#session-screen").show();
			$("#session-altscreen").hide();
			$("#terminal").removeClass("gterm-altmode");
		    }

		    // Note: Paste operation pastes DOM elements with "span.row" class into screen
                    // Therefore, need to restrict selector to immediate children of #session-screen
		    var nrows = $("#session-screen > span.row").length;

		    if (!update_opts.alt_mode && (update_opts.reset || nrows != update_opts.active_rows)) {
			if (update_opts.reset) {
			    $("#session-screen").empty();
			    nrows = 0;
			    if (gSplitScreen)
				MergeScreen("reset");
			}

			if (gSplitScreen && update_opts.active_rows != 1)
			    MergeScreen("rows");

			if (update_opts.active_rows < nrows) {
			    for (var k=update_opts.active_rows; k<nrows; k++)
				$("#gterm-pre"+k).remove();
			} else if (update_opts.active_rows > nrows) {
			    for (var k=nrows; k<update_opts.active_rows; k++)
				$('<span id="'+"gterm-pre"+k+'" class="row">\n</span>').appendTo("#session-screen");
			    if (gSplitScreen)
				ResizeSplitScreen(true);
			}
		    }

		    if (update_opts.alt_mode && (update_opts.reset || !$("#session-altscreen span.row").length)) {
			gCursorAtEOL = false;
			var preList = ["<hr>"];
			for (var k=0; k<term_height; k++)
			    preList.push('<span id="'+"gterm-alt"+k+'" class="row">\n</span>');
			$("#session-altscreen").html(preList.join(""));
		    }

		    if (update_rows.length)
			gCursorAtEOL = false;
		    for (var j=0; j<update_rows.length; j++) {
			var row_num = update_rows[j][JINDEX];
			var prompt_offset = update_rows[j][JOFFSET];
			var row_span = update_rows[j][JLINE];
			var row_line = "";
			var line_html = "";
			if (prompt_offset) {
			    for (var k=0; k<row_span.length; k++)
				row_line += row_span[k][1];
			    if (gPromptAction && !$.trim(row_line.substr(prompt_offset)))
				gPromptAction = null;  // Blank line after prompt
			    if (row_num == cursor_y) {
				gCursorAtEOL = (cursor_x == row_line.length);
				var cursor_char = gCursorAtEOL ? ' ' : row_line.substr(cursor_x,1);
				line_html += GTEscape(row_line.substr(0,cursor_x), update_opts.pre_offset, prompt_offset)+GTCursorSpan(cursor_char)+GTEscape(row_line.substr(cursor_x+1));
			    } else {
				line_html += GTEscape(row_line, update_opts.pre_offset, prompt_offset);
			    }

			} else {
			    var style_list, span;
			    var row_offset = 0;
			    for (var k=0; k<row_span.length; k++) {
				style_list = row_span[k][0];
				span = row_span[k][1];
				row_line += span;
				
				if (row_num == cursor_y && cursor_x >= row_offset && cursor_x < row_offset+span.length) {
				    var rel_offset = cursor_x - row_offset;
				    line_html += GTEscapeSpan(span.substr(0,rel_offset), style_list);
				    line_html += GTCursorSpan(span.substr(rel_offset,1));
				    line_html += GTEscapeSpan(span.substr(rel_offset+1), style_list);
				} else {
				    line_html += GTEscapeSpan(span, style_list);
				}
				row_offset += span.length;
			    }
			    if (row_num == cursor_y && gPromptAction && _.str.startsWith(row_line, gPromptAction.prompt)) {
				gPromptAction.action();
				gPromptAction = null;
			    }
			    if (row_num == cursor_y && cursor_x >= row_line.length) {
				// Cursor at end of line; pad with spaces to extend to cursor location
				for (var k=row_line.length; k<cursor_x; k++)
				    line_html+= " ";
				// Display cursor
				line_html += GTCursorSpan(' ');
			    }
			}
			var idstr = (update_opts.alt_mode ? "gterm-alt" : "gterm-pre") + row_num;
			var cmd_class = prompt_offset ? " gterm-cmd-line droppable" : "";
			var row_html = '<span id="'+idstr+'" class="row'+cmd_class+'">'+line_html+'\n</span>';
			if ($("#"+idstr).length) {
			    GTDropBindings($(row_html).replaceAll("#"+idstr).filter(".droppable"));
			    if (prompt_offset)
				$("#gterm-pre0 .gterm-cmd-prompt").bindclick(ToggleFooter);

			} else {
			    console.log("graphterm: Error - missing element with ID "+idstr);
			}
		    }
		    if (update_rows.length && !gAltPasteImpl) {
			GTPasteSetup(false);
		    }

		    if (update_scroll.length) {
			for (var j=0; j<update_scroll.length; j++) {
			    var delCommands = $("#session-bufscreen .promptrow").length - MAX_COMMAND_BUFFER;
			    var delOutput = $("#session-bufscreen .entry:not(.promptrow):not(.gterm-ellipsis)").length - MAX_LINE_BUFFER;
			    if (delCommands > 0 || delOutput > 0) {
				var bufRows = $("#session-bufscreen").children();
				var deletingCommand = delCommands > 0;
				var outputCount = 0;
				for (var k=0; k<bufRows.length; k++) {
				    var rowElem = $(bufRows[k]);
				    if (rowElem.hasClass("promptrow")) {
					outputCount = 0;
					if (delCommands > 0) {
					    delCommands -= 1;
					    rowElem.remove();
					    deletingCommand = true;
					} else {
					    deletingCommand = false;
					}
				    } else if (deletingCommand || delOutput > 0){
					outputCount += 1;
					if (deletingCommand || outputCount > 1) {
					    rowElem.remove();
					    delOutput -= 1;
					} else if (outputCount == 1) {
					    rowElem.addClass("gterm-ellipsis");
					    rowElem.html(ELLIPSIS);
					}
				    } else {
					break;
				    }
				}
			    }
			    var newPromptIndex = update_scroll[j][JINDEX];
			    var entry_id = "entry"+newPromptIndex;
			    var prompt_id = "prompt"+newPromptIndex;
			    var prompt_offset = update_scroll[j][JOFFSET];
			    var entry_class = entry_id;
			    var id_attr = "";
			    if (prompt_offset) {
				entry_class += " promptrow";
				id_attr = 'id="'+entry_id+'"'
				if (gPromptIndex == newPromptIndex) {
				    // Repeat entry; remove any previous versions of same entry
				    $("."+"entry"+newPromptIndex).remove();
				    // Hide older entries
				    StartFullpage("", false);
				} else {
				    // New entry; show any older entries
				    EndFullpage();
				}
			    }
			    if (gPromptIndex > 0 && newPromptIndex > gPromptIndex) {
				for (var k=gPromptIndex; k<newPromptIndex; k++) {
				    // Add class to mark old entries
				    $("#session-bufscreen").children(".entry"+k).addClass("oldentry");
				}
			    }
			    gPromptIndex = newPromptIndex;
			    var row_params = update_scroll[j][JPARAMS];
			    var add_class = row_params[JOPTS].add_class;
			    var markup = update_scroll[j][JMARKUP];
			    var row_html;
			    if (row_params[JTYPE] == "pagelet") {
				GTAppendPagelet($("#session-bufscreen"), row_params, entry_class, "pagelet entry "+entry_class+' '+add_class, markup);
				delayed_scroll = true;
			    } else if (row_params[JTYPE] == "markdown") {
				gTempId += 1;
				var cellId = 'gterm-mdcell'+gTempId;
				var cell_html = math_md2html(markup);
				row_html = '<div id="'+cellId+'" class="gterm-notecell-buffered gterm-notecell-markdown '+entry_class+' '+add_class+'">\n'+cell_html+'\n</div>';
				$(row_html).appendTo("#session-bufscreen");
				if (_.str.startsWith(cell_html, MATHCOMMENT))
				    GTApplyMathJax(cellId);
			    } else {
				var row_escaped = (markup == null) ? GTEscape(update_scroll[j][JLINE], update_opts.pre_offset, prompt_offset, prompt_id) : markup;
				row_html = '<pre '+id_attr+' class="row entry '+entry_class+' '+add_class+'">'+row_escaped+"\n</pre>";
				$(row_html).appendTo("#session-bufscreen");
			    }
			    $("#"+entry_id+" .gterm-link:not(.gterm-download)").bindclick(gtermLinkClickHandler);
			    $("#session-bufscreen ."+entry_class+" .gterm-toggleblock .gterm-togglelink").bindclick(gtermLinkClickHandler);
			}
		    }

		    if (gScrollTop) {
			gScrollTop = false;
			ScrollTop(0);
		    } else if ($("body").hasClass("three-d")) {
			// 3D theme
			$("#session-term").scrollTop($("#session-term")[0].scrollHeight - $("#session-term").height())
		    } else if (delayed_scroll) {
			// Delayed scroll (usually to allow image to render)
			setTimeout(ScrollScreen, 200);
		    } else {
			// Scroll to bottom of screen, if not split
			if (!gSplitScreen)
			    ScrollScreen(update_opts.alt_mode);
		    }
		}

            } else if (action == "completed_input") {
		if (command[1].length == 1) {
		    GTSetCommandText(command[1][0]);  // Unescaped text
		    GTSetCursor(gCommandId);
		}
		$("#session-log .curentry .input .command").focus();

            } else if (action == "edit") {
		var editParams = command[1];
		var content = b64_to_utf8(command[2]);

		GTStartEdit(editParams, content);

            } else if (action == "errmsg") {
		GTPopAlert(command[1]);

	    } else {
		console.log("GTWebSocket.onmessage: Invalid message type: "+action);
	    }
	}
	return;

    } catch(err) {
	console.log("GTWebSocket.onmessage", err, err.stack);
	this.write([["errmsg", ""+err]]);
	this.close();
    }
}

GTWebSocket.prototype.onclose = function(e) {
  console.log("GTWebSocket.onclose: ");
  if (!this.opened && !this.closed && !this.failed) {
      this.failed = true;
      alert("Failed to open websocket: "+this.ws_url);
  } else {
      //GTPopAlert("Terminal closed");
  }

  $("#menubar-sessionlabel").text("CLOSED");
  this.closed = true;
}

GTWebSocket.prototype.abort = function() {
  console.log("GTWebSocket.abort: ");
  this.close();
}

GTWebSocket.prototype.close = function() {
  console.log("GTWebSocket.close: ");
  if (this.closed)
    return;

  this.closed = true;
  try {
    this.ws.close();
  } catch(err) {
  }
}

function GTGetCursorOffset(elementId) {
    // Return text cursor offset relative to immediate container node
    // If elementId is specified, and startContainer does not match it,
    // null is returned
    try {
	var range = rangy.getSelection().getRangeAt(0);
	if (elementId) {
	    if (elementId != $(range.startContainer).parent().attr("id"))
		return null;
	}
	return range.startOffset;
    } catch (err) {
	return null;
    }
}

function GTSetCursor(elementId, cursorPos) {
    // Position text cursor within element (default: end of text)
    try {
	if (typeof(cursorPos) == "undefined")
	    cursorPos = $("#"+elementId).text().length;
	var elem = $("#"+elementId);
	var range = rangy.createRange();
	range.setStart(elem[0].childNodes[0], cursorPos);
	range.collapse(true);
	var sel = rangy.getSelection();
	sel.setSingleRange(range);
    } catch(err) {
	console.log("GTSetCursor: ", err);
    }
}

function GTHandleRecall(up_arrow) {
    // otrace version
    // Returns true/false for event handling
    var commandPrefix = (gWebSocket && gWebSocket.terminal) ? "entry" : gCommandPrefix;
    var curIndex = (gWebSocket && gWebSocket.terminal) ? gPromptIndex+1 : gEntryIndex;
    var commandId = commandPrefix+curIndex;
    var commandText = $("#"+commandId).text();
    if (gCommandBuffer == null) {
	gCommandBuffer = commandText;  // First recall; save current command text
	gCommandMatchIndex = gEntryIndex;
	gCommandMatchPrev = null;
    }
    var offset = GTGetCursorOffset(commandId) || 0;
    var prefix = commandText.substr(0,offset);
    var nbsp_offset = prefix.indexOf("\xa0");
    if (nbsp_offset >= 0) {
	prefix = prefix.replace(/[\xa0]/g,"");  // Strip non-breaking spaces
	if (nbsp_offset < offset)
	    offset = offset - 1
    }
    var matchCommand = GTCommandMatch(prefix, !up_arrow);
    if (matchCommand) {
	// Update command (without updating buffer)
	GTSetCommandText(matchCommand, true);
	GTSetCursor(commandId, offset);
    }
    return false;
}

function GTHandleHistory(up_arrow) {
    // Terminal version
    // Returns true/false for event handling
    var commandText = GTGetCurCommandText();
    if (!commandText) {
	// Default shell handling of arrow key, if empty command line
	gShellRecall = true;
	return true;
    }
    commandText = commandText.replace(/^\s+/, ""); // Trim any leading spaces
    if (gCommandBuffer == null) {
	gCommandBuffer = commandText;  // First recall; save current command text
	gCommandMatchIndex = gPromptIndex+1;
	gCommandMatchPrev = null;
    }
    var matchCommand = GTCommandMatch(commandText, !up_arrow);
    if (matchCommand) {
	// Update command (without updating buffer)
	GTSetCommandText(matchCommand, true);
    }
    return false;
}

function AnimatePerspective(persp, rot, millisec, completed) {
    var maxIter = 50;
    var jIter = 0;
    if (!millisec) millisec = 3000;
    function iterCallback() {
	if (jIter >= maxIter) {
	    return completed ? completed() : null;
	}
	jIter += 1;
	var fac = jIter/maxIter;
        var css_prop = "perspective("+persp/fac+") rotateX("+rot*fac+"deg)";
	$(".perspective").css("-webkit-transform", css_prop);
	setTimeout(iterCallback, millisec/maxIter);
    }
    iterCallback();
}

function pasteReadyHandler(evt) {
    var cursorElem = $(".session-screen .cursorspan");
    cursorElem.addClass("cursorhighlight");
    if (gFirefoxBrowser) {
	try {
	    // Save range offsets (used for firefox paste)
	    var cur_sel = rangy.getSelection();
	    var cur_range = cur_sel.getRangeAt(0);
	    
	    if (cur_range.startOffset != 0 || cur_range.endOffset != 0) {
		try {
		    // Try to collapse range to start of text
		    var new_range = rangy.createRange();
		    var startElem = $(cur_range.startContainer);
		    //console.log("pasteReadyHandler:", startElem, cur_range);
		    new_range.setStart(startElem[0], 0);
		    new_range.collapse(true);
		    cur_sel.setSingleRange(new_range);
		    cur_range = cur_sel.getRangeAt(0);
		} catch (err) {
		    //console.log("pasteReadyHandler: ERR", err);
		}
	    }

	    cursorElem.attr("data-gtermpastestart", cur_range.startOffset+"");
	    cursorElem.attr("data-gtermpasteend", cur_range.endOffset+"");
	} catch(err) {}
    }
}

function pasteHandler(evt) {
    if (gPasteActive)
	return true;
    if ((gNotebook && !gNotebook.passthru_stdin) || gForm || gPopupActive)
	return true;

    gPasteActive = true;
    var elem = $(this);
    setTimeout(function() {
	var cursor_char = elem.attr("data-gtermcursorchar");
	var pasteText = "";
	var innerElem = elem.children(".cursorloc");
	gPasteActive = false;

	if (innerElem.attr("contentEditable") == "true") {
	    // Firefox paste implementation (setting inner span to not contentEditable does not work)
	    pasteText = elem.text();
	    if (pasteText) {
		var pasteStart = elem.attr("data-gtermpastestart") || "0";
		var pasteEnd = elem.attr("data-gtermpasteend") || "0";
		var startOffset = parseInt(pasteStart); 
		var endOffset = parseInt(pasteEnd);
		if (startOffset == 0 && endOffset == 0) {
		    pasteText = pasteText.substr(0,pasteText.length-1);
		} else if (startOffset == 1 && endOffset == 1) {
		    pasteText = pasteText.substr(1);
		}
	    }
	} else {
	    // Default paste implementation
	    var cursorElem = innerElem.remove();
	    pasteText = elem.text();
	    elem.empty();
	    elem.append(cursorElem);
	}
	//console.log("pasteHandler:", elem, pasteText.length, pasteText)
	if (gWebSocket && pasteText)
	    gWebSocket.term_input(pasteText);
    }, 100);
}

function GTAltPasteHandler(evt) {
    console.log("GTAltPasteHandler:", gPasteActive, evt, evt.clipboardData);
    if (gPasteActive)
	return true;
    if ((gNotebook && !gNotebook.passthru_stdin) || gForm || gPopupActive)
	return true;

    gPasteActive = true;
    setTimeout(GTAltPasteHandlerAux, 100);
    $("#gterm-pastedirect-content").val("");
    $(".gterm-pastedirect").show();
    $("#gterm-pastedirect-content").focus();
    return true;
}

function GTPasteShortcut(auto) {
    console.log("GTPasteShortcut:");
    if ((gNotebook && !gNotebook.passthru_stdin) || gForm || gPopupActive)
	return true;

    $("#gterm-pastedirect-content").val("");
    $(".gterm-pastedirect").show();
    $("#gterm-pastedirect-content").focus();

    if (auto) {
	gPasteActive = true;
	setTimeout(GTAltPasteHandlerAux, 250);
    }
    return true;
}

function GTAltPasteHandlerAux() {
    gPasteActive = false;
    if (!gPasteDebug)
	$(".gterm-pastedirect").hide();
    var text = $("#gterm-pastedirect-content").val();
    console.log("GTAltPasteHandlerAux: ", text);
    $("#gterm-pastedirect-content").val("");
    $("#gterm-pastedirect-content").unbind("change");
    if (text)
	gWebSocket.term_input(text);
    //setTimeout(function() { ScrollTop(null); }, 100);
}

function GTExportEnvironment(profile) {
    if (window.confirm("WARNING: Do not export environment unless the remote computer is trusted. Malicious remote programs could execute commands on your local computer. CANCEL if not sure.")) {
	if (gWebSocket && gWebSocket.terminal)
	    gWebSocket.write([["export_environment", profile]]);
    }

}

var gSharedCount = 0;
var gShared = {};
function GTJoin(user, joining, setup) {
    console.log("GTJoin: ", user, joining, setup);
    if (joining) {
	gSharedCount += 1;
	if (user && !(user in gShared)) {
	    gShared[user] = 1;
	    $('#gterm-menu-users-list').append('<li class="gterm-menu-user-name" gterm-user="'+user+'"><a href="#">'+user+'</a></li>');
	}
    } else {
	gSharedCount -= 1;
	if (user && (user in gShared)) {
	    $('#gterm-menu-users-list li[gterm-user="'+user+'"]').remove();
	    delete gShared[user];
	}
    }
    $('#gterm-menu-users-count').text(""+gSharedCount);
    $('#gterm-menu-users-container').toggleClass("menu-disabled", !$('#gterm-menu-users-list li').length);
}

var gMenuState = {view: {menubar: true, footer: gMobileBrowser, icons: false, fontsize: "", theme: ""},
		  command: {advanced: false},
                  share: {control: true, private: true, locked: false, tandem: false, webcast: false},
                  notebook: {markdown: false, page: {slide: false}} };
var gMenuObj = null;

function GTMenuSetup() {
    gMenuObj = $("ul.sf-menu").superfish({
	cssArrows: false
    });
    $("ul.sf-menu").on("click", "a", GTMenuHandler);
    GTMenuRefresh();
}

function GTMenuStateUpdate(stateValues, prefix) {
    prefix = prefix || "";
    for (var key in stateValues) {
	var val = stateValues[key];
	if (_.isObject(val)) {
	    GTMenuStateUpdate(val, prefix+key+"_");
	} else {
	    if (key == "view_fontsize" || key == "view_theme"|| key == "view_icons") {
		var selval = key.substr(5);
		GTMenuView(selval+"_"+val, val);
		gMenuState.view[selval] = val;
	    } else {
		GTMenuUpdateToggle(prefix+key, val);
	    }
	}
    }
    // Float menubar for embedded terminal
    if (is_embedded_frame()) {
	$("#terminal").addClass("gterm-embed");
	GTMenuTrigger("view_menubar", false);
    }
}

function GTMenuRefresh() {
    $("ul.sf-menu a[gterm-toggle]").each(function() {
	GTMenuRefreshToggle(this);
    });
    var curTheme = gMenuState.view.theme;
    if (curTheme)
	GTMenuRefreshToggle($('ul.sf-menu a[gterm-state="view_theme_'+curTheme+'"]'))
    var curFontsize = gMenuState.view.fontsize;
    if (curFontsize)
	GTMenuRefreshToggle($('ul.sf-menu a[gterm-state="view_fontsize_'+curFontsize+'"]'))
}

function GTMenuRefreshToggle(target, update, newValue) {
    if (!target || !$(target).length)
	return;
    if (!newValue && newValue !== false && newValue !== "")
	newValue = null;
	
    var stateKey = $(target).attr("gterm-state");
    //console.log("GTMenuRefreshToggle: ", stateKey, update, newValue, target);
    if (!stateKey)
	return null;
    var comps = stateKey.split("_");
    var menuObj = gMenuState;
    while (comps.length > 0) {
	if (!(comps[0] in menuObj))
	    return null;
	if (!_.isObject(menuObj[comps[0]]))
	    break;
	menuObj = menuObj[comps.shift()];
    }
    if (comps.length > 1) {
	$(target).parent().siblings().find("a[gterm-toggle]").attr("gterm-toggle", "false");
	if (update)
	    menuObj[comps[0]] = (newValue !== null) ? newValue : comps[1];
	if (menuObj[comps[0]] == comps[1])
	    $(target).attr("gterm-toggle", "true" );
    } else {
	if (update)
	    menuObj[comps[0]] = (newValue !== null) ? newValue : !menuObj[comps[0]];
	$(target).attr("gterm-toggle", menuObj[comps[0]] ? "true":"false" );
	if (stateKey == "share_private")
	    $("#terminal").toggleClass("gterm-private", menuObj[comps[0]]);
	if (stateKey == "share_locked")
	    $("#terminal").toggleClass("gterm-locked", menuObj[comps[0]]);
    }
    return menuObj[comps[0]];
}

function GTMenuUpdateToggle(stateKey, newValue, force) {
    GTMenuRefreshToggle($('ul.sf-menu a[gterm-state="'+stateKey+'"]'), true, newValue);
    if (stateKey == "share_private")
	$("#terminal").toggleClass("gterm-share", !newValue);
    if (stateKey == "share_webcast")
	$("#terminal").toggleClass("gterm-webcast", newValue);
}

function GTMenuHandler(evt) {
    //console.log("GTMenuHandler: ", evt);
    if (!$(this).hasClass("gterm-menu-splash"))
	GTReceivedUserInput("menuhandler");
    if (gShortcutMenus)
	GTShortcutEnd(false);
    try {
	GTMenuEvent(this);
    } catch (err) {
	console.log("GTMenuHandler: ERROR "+err, err.stack);
    }
    return false;
}

function GTMenuTrigger(stateKey, setValue, inputReceived) {
    if (inputReceived)
	GTReceivedUserInput("menutrigger");
    // Check for exact match
    var elem = $('#gterm-menu a[gterm-state="'+stateKey+'"]');
    if (!elem.length)
	elem = $('#gterm-menu a[gterm-state$="_'+stateKey+'"]');
    if (!elem.length)
	elem = $('#gterm-menu a[gterm-state$="'+stateKey+'"]');

    if (elem.length == 1)
	return GTMenuEvent(elem, setValue, true);

    if (elem.length > 1) {
	alert("Ambiguous menu selection: "+stateKey);
    } else {
	alert("Invalid menu selection: "+stateKey);
    }
    return null;
}

function GTMenuEvent(target, setValue, force) {
    if ($(target).hasClass("gterm-only-controller") && !gParams.controller)
	return false;
    if ($(target).hasClass("gterm-non-controller") && gParams.controller)
	return false;
    if ($(target).hasClass("gterm-non-private") && gMenuState.share.private)
	return false;
    if ($(target).hasClass("gterm-non-locked") && gMenuState.share.locked)
	return false;
    if ($(target).hasClass("gterm-only-notebook") && !gNotebook)
	return false;
    if ($(target).hasClass("gterm-non-notebook") && gNotebook)
	return false;
    var stateKey = $(target).attr("gterm-state");
    //console.log("GTMenuEvent: ", stateKey, target);
    if (!stateKey)
	return null;

    var comps = stateKey.split("_");
    var selectKey = comps.slice(1).join("_");
    var newValue = null;
    if ($(target).hasClass("gterm-toggle-link") || $(target).hasClass("gterm-radio-link"))
	newValue = GTMenuRefreshToggle(target, true, setValue);
    if (comps[0] == "view")
	GTMenuView(selectKey, newValue, force);
    else if (comps[0] == "terminal")
	GTMenuTerminal(selectKey, newValue, force);
    else if (comps[0] == "command")
	GTMenuCommand(selectKey, newValue, force);
    else if (comps[0] == "notebook")
	GTMenuNotebook(selectKey, newValue, force);
    else if (comps[0] == "help")
	GTMenuHelp(selectKey, newValue, force);
    else if (comps[0] == "share")
	GTMenuShare(selectKey, newValue, force);
    else
	GTMenuTop(comps[0], force);
    return true;
}

function GTMenuUpdate(stateKey, newValue) {
    console.log("GTMenuUpdate: ", stateKey, newValue);
    GTMenuUpdateToggle(stateKey, newValue);

    switch (stateKey) {
    case "share_control":
	gParams.controller = newValue;
	GTUpdateController();
	break;

    case "share_tandem":
	break;

    case "share_webcast":
	break;

    case "share_locked":
	break;

    case "share_private":
	break;
    }
}

function GTMenuView(selectKey, newValue, force) {
    console.log("GTMenuView: ", selectKey, newValue, force);
    var comps = selectKey.split("_");
    switch (comps[0]) {
    case "menubar":
	$("#terminal").toggleClass("gterm-menubar-hide", !newValue);
	break;

    case "footer":
	$("#session-term").toggleClass("display-footer", newValue);
	break;

    case "keyboard":   // Commented out in index.html, because it does not work properly
	ScrollScreen();
	$("#headfoot-keyboard").focus();
	break;

    case "top":
	ScrollTop(0);
	break;

    case "bottom":
	ScrollScreen();
	break;

    case "collapse":
	$("#session-bufscreen .oldentry").addClass("gterm-hideoutput");
	ScrollScreen();
	break;

    case "expand":
	$("#session-bufscreen .oldentry").removeClass("gterm-hideoutput");
	ScrollScreen();
	break;

    case "resize":
	handle_resize();
	break;

    case "icons":
	gWebSocket.icons = !!newValue;
	$("#terminal").toggleClass("showicons", gWebSocket.icons);
	break;

    case "fontsize":
	// Select fontsize
	if (gWebSocket.fontsize != comps[1]) {
	    if (gWebSocket.fontsize)
		$("body").removeClass("gterm-fsize-"+gWebSocket.fontsize);
	    if (!comps[1] || comps[1] == "medium") {
		gWebSocket.fontsize = "medium";
	    } else {
		gWebSocket.fontsize = comps[1];
		$("body").addClass("gterm-fsize-"+gWebSocket.fontsize);
	    }
	}
	resizeTerminal();
	break;

    case "theme":
	// Select theme
	var three_d = (newValue.substr(newValue.length-2) == "3d");
	var base_theme = three_d ? newValue.substr(0, newValue.length-2) : newValue;

       if (gWebSocket.theme && gWebSocket.theme != "light")
	   $("body").removeClass(gWebSocket.theme);
       if (base_theme && base_theme != "light")
	   $("body").addClass(base_theme);
         gWebSocket.theme = base_theme;

       if (three_d) {
	   $("body").addClass("three-d");
           $("#session-container").css("height", $(window).height()-100);
	   $("#session-term, #session-roll").css("height", 0.75*$(window).height());
	    //AnimatePerspective(300, 20);
       } else {
	   $("body").removeClass("three-d");
           $("#session-container").css("height", "");
	   $("#session-term, #session-roll").css("height", "");
       }

      break;

    case "save":
	if (gWebSocket && gWebSocket.terminal)
	    gWebSocket.write([["save_prefs", {view: {icons: gMenuState.view.icons, fontsize: gMenuState.view.fontsize, theme: gMenuState.view.theme} }]]);
	break;
    }
}

function GTMenuShare(selectKey, newValue, force) {
    console.log("GTMenuShare: ", selectKey, newValue, force);
    if (!gWebSocket)
	return;
    if (gParams.controller || (selectKey == "control" && !gMenuState.share.locked)) {
    } else {
	alert("Only controller can update share settings");
    }
	
    newValue = !!newValue;
    console.log("GTMenuShare: ", selectKey);
    switch (selectKey) {
    case "control":
	gParams.controller = newValue;
	GTUpdateController();
	break;
    case "private":
	if (!newValue && !force && !window.confirm('Make terminal viewable by other users?')) {
	    GTMenuUpdateToggle("share_private", false);
	    return;
	}
	$("#terminal").toggleClass("gterm-share", !newValue);
	break;
    case "locked":
	if (!newValue && !force && !window.confirm('Make terminal controllable by other users?')) {
	    GTMenuUpdateToggle("share_locked", false);
	    return;
	}
	break;
    case "tandem":
	if (newValue && !force && !window.confirm('Tandem (or simultaneous) control is an experimental feature and may be unstable. Proceed?')) {
	    GTMenuUpdateToggle("share_tandem", false);
	    return;
	}
	break;
    case "webcast":
	if (!gParams.state_values.allow_webcast) {
	    GTMenuUpdateToggle("share_webcast", false);
	    alert("Webcasting not permitted for user")
	    return;
	}
	if (newValue && !force && !window.confirm('Make terminal publicly viewable ("webcast")?')) {
	    GTMenuUpdateToggle("share_webcast", false);
	    return;
	}
	$("#terminal").toggleClass("gterm-webcast", newValue);
	gWebSocket.webcast = newValue;
	break;
    }
    // Update value for all users
    gWebSocket.write([["update_params", "share_"+selectKey, newValue]])
}

function GTMenuTop(topKey, force) {
    //console.log("GTMenuTop: ", topKey, force);
    switch (topKey) {
    case "steal":
	if (!gMenuState.share.locked) {
	    gParams.controller = true;
	    GTUpdateController();
	    gWebSocket.write([["update_params", "share_control", true]]);
	}
	break;
    case "home":
	if (gParams.controller && gWebSocket)
	    gWebSocket.term_input("cd; gls\n");
	break;
    case "new":
	OpenNew();
	break;
    case "detach":
	DetachSession()
	break;
    case "run":
	gNotebook.handleCommand("runbutton", true);
	break;
    }
}

function GTMenuTerminal(selectKey, newValue, force) {
    console.log("GTMenuTerminal: ", selectKey, newValue, force);
    switch (selectKey) {
    case "new":
	OpenNew();
	break;
    case "full":
	load("full");
	break;
    case "reload":
	window.location.reload();
	break;
    case "steal":
	StealSession();
	break;
    case "detach":
	DetachSession()
	break;
    case "reconnect":
	ReconnectHost();
	break;
    case "kill":
	if (force || window.confirm("Kill terminal?")) {
	    if (gWebSocket && gWebSocket.terminal)
		gWebSocket.write([["kill_term"]]);
	}
	break;
    case "clear":
	if (newValue && !force && !window.confirm('Clear screen?')) {
	    return
	}
	GTClearTerminal();
	if (gWebSocket && gWebSocket.terminal)
	    gWebSocket.write([["clear_term"]]);
	//text = "\x01\x0B";  // Ctrl-A Ctrl-K
	break;
    case "home":
	if (gWebSocket)
	    gWebSocket.term_input("cd; gls\n");
	break;
    case "export":
	GTExportEnvironment(false);
	break;
    case "append":
	GTExportEnvironment(true);
	break;
    case "paste":
	GTPasteSpecialBegin();
	break;
    }
}

function GTMenuCommand(selectKey, newValue, force) {
    var advanced = gMenuState.command.advanced;
    console.log("GTMenuCommand: ", selectKey, newValue, force, advanced);
    var cmd = "";
    switch (selectKey) {
    case "advanced":
	break;
    case "copy":
	cmd = advanced ? "cp " : "cp OLD_FILE NEW_FILE_OR_DIR";
	break;
    case "delete":
	cmd = advanced ? "rm " : "rm FILE";
	break;
    case "eof":
	cmd = String.fromCharCode(4);
	break;
    case "file":
	cmd = advanced ? "gvi " : "gvi #filename";
	break;
    case "home":
	cmd = "cd; gls";
	break;
    case "interrupt":
	cmd = String.fromCharCode(3);
	break;
    case "ipython":
	cmd = advanced ? "gipython" : "gipython #optional_notebook_name";
	break;
    case "list":
	cmd = advanced ? "gls" : "gls #filename_pattern";
	break;
    case "nbserver":
	if (!gParams.nb_server) {
	    alert("nb_server option not enabled")
	} else {
	    cmd = "gnbserver";
	}
	break;
    case "python":
	cmd = advanced ? "gpython" : "gpython #optional_notebook_name";
	break;
    case "rename":
	cmd = advanced ? "mv " : "mv OLD_FILE NEW_FILE_OR_DIR";
	break;
    case "make":
	cmd = advanced ? "mkdir " : "mkdir DIRECTORY_NAME";
	break;
    case "chat":
	cmd = "gchat 2> $GTERM_SOCKET 0<&2 | gfeed > $GTERM_SOCKET &";
	break;
    case "upload":
	cmd = advanced ? "gupload" : "gupload #optional_filename";
	break;
    case "download":
	cmd = advanced ? "gdownload" : "gdownload #filename(s)";
	break;
    case "yweather":
	cmd = advanced ? "yweather " : "yweather #location";
	break;
    case "parent":
	if (is_embedded_frame()) {
	    try {
		if (window.parent.gWebSocket && window.parent.gWebSocket.terminal)
		    window.parent.GTTerminalInput(String.fromCharCode(3));
	    } catch(err) {
		alert("Failed to send command to parent: "+err);
	    }
	}
	break;
    case "upload":
	cmd = advanced ? "gupload" : "gupload ";
	break;
    }
    if (cmd && gWebSocket && gWebSocket.terminal) {
	if (advanced && !_.str.endsWith(cmd, " "))
	    cmd += "\n";
	GTTerminalInput(cmd);
    }
}

function GTMenuNotebook(selectKey, newValue, force) {
    console.log("GTMenuNotebook: ", selectKey, newValue, force);

    if (_.str.startsWith(selectKey, "new_")) {
        if (selectKey == "new_pylab") {
	    gWebSocket.write([["paste_command", 'python -i $GTERM_DIR/bin/gpylab.py\ngterm.open_notebook()\n']]);
	    //gWebSocket.write([["paste_command", 'python -i $GTERM_DIR/bin/gpylab.py\n']]);
	    //setTimeout(GTActivateNotebook, 200);
        } else if (selectKey == "new_r") {
	    gWebSocket.write([["paste_command", 'R -q\nsource(paste(Sys.getenv("GTERM_DIR"), "/bin/gterm.R", sep=""))\ngnotebook()\n']]);
        } else {
	    GTActivateNotebook("");
	}
    } else if (selectKey == "open") {
	var filepath = $.trim(window.prompt("Notebook file (or terminal path): "));
	var prompts = "";
	if (!filepath)
	    prompts = $.trim(window.prompt("Shell prompts: "));
	GTActivateNotebook(filepath, prompts ? prompts.split(/\s+/) : []);
    } else {
	if (!gNotebook)
	    return;
	gNotebook.handleCommand(selectKey, newValue);
    }
}

function GTMenuHelp(selectKey, newValue, force) {
    console.log("GTMenuHelp: ", selectKey, newValue, force);
    if (selectKey == "about")
	GTermAbout();
    else if (selectKey == "updates")
	CheckUpdates();
    else
	GTermHelp();
}

function gtermMenuClickHandler(event) {
    var idcomps = $(this).attr("id").split("-");
    console.log("gtermMenuClickHandler", $(this).attr("id"), idcomps[1]);
    var text = "";
    switch (idcomps[1]) {
    case "kbrd":
	$("#headfoot-keyboard").focus();
	break;
    case "control":
	$("#headfoot-control").toggleClass("gterm-headfoot-active");
	gControlActive = $("#headfoot-control").hasClass("gterm-headfoot-active");
	break;
    case "home":
	if (gWebSocket)
	    gWebSocket.term_input("cd; gls\n");
	break;
    case "top":
	ScrollTop(0);
	break;
    case "up":
	if (HandleArrowKeys(38))
	    text = "\x1b[A";
	break;
    case "down":
	if (HandleArrowKeys(40))
	    text = "\x1b[B";
	break;
    case "delete":
	text = "\x7f";
	break;
    case "left":
	if (HandleArrowKeys(37))
	    text = "\x1b[D";
	break;
    case "right":
	if (HandleArrowKeys(39))
	    text = "\x1b[C";
	break;
    case "tab":
	text = "\x09";
	break;
    case "command":
	GetFinder("command");
	break;
    case "options":
	GetFinder("options");
	break;
    case "file":
	GetFinder("file");
	break;
    case "enter":
	text = (gAndroid ? GetCursorText() : "") + "\n";
	if (gShowingFinder)
	    HideFinder();
	break;
    }
    if (text.length)
	GTTerminalInput(text, false);
    return false;
}

function GTPopAlert(text, is_html) {
    if (!is_html) {
	text = '<div class="gterm-alert gterm-prewrap">'+GTPreserveLinebreaks(GTEscape(text))+'</div>';
    }
    $("#gterm-alertarea-content").html(text);

    popupShow("#gterm-alertarea", null, null, "alert");
}

function GTPasteSpecialBegin(event) {
    var keyEvent = gFirefoxBrowser ? "keypress" : "keydown";
    $("#gterm-pastearea-content").val("");
    $("#gterm-pastearea-content").bind(keyEvent, pasteKeyHandler);
    popupShow("#gterm-pastearea", GTPasteSpecialEnd, null, "paste");
}

function GTPasteSpecialEnd(buttonElem) {
    var action = $(buttonElem).attr("name");
    var text = $("#gterm-pastearea-content").val();
    if (text && action == "paste_text")
	gWebSocket.term_input(text);
    popupClose();
    var keyEvent = gFirefoxBrowser ? "keypress" : "keydown";
    $("#gterm-pastearea-content").unbind(keyEvent, pasteKeyHandler);
    setTimeout(ScrollTop, 200);
}

function gtermCloneSession(event) {
    // Clone session, if embedded
    if (!is_embedded_frame())
	return;
    var url = self.location.pathname;
    if (!_.str.endsWith(url, "/watch/"))
	url += "watch/";
    url += '?qauth='+getAuth();
    window.open(url, "_blank");
}

function gtermAlert(event) {
    gtermAlertSend(!$("#terminal").hasClass("gterm-alert"));
}

function gtermAlertSend(status) {
    gWebSocket.write([["chat", "", "", "alert"+(!!status)+"\n"]]);
    gtermAlertUpdate(status);
}

function gtermAlertUpdate(status) {
    $("#terminal").toggleClass("gterm-alert", status);
}

function gtermChatStatus(status) {
    gChat = status;
    $("#session-term").toggleClass("gterm-chat", gChat);
}

function gtermChatHandler(event) {
    gChatText = "";
    $("#gterm-chatarea-content").val("");
    popupShow("#gterm-chatarea", gtermChatAction, gtermChatConfirmClose, "chat");
}

gChatText = null;
function gtermChatConfirmClose() {
  if (gChatText == $("#gterm-chatarea-content").val()) {
    // No changes
    return true
  }
  return false;
}

function gtermChatAction(buttonElem) {
    var action = $(buttonElem).attr("name");
    var text = $("#gterm-chatarea-content").val().replace(/\xa0/g, " ").replace(/\r\n/g,"\n").replace(/\r/g,"\n").replace(/\n/g," ");
    //console.log("popupButton", action, text);
    if (action == "send")
	gWebSocket.write([["chat", "", "", text+"\n"]]);
    popupClose();
}

var gShowClickInterval = 250;
function gtermShowClick(msg) {
    $("#"+msg.targetId).addClass("gterm-show-click");
}

function gtermShowClickEnd() {
    $(".gterm-show-click").removeClass("gterm-show-click");
}

function gtermShowClickPaste(text, file_url, options, targetId) {
    //console.log("gtermShowClickPaste: ", text, file_url, options, targetId);
    var msg = {targetId: targetId};
    gtermShowClick(msg);
    if (gSharedCount > 1 && gWebSocket && gParams.controller)
	gWebSocket.write([["send_msg", "*", "showclick", msg]]);

    if (targetId && gSharedCount > 1) {
	setTimeout(function() {gtermClickPaste(text, file_url, options);}, gShowClickInterval);
    } else {
	gtermClickPaste(text, file_url, options);
    }
}

function gtermClickPaste(text, file_url, options) {
    gWebSocket.write([["click_paste", text, file_url, options]]);
    if (!gSplitScreen)
	SplitScreen("paste");
}

function gtermInterruptHandler(event) {
    console.log("gtermInterruptHandler");
    if (gWebSocket && gWebSocket.terminal)
	gWebSocket.term_input(String.fromCharCode(3));
}

function gtermLinkClickHandler(event) {
    var contextMenu = gControlActive;
    GTReceivedUserInput("click");
    var file_url = "";
    var options = {};

    if ($(this).hasClass("gterm-cmd-prompt")) {
	if (contextMenu) {
	    if (gWebSocket) {
		var cmdText = $(this).parent().text().substr($(this).text().length+1);
		cmdText = cmdText.substr(0,cmdText.length-1);
		gWebSocket.term_input(cmdText);
	    }
	    return false;
	}
	var cmd_output = $(this).parent().nextUntil(".promptrow");
	cmd_output.toggleClass("gterm-hideoutput");
	$(this).parent().toggleClass("gterm-hideoutput");

    } else if ($(this).hasClass("gterm-cmd-text")) {
	gtermClickPaste($(this).text(), file_url, options);

    } else if ($(this).hasClass("gterm-cmd-path")) {
	file_url = makeFileURL($(this).attr("href"));
	gtermClickPaste("", file_url, options);

    } else if ($(this).hasClass("gterm-togglelink")) {
	$(this).parent(".gterm-toggleblock").toggleClass("gterm-togglehide");
    }

    if (contextMenu) {
	alert("Context menu not yet implemented");
	return false;
    }

    //console.log("gtermLinkClickHandler", file_url, options);
    return false;
}

function gtermPageletClickHandler(event) {
    var confirm = $(this).attr("data-gtermconfirm");
    if (confirm) {
	if (!window.confirm(confirm)) {
	    return false;
	}
    }

    if ($(this).attr("download")) {
	return false;
    }

    var targetId = event.target ? $(event.target).attr("id") : null;

    var contextMenu = gControlActive;
    GTReceivedUserInput("click");
    var text = $(this).text();
    var pagelet = $(this).closest(".pagelet");
    var href = $(this).attr("href");
    var file_url = makeFileURL(href);

    if (contextMenu) {
	alert("Context menu not yet implemented");
	return false;
    }

    var options = {enter: true}
    options.command = $(this).attr("data-gtermcmd");
    var cd_command = (options.command.indexOf("cd ") == 0);
    options.clear_last = (pagelet.length && cd_command) ? pagelet.attr("data-gtermpromptindex") : "0";

    var noffset = options.command.indexOf(" %[notebook]");
    if (noffset > -1) {
	var filepath = "";
	if (_.str.startsWith(href, FILE_URI_PREFIX))
	    filepath = href.substr(FILE_URI_PREFIX.length);
	else if (_.str.startsWith(href, FILE_PREFIX))
	    filepath = href.substr(FILE_PREFIX.length);
	filepath = filepath.substr(filepath.indexOf("/"));
	var qindex = filepath.indexOf("?");
	if (qindex > -1)
	    filepath = filepath.substr(0,qindex);

	var prompts = options.command.substr(noffset+" %[notebook]".length).split(/\|/);
	options.command = options.command.substr(0,noffset) + "  # Notebook: "
	if (noffset == 0) {
	    // Shell notebook
	    GTActivateNotebook(filepath, [])
	} else {
	    gPromptAction = {prompt: prompts[0],
			     action: function () {
				 GTActivateNotebook(filepath, prompts);
			     }
			    }
	}
    }

    //console.log("gtermPageletClickHandler", file_url, options);
    if (targetId) {
	gtermShowClickPaste("", file_url, options, targetId);
    } else {
	gtermClickPaste(text, file_url, options);
    }
    return false;
}

function gtermBottomSelectHandler(event) {
    var idcomps = $(this).attr("id").split("-");
    var selectedOption = $(this).val();
    console.log("gtermBottomSelectHandler: ", idcomps[1], selectedOption);

    GTReceivedUserInput("botselect");
    var text = "";
    switch (idcomps[1]) {
    case "key":
	$(this).val(1);

	if (selectedOption == "space")
	    text = String.fromCharCode(32);
	else if (selectedOption == "escape")
	    text = String.fromCharCode(27);
	else if (selectedOption == "noenter")
	    text = "no\n";
	else if (selectedOption == "yesenter")
	    text = "yes\n";
	else if (selectedOption == "controla")
	    text = String.fromCharCode(1);
	else if (selectedOption == "controlc")
	    text = String.fromCharCode(3);
	else if (selectedOption == "controld")
	    text = String.fromCharCode(4);
	else if (selectedOption == "controle")
	    text = String.fromCharCode(5);
	else if (selectedOption == "controlk")
	    text = String.fromCharCode(11);
	else if (selectedOption == "controlz")
	    text = String.fromCharCode(26);
	break;
    }
    if (text.length)
	GTTerminalInput(text, false);
    return false;
}

function gtermFinderClickHandler(event) {
    // Paste selected Command/Option/File
    // TODO: If empty command line and File finder, display context menu,
    // and paste command as well as filepath
    var contextMenu = gControlActive;
    GTReceivedUserInput("click");
    var text = $(this).text();
    var file_url = makeFileURL($(this).attr("href"));

    if (contextMenu) {
	alert("Context menu not yet implemented");
	return false;
    }

    var options = {clear_last: 0};
    options.command = $(this).attr("data-gtermcmd");
    console.log("gtermFinderClickHandler", text, file_url, options);
    gtermClickPaste("", file_url, options);
    HideFinder();
    return false;
}

function otraceClickHandler(event) {
    var prev_command = $("#session-log .preventry").length ? GTStrip($("#session-log .preventry .input .command").text()) : "";
    var cur_command = GTStrip(GTGetCurCommandText());
    var fileURI = createFileURI($(this).attr("data-gtermuri") || $(this).attr("href"));
    var filepath = GTGetFilePath(fileURI, GTCurDirURI);

    console.log("otraceClickHandler", GTCurDirURI);
    if (cur_command.length) {
	GTSetCommandText(cur_command + " " + filepath);
	GTSetCursor(gCommandId);
	$("#session-log .curentry .input .command").focus();
	GTExpandCurEntry(false);
    } else {
	var new_command = $(this).attr("data-gtermcmd");
	var command_line;
	if (new_command.indexOf("%(path)") >= 0)
	    command_line = new_command.replace(/%\(path\)/g, filepath);
	else
	    command_line = new_command+" "+filepath;

	if ((new_command == "cdls" || new_command.indexOf("cdls ") == 0) &&
	    (prev_command == "cdls" || prev_command.indexOf("cdls ") == 0)) {
	    // Successive open commands; consolidate by preparing to overwrite previous entry
	    var savedURI = $("#session-log .preventry .prompt").attr("data-gtermsaveduri");
	    if (!savedURI) {
		savedURI = $("#session-log .preventry .prompt").attr("data-gtermuri");
	        $("#session-log .preventry .prompt").attr("data-gtermsaveduri", savedURI);
	    }
	    var alt_filepath = GTGetFilePath(fileURI, savedURI);
	    var alt_command_line = new_command+" "+alt_filepath;
	    $("#session-log .curentry .prompt").attr("data-gtermsaveduri", savedURI);
	    $("#session-log .curentry .prompt").attr("data-gtermaltcmd", alt_command_line);
	    GTExpandCurEntry(true);
	} else {
	    GTExpandCurEntry(false);
	}
	gWebSocket.write([["input", command_line, null]]);
	gCommandBuffer = null;
    }
    return false;
}

function GTExpandCurEntry(expand) {
    // Expand current entry to fill window
    if (expand) {
	$("#session-log .curentry").addClass("open-expanded");
	$("#session-log .curentry").css("min-height", $(window).height()-30);
    } else {
	$(".open-expanded").css("min-height", "");
	$(".open-expanded").removeClass("open-expanded");
    }
}

function GTShortcutPrefixKey(evt) {
    // Control-J prefix: menu shortcuts
    if (gControlQ) {
	gControlQ = false;
	return false;
    }
    if (gShortcutMenus) {
	GTShortcutEnd(true);
    } else {
	$("#terminal").addClass("gterm-shortcut-mode");
	gShortcutMenus = [$("#gterm-menu")];
    }
    return true;
}

function keydownHandler(evt) {
    if (gPasteActive)
	return true;
    var activeTag = "";
    var activeType = "";
    var activeElem = $(document.activeElement);

    if (evt.which == 81 && evt.ctrlKey) {
	// Control-Q prefix: menu shortcuts
	gControlQ = true;
    } else if (evt.which == 74 && evt.ctrlKey && GTShortcutPrefixKey(evt)) {
	// Control-J prefix: menu shortcuts
	return false;
    }

    if (!gFirefoxBrowser && gNotebook && !gNotebook.passthru_stdin && !gNotebook.handling_tab && !gNotebook.prefix_key && evt.which == 77 && evt.ctrlKey) {
	// Control-M prefix: notebook shortcuts
	gNotebook.prefix_key = true;
	return false;
    }

    if (gNotebook && !gNotebook.passthru_stdin && (evt.which == 9 || evt.which == 8 || evt.which == 127)) {
	// Notebook mode: TAB/BSP/DEL
	if (gNotebook.handling_tab) {
	    if (evt.which == 9) {
		// Note: BSP/DEL is handled normally if handling TAB
		gWebSocket.write([["complete_cell", "\x09"]]);
		return false;
	    }
	} else {
	    // Not handling TAB yet
	    var cellParams = gNotebook.cellParams[gNotebook.curIndex];
	    var textElem = $("#"+gNotebook.getCellId(gNotebook.curIndex)+"-textarea");
	    var caretPos = textElem.prop("selectionStart");
	    if (caretPos == textElem.prop("selectionEnd")) {
		var textVal = textElem.val();
		var lines = textVal.substr(0,caretPos).replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
		var lastLine = lines[lines.length-1];
		var prefix = $.trim(lastLine);
		if (!prefix) {
		    // Blank line prefix
		    var tabOffset = lastLine.length % 4;
		    if (evt.which == 9) {
			// TAB: insert 4-space tab
			textElem.val( textVal.substr(0,caretPos)+"    ".substr(0,4-tabOffset)+textVal.substr(caretPos) );
			textElem.caret(caretPos+4-tabOffset);
			return false;
		    } else if (lastLine) {
			// BSP/DEL: delete to previous tab
			tabOffset = tabOffset ?  tabOffset : 4;
			textElem.val( textVal.substr(0,caretPos-tabOffset)+textVal.substr(caretPos) );
			textElem.caret(caretPos-tabOffset);
			return false;
		    }
		} else if (evt.which == 9 && (cellParams.cellType in MARKUP_TYPES)) {
		    // TAB: ignored for non-blank markup line prefix
		    return false;
		} else if (evt.which == 9 && gWebSocket) {
		    // TAB: completion for non-blank code line prefix
		    gNotebook.handling_tab = [caretPos, prefix];
		    gWebSocket.write([["complete_cell", prefix]]);
		    return false;
		}
	    }
	}
    }

    if (GTCaptureInput())
	return true;

    if (gDebugKeys)
	console.log("graphterm.keydownHandler: ", evt.keyCode, evt.which, evt.charCode, evt);

    if ((gMacPlatform && evt.metaKey && evt.which == 86) || ((!gMacPlatform && evt.ctrlKey && matchCodes(evt, 22)))) {
	// Ctrl-V or Meta-V for paste
	return GTPasteShortcut(true);
    }

    if (gIExplorer && evt.which == 13 && !evt.ctrlKey && WebSocket && gWebSocket.terminal) {
	// Special handling of Enter key for MSIE
	return AjaxKeypress(evt);
    }

    GTExpandCurEntry(false);

    if (evt.which >= 33 && evt.which <= 46) {
	// Special keys (arrow keys etc.)
	if (evt.charCode == 0) {
	    // Note: Command recall not properly implemented for terminal; default to shell
	    if (gWebSocket && gWebSocket.terminal)
		return AjaxKeypress(evt);
	}
    }

    if (evt.which == 38 || evt.which == 40) {
	// Up/down arrows
	return GTHandleRecall((evt.which == 38));
    }
    gCommandBuffer = null; // Clear command recall buffer

    if (gFirefoxBrowser)  // Firefox handles TAB/ESC/DEL on keypress
	return true;

    if (evt.which == 9) {
	// TAB key
	var text = GTStrip(GTGetCurCommandText());
	if (gWebSocket && gWebSocket.terminal)
	    gWebSocket.term_input(String.fromCharCode(9));
	else if (gWebSocket && !gParams.wildcard)
	    gWebSocket.write([["incomplete_input", text]]);
	return false;
    } else if (evt.which == 27) {
	// ESC key
	gWebSocket.term_input(String.fromCharCode(27));
	return false;
    } else if (evt.which == 8 || evt.which == 127) {
	// BSP/DEL key
	if (gWebSocket && gWebSocket.terminal) {
	    gWebSocket.term_input(String.fromCharCode(127), true);
	    return false;
	}
    }

    if (gWebkitBrowser && evt.ctrlKey && evt.which >= 65) {
	// Control keys on Safari
	if (gWebSocket && gWebSocket.terminal)
	    return AjaxKeypress(evt);
    }

    return true;
}

function matchCodes(evt, code) {
    return (evt.which == code || evt.which == (code+64) || evt.which == (code+96));
}

function pasteKeyHandler(evt) {
    //console.log("graphterm.pasteKeyHandler: code ", evt.keyCode, evt.which, evt);
    if (evt.ctrlKey && matchCodes(evt, gPasteSpecialKeycode)) {
	GTPasteSpecialEnd($("#gterm-pastearea-pastetext"));
	return false;
    }
    return true;
}

var gAltKeyboardBuffer = "";
function AltKeyboardFocus(evt) {
    var cursorElem = $("#gterm-pre0 .cursorspan");
    gAltKeyboardBuffer = cursorElem.length ? prevElem[0].previousSibling.nodeValue : GTGetCurCommandText();
    $("#headfoot-keyboard").text(gAltKeyboardBuffer);
    GTSetCursor("headfoot-keyboard");
}
function AltKeyboardBlur(evt) {
    $("#headfoot-keyboard").text("");
    gAltKeyboardBuffer = "";
}
function AltKeyboardHandler(evt) {
    var text = $("#headfoot-keyboard").text();
    var newchars = text.length - gAltKeyboardBuffer.length;
    //serverLog("AltKeyboardHandler: "+newchars+" "+text+":"+gAltKeyboardBuffer+":"+evt.which+":"+evt.keyCode+":"+evt.charCode+" "+(text.length ? text.charCodeAt(text.length-1):""));
    if (newchars > 0) {
	// Replace no-break space (\xa0) with normal space
	var newtext = text.substr(gAltKeyboardBuffer.length).replace(/\xa0/g, " ");
	// NOTE: Android autocorrect can corrupt input when Enter is pressed!
	GTTerminalInput(newtext, false);
    } else if (newchars < 0) {
	for (var j=0; j<-newchars; j++)
	    GTTerminalInput(String.fromCharCode(127), false)
    }
    if (evt.keyCode == 13) {
	$("#headfoot-keyboard").text("");
	gAltKeyboardBuffer = "";
    } else {
	gAltKeyboardBuffer = text;
    }
    return false;
}

function keypressHandler(evt) {
    if (gPasteActive)
	return true;

    if (gDebugKeys)
	console.log("graphterm.keypressHandler: code ", evt.keyCode, evt.which, evt);

    if (evt.which == 106 && evt.ctrlKey && gShortcutMenus) {
	// Control-J prefix: ignore duplicate in Firefox
	return false;
    }

    if (gFirefoxBrowser && gNotebook && !gNotebook.passthru_stdin && !gNotebook.handling_tab && !gNotebook.prefix_key && evt.which == 109 && evt.ctrlKey) {
	// Control-M prefix: notebook shortcuts
	gNotebook.prefix_key = true;
	return false;
    }

    if (gWebSocket && gWebSocket.terminal)
	return AjaxKeypress(evt);
    
    var activeTag = "";
    var activeType = "";
    var activeElem = $(document.activeElement);
    
    if (evt.which == 27)
	return false;

    if (GTCaptureInput())
	return true;

    if (evt.which == 13) {
	// Enter key
	var text = GTStrip(GTGetCurCommandText());  // Unescaped text
	if (!text && gAndroid)
	    text = GetCursorText();
	if (gScriptBuffer.length && (evt.ctrlKey || gControlActive)) {
	    // Scripted command
	    text = gScriptBuffer.shift();
	    GTSetCommandText(text)
	}

	gWebSocket.write([["input", text, null]]);

	if (gParams.wildcard) {
	    GTSetCommandText(text);  // Unescaped text
	    $("#session-log .curentry .input .command").removeAttr("contentEditable");
	    $("#session-log .preventry").removeClass("preventry");
	    $("#session-log .curentry").addClass("preventry");
	    $("#session-log .curentry").removeClass("curentry");
	    
	    $(GTNextEntry()).appendTo("#session-log");
	    $("#session-log .curentry .input .command").focus();
	}

	return false;
    }

    if ((gMacPlatform && evt.metaKey && evt.which == 86) || ((!gMacPlatform && evt.ctrlKey && matchCodes(evt, 22)))) {
	// Ctrl-V or Meta-V for paste
	return GTPasteShortcut(true);
    }

    return true;
}

function HandleArrowKeys(keyCode) {
    //console.log("HandleArrowKeys", keyCode, gCursorAtEOL, gShellRecall);
    if (!gCursorAtEOL || gWebSocket.alt_mode || gShellRecall)
	return true;
    // Cursor at end of command line
    if (keyCode == 38 || keyCode == 40) {
	// Up/down arrows; command history recall
	return GTHandleHistory((keyCode == 38));

    } else if (keyCode == 39) {
	// Right arrow; command history completion
	return CompleteCommand()
    }
    // Default handling
    return true;
}

function CompleteCommand(enter) {
    // Returns false if completed command was sent, and true otherwise (for event propagation)
    // If enter, newline is appended to command (after a delay)
    if ($("#gterm-pre0 .cmd-completion").length) {
	var comptext = $("#gterm-pre0 .cmd-completion").text();
	$("#gterm-pre0 .cmd-completion").text("");
	if (comptext) {
	    if (enter)
		comptext += "\n";
	    gWebSocket.term_input(String.fromCharCode(5)+comptext, false, true);
	    return false;
	}
    }
    return true;
}

function AjaxKeypress(evt) {
    // From ajaxterm.js
    if (!evt) var evt = window.event;

    if (evt.metaKey && !evt.ctrlKey)
	return true;

    if (!evt.charCode && (evt.which >= 37 && evt.which <= 40)) {
	if (!HandleArrowKeys(evt.which))
	    return false
    }

    //	s="kp keyCode="+evt.keyCode+" which="+evt.which+" shiftKey="+evt.shiftKey+" ctrlKey="+evt.ctrlKey+" altKey="+evt.altKey;
    //	debug(s);
    //  return false;
    //  else { if (!evt.ctrlKey || evt.keyCode==17) { return; }

    var k = "";
    var clearForm = false;
    var kc = 0;

    if (evt.keyCode)
	kc = evt.keyCode;

    if (evt.which)
	kc = evt.which;

    if (gDebugKeys)
	console.log("graphterm.AjaxKeypress1", gControlActive, kc, evt.ctrlKey, evt);

    if (kc == 13 || (gWinBrowser && !gFirefoxBrowser && kc == 10 && evt.ctrlKey) ) {  // Enter key
	if (gScriptBuffer.length && (evt.ctrlKey || gControlActive)) {
	    // Scripted command
	    var scriptText = gScriptBuffer.shift();
	    if (scriptText.length)
		gWebSocket.term_input(scriptText+"\n", null, true);
	    return false;
	}

	var formSubmitter = ".pagelet.entry"+gPromptIndex+" .gterm-form-command";
	if (gForm && gParams.controller && $(formSubmitter).length == 1) {
	    $(formSubmitter).click();
	    return false;
	}

	if (!gNotebook && evt.shiftKey && gParams.update_opts.command) {
	    GTMenuNotebook("new_default");
	    return false;
	}

	if (!gNotebook && evt.ctrlKey && gParams.update_opts.command) {
	    GTMenuNotebook("open");
	    return false;
	}

	if (gNotebook && evt.ctrlKey) {
	    gNotebook.handleCommand("execute");
	    return false;
	}

	if (gNotebook && evt.shiftKey) {
	    gNotebook.handleCommand("run");
	    return false;
	}

	if (gNotebook && evt.altKey) {
	    gNotebook.handleCommand("execinsert");
	    return false;
	}

	if (gNotebook)
	    gNotebook.poll(true);
    }

    if (!evt.ctrlKey && !gControlActive && GTCaptureInput()) {
	// Not Ctrl character; editing/processing form/notebook
	if (gNotebook && gNotebook.handling_tab)
	    gNotebook.cancelCompletion();
	return true;
    }

    if (evt.altKey) {
	if (kc>=65 && kc<=90)
	    kc+=32;
	if (kc>=97 && kc<=122) {
	    k=String.fromCharCode(27)+String.fromCharCode(kc);
	}

	if (evt.ctrlKey && kc == 116) {
	    // Ctrl-Alt-T: Open new terminal
	    OpenNew()
	    return false;
	}

    } else if (gControlActive && kc == 91) {
	k=String.fromCharCode(kc-64); // Ctrl-[ (ESC)

    } else if (evt.ctrlKey || gControlActive) {
	if (kc>=0 && kc<=31) k=String.fromCharCode(kc); // Ctrl-@..Z.._
	else if (kc>=64 && kc<=90) k=String.fromCharCode(kc-64); // Ctrl-@..Z
	else if (kc>=96 && kc<=122) k=String.fromCharCode(kc-96); // Ctrl-@..Z
	else if (kc==54)  k=String.fromCharCode(30); // Ctrl-^
	else if (kc==109) k=String.fromCharCode(31); // Ctrl-_
	else if (kc==219) k=String.fromCharCode(27); // Ctrl-[
	else if (kc==220) k=String.fromCharCode(28); // Ctrl-\
	else if (kc==221) k=String.fromCharCode(29); // Ctrl-]
	else if (kc==219) k=String.fromCharCode(29); // Ctrl-]
	else if (kc==219) k=String.fromCharCode(0);  // Ctrl-@

    } else if (evt.which==0 || (evt.charCode==0 && kc >=33 && kc <= 46) ) {
	if (kc==9) k=String.fromCharCode(9);  // Tab
	else if (kc==8) k=String.fromCharCode(127);  // Backspace
	else if (kc==27) k=String.fromCharCode(27); // Escape
	else {
	    if (kc==33) k="[5~";        // PgUp
	    else if (kc==34) k="[6~";   // PgDn
	    else if (kc==35) k="[4~";   // End
	    else if (kc==36) k="[1~";   // Home
	    else if (kc==37) k="[D";    // Left
	    else if (kc==38) k="[A";    // Up
	    else if (kc==39) k="[C";    // Right
	    else if (kc==40) k="[B";    // Down
	    else if (kc==45) k="[2~";   // Ins
	    else if (kc==46) k="[3~";   // Del
	    else if (kc==112) k="[[A";  // F1
	    else if (kc==113) k="[[B";  // F2
	    else if (kc==114) k="[[C";  // F3
	    else if (kc==115) k="[[D";  // F4
	    else if (kc==116) k="[[E";  // F5
	    else if (kc==117) k="[17~"; // F6
	    else if (kc==118) k="[18~"; // F7
	    else if (kc==119) k="[19~"; // F8
	    else if (kc==120) k="[20~"; // F9
	    else if (kc==121) k="[21~"; // F10
	    else if (kc==122) k="[23~"; // F11
	    else if (kc==123) k="[24~"; // F12
	    if (k.length) {
		k=String.fromCharCode(27)+k;
	    }
	}
    } else {
	if (kc==8)
	    k=String.fromCharCode(127);  // Backspace
	else
	    k=String.fromCharCode(kc);
    }

    if (gDebugKeys)
	console.log("graphterm.AjaxKeypress2", kc, k, k.charCodeAt(0), k.length);

    if (k != String.fromCharCode(17))
	gControlQ = false;

    if (gShortcutMenus) {
	GTShortcutHandler(k);
	return false;
    }

    if (GTTerminalInput(k, true))
	return true;
    evt.cancelBubble = true;
    return GTPreventHandler(evt);
}

function GTTerminalInput(chr, type_ahead) {
    if (gNotebook && !gNotebook.passthru_stdin && gNotebook.prefix_key) {
	gNotebook.prefix_key = false;
	gNotebook.handleKey(chr);
	return false;
    }

    if (!gMacPlatform && chr == String.fromCharCode(22)) {
	// Ctrl-V passthru
	return true
    }

    if (chr == String.fromCharCode(3)) {
	// Ctrl-C handling
	if (gPopupType) {
	    // Exit from popup
	    popupClose();
	    return false;
	} else if (gExpectUpload) {
	    // Exit from upload
	    GTUploadCancel(null);
	    return false;
	} else if (gForm) {
	    // Exit from form
	    GTEndForm("", true);
	    return false;
	} else if (gNotebook && !gNotebook.passthru_stdin) {
	    // Close notebook
	    if (window.confirm("Exit notebook mode without saving and display output in terminal mode?"))
		GTCloseNotebook();
	    return false;
	}
    }

    if (GTCaptureInput()) {
	// Editing or processing form or using notebook
	return true;
    }

    if (!gParams.controller) {
	alert("Not controlling this terminal; keyboard input discarded.");
	return true;
    }

    if (chr.length) {
	if (chr.charCodeAt(0) == gPasteSpecialKeycode) {
	    // Paste Special shortcut
	    GTPasteSpecialBegin();
            chr = "";
	} else if (chr.charCodeAt(chr.length-1) == 13) {
	    // Enter key
	    if (gShowingFinder)
		HideFinder();
	    if (gCommandMatchPrev) {
		// Simulate right arrow for command completion
		if (!CompleteCommand(true))
		    chr = "";
	    } else if (gAndroid) {
		chr = GetCursorText() + chr;
	    }
	}
	if (chr)
	    gWebSocket.term_input(chr, type_ahead);
    }
    return false;
}

function GTShortcutHandler(ch) {
    console.log("GTShortcutHandler: ", ch);
    if (!gShortcutMenus)
	return;

    var subMenus = gShortcutMenus[0].find('> li > a');
    var matched = false;
    for (var j=0; j<subMenus.length; j++) {
	var elem = $(subMenus[j]);
	var elemText = elem.hasClass("gterm-key-altletter") ? elem.children(".gterm-key-letter").text() : elem.text();
	if (_.str.startsWith(elemText, ch)) {
	    if (elem.attr("gterm-state")) {
		GTMenuEvent(elem);
	    } else {
		elem.next().show();
		gShortcutMenus.unshift(elem.next());
		matched = true;
	    }
	    break;
	}
    }
    if (!matched)
	return GTShortcutEnd(true);
}

function GTShortcutEnd(hide) {
    if (!gShortcutMenus)
	return;
    if (hide) {
	while (gShortcutMenus.length > 1)
	    gShortcutMenus.shift().hide();
    }

    $("#terminal").removeClass("gterm-shortcut-mode");
    gShortcutMenus = null
}

function OpenNew(host, term_name, options) {
    host = host || gParams.host;
    term_name = term_name || "new";
    var path = host + "/" + term_name;
    if (term_name == "new" && gParams && gParams.term)
	path += "/"+gParams.term;
    var new_url = window.location.protocol+"/"+"/"+window.location.host+"/"+path+"/?qauth="+getAuth(); // Split the double slash to avoid confusing the JS minifier
    console.log("open", new_url);
    var target = (term_name == "new") ? "_blank" : path;
    window.open(new_url, target);
}

function load(path) {
    // Load terminal in current window
    if (path == "full") {
	top.location = "/"+gParams.host+"/"+gParams.term+"/?qauth="+getAuth();
	return;
    }
    if (path.indexOf("/") == -1)
	path = "/" + gParams.host + "/" + path;
    console.log("gterm", path);
    window.location = path+"/?qauth="+getAuth();
}

function CheckUpdates() {
    $.getJSON(PYPI_JSON_URL, function(data) {
	if (gParams.about_version == data.info.version) {
	    GTPopAlert('GraphTerm is up-to-date (version: '+gParams.about_version+').<p> There is  now a <a href="https://groups.google.com/group/graphterm" target="_blank">Mailing list</a> for GraphTerm.', true);
	} else {
	    GTPopAlert('A new release of GraphTerm ('+data.info.version+') is available!<br>See <a href="'+RELEASE_NOTES_URL+'" target="_blank">Release Notes</a> for details.<br> There is also a <em>new</em> <a href="https://groups.google.com/group/graphterm" target="_blank">Mailing list</a> for GraphTerm.<p>Upgrade using <b>sudo pip install --upgrade graphterm</b><br> OR download from the <a href="'+PYPI_URL+'" target="_blank">Python Package Index</a>', true);
	}
    });
    gWebSocket.write([["check_updates"]]);
}

function ReconnectHost() {
    console.log("ReconnectHost");
    if (window.confirm("Reconnect to host? (will take over 15 sec)")) {
	gWebSocket.write([["reconnect_host"]]);
    }
}

function StealSession() {
    if (!window.confirm("Steal control of "+gParams.host+"/"+gParams.term+"?"))
	return;
    var steal_url = window.location.protocol+"/"+"/_steal/"+window.location.host+"/"+gParams.host+"/"+gParams.term+'/?qauth='+getAuth()+'&websocket='+gParams.websocket_id; // Split the double slash to avoid confusing the JS minifier
    console.log("StealSession: ", steal_url);
    window.location = steal_url;
}

function DetachSession() {
    var comps = window.location.pathname.split("/");
    window.location = ((comps.length > 1) ? ('/'+comps[1]) : '') + '/?qauth='+getAuth();
}

function Webcast(start) {
    console.log("Webcast", start);
    if (!gWebSocket)
	return;
    if (start && !window.confirm('Make terminal publicly viewable ("webcast")?'))
	return;

    $("#terminal").toggleClass("gterm-webcast", start);
    gWebSocket.webcast = start;
    gWebSocket.write([["webcast", gWebSocket.webcast]]);
}

// Popup management
var gPopupActive = false;
var gPopupCallback = null;
var gPopupType = "";
var gPopupParams = null;
var gPopupConfirmClose = null;

function popupSetup() {
  // Initialize bindings for popup handling
  $(".gterm-popup").hide();
  $(".gterm-popupmask").hide();
  $(".gterm-popupbutton").bindclick(popupButton);
  $(".gterm-popupmask, .gterm-popupclose").bindclick(popupClose);
}

function popupClose(confirm) {
  // Hide mask and popup window
  if (confirm && gPopupConfirmClose) {
    if (!gPopupConfirmClose()) {
      // Cancel close
      return false;
    }
  }
  $(".gterm-popup").hide();
  $(".gterm-popupmask").hide();
  gPopupActive = false;
  gPopupCallback = null;
  gPopupConfirmClose = null;
  gPopupType = "";
  gPopupParams = null;
  ScrollTop(null);
}

function popupButton(event) {
    if (gPopupCallback)
	gPopupCallback(this);
}

function popupShow(elementSelector, popupCallback, popupConfirmClose, popupType, popupParams) {
  // Display element as modal popup window
  var maskSelector = "#gterm-popupmask";

  gPopupActive = true;
  gPopupCallback = popupCallback || null;
  gPopupConfirmClose = popupConfirmClose || null;
  gPopupType = popupType || "";
  gPopupParams = popupParams || null;

  var animateMs = 0;

  // Get screen height/width
  var maxWidth = 1600;
  var minWidth = 100;

  var winWidth = $(window).width();
  var winHeight = $(window).height();
  var docHeight = $(document).height();

  // Fade in mask
  ScrollTop(0);
  $(maskSelector).css({width: winWidth, height: docHeight});

  //$(maskSelector).fadeIn(1000);
  $(maskSelector).fadeTo(0.6*animateMs, 0.7);

  // Position popup window
  //$(elementSelector).css("top", winHeight/2 - $(elementSelector).outerHeight()/2);
  $(elementSelector).css("top", 0);
  $(elementSelector).css("left", (winWidth/2) - ($(elementSelector).outerWidth()/2));

  // Fade in popup
  $(elementSelector).fadeIn(1.0*animateMs);

  $(elementSelector).find("textarea").focus();
  $(elementSelector).find("input:text").focus();

  gScrollTop = true;
}

function GTCaptureInput() {
    if (gShortcutMenus)
	return false;
    return (gParams.controller && gNotebook && !gNotebook.passthru_stdin && !gNotebook.prefix_key) || gForm || (gParams.controller && gEditing) || gPopupType;
}

function GTClearCKEditor() {
    for (var name in CKEDITOR.instances){
	var instance = CKEDITOR.instances[name];
	instance.destroy();
    }
}
function GTResizeCKEditor() {
    var defaultHeight = 300;
    var newHeight = window.innerHeight-150; 
    var height = defaultHeight > newHeight ? defaultHeight : newHeight;
    for (var name in CKEDITOR.instances){
	var instance = CKEDITOR.instances[name];
	instance.resize('100%', height);
    }
}

function GTStartEdit(params, content) {
    var editor = params.editor ? params.editor : gDefaultEditor;
    console.log("GTStartEdit", editor, params);
    $("#gterm-mid").hide();
    gEditing = {params: params, content: content, editor: editor};
    if (params.editor == "textarea") {
	$("#gterm-texteditarea-content").val(content);
	popupShow("#gterm-texteditarea", "editarea");
    } else {
	var url = gParams.apps_url+"/"+editor+".html";
	var html = gFrameDispatcher.createFrame(params, content, url, "gterm-editframe");
	$("body").append(html);
    }
}

function GTEndEditArea(save) {
    if (!gEditing)
	return;
    var newContent = $("#gterm-texteditarea-content").val();
    GTEndEdit(newContent, gEditing.content, gEditing.params, save);
}

function GTEndEdit(newContent, oldContent, params, save) {
    console.log("GTEndEdit", params, save);
    if (newContent != null) {
	if (params.action == "buffer") {
	    if (newContent != oldContent)
		GTBufferScript(newContent);

	} else if (gParams.controller && params.modify && newContent != oldContent) {
	    if (params.command) {
		gWebSocket.write([["input", params.command, utf8_to_b64(newContent)]]);
	    } else {
		gWebSocket.write([["save_data", {x_gterm_filepath: params.filepath,
						 x_gterm_location: params.location||"",
						 x_gterm_popstatus: "alert",
						 x_gterm_encoding: "base64"}, utf8_to_b64(newContent)]]);
	    }
	}
    }

    if (params.editor == "textarea") {
	$("#gterm-texteditarea-content").val("");
	popupClose(false);
    } else {
	// Kludge to return focus from editor iframe to terminal
	$('<textarea></textarea>').replaceAll("#gterm-editframe").focus().remove();
	//$("#gterm-editframe").remove();
	//if (!save)
	    //GTPopAlert("File not saved");   // Seems to be needed to return focus to terminal. Why?
    }
    gEditing = null;
    $("#gterm-mid").show();
    ScrollScreen();
}


function GTStartForm(params, promptIndex) {
    gForm = params || {};
    gFormIndex = promptIndex || 0;
    $("#session-screen").hide();
}

function GTEndForm(text, cancel) {
    text = text || "";
    console.log("GTEndForm: ", text, cancel);
    if (cancel) {
	if (gForm && !gForm.form_command)
	    gWebSocket.term_input("\n");
	    
    } else {
	if (gFormIndex)
	    gWebSocket.write([["clear_last_entry", gFormIndex+""]]);
	if (gForm)
	    gWebSocket.term_input(text+"\n", false, gForm.form_command);
    }
    if (gFormIndex)
	$("#session-bufscreen").children(".pagelet.entry"+gFormIndex).remove();
    $("#session-screen").show();
    gForm = null;
    gFormIndex = null;
}

function GTHelpLink(evt) {
    var helpStr = $(this).attr("title");
    if (helpStr) {
	var html = '<div class="gterm-help gterm-prewrap">'+GTPreserveLinebreaks(GTEscape(helpStr))+'</div>';
	$("#gterm-helparea-content").html(html);
	popupShow("#gterm-helparea", null, null, "help");
    }
    return false;
}

function GTFormSubmit(evt) {
    var formCommand = gForm.form_command;
    if ($(this).hasClass("gterm-form-cancel"))
	GTEndForm("", true);

    var formElem = $(this).closest(".gterm-form");
    var inputArgs = $(this).attr("data-gtermformnames");
    var inputElems;
    if (inputArgs) {
	var names = inputArgs.split(",");
	inputElems = [];
	for (var j=0; j<names.length; j++)
	    inputElems.push(formElem.find("[name="+names[j]+"]"));
    } else {
	inputElems = formElem.find("input, select");
    }
    var optStr = "";
    var argStr = ""
    var formValues = {};
    for (var j=0; j<inputElems.length; j++) {
	var inputElem = $(inputElems[j]);
	var inputName = inputElem.attr("name");
	if (!inputName)
	    continue;
        var serialized = inputElem.serializeArray();
        var inputValue = (serialized && serialized[0]) ? serialized[0]["value"] : "";
	if (inputValue.indexOf(" ") > -1)
	    inputValue = '"' + inputValue + '"';
	if (formCommand) {
            if (inputValue) {
		if (inputValue.substr(0,1) == '"') {
		    var nlen = inputValue.length;
		    inputValue = '"'+inputValue.substr(1,nlen-2).replace(/"/g, '\\"')+inputValue.substr(nlen-1);
		} else {
		    inputValue = inputValue.replace(/"/g, '\\"');
		    if (inputValue.indexOf(" ") >= 0)
			inputValue = '"'+inputValue+'"';
		}
		if (inputName.substr(0,3) == "arg") {
		    // Command line arguments
		    argStr += ' ' + inputValue; 
		} else {
		    // Command options
		    if (inputElem.attr("type") == "checkbox")
			optStr += ' --' + inputName;
		    else
			optStr += ' --' + inputName + '=' + inputValue;
		}
	    }
	} else {
	    if (inputValue.indexOf(" ") >= 0 && inputValue.substr(0,1) == '"' && inputValue.substr(inputValue.length-1) == '"')
		inputValue = inputValue.substr(1,inputValue.length-2);
	    formValues[inputName] = inputValue;
	}
    }
    var sendLine;
    if (formCommand) {
	if (formCommand.indexOf("%(args)") >= 0)
	    sendLine = formCommand.replace(/%\(args\)/g, optStr+argStr);
	else
	    sendLine = formCommand+optStr+argStr;
    } else {
	sendLine = JSON.stringify(formValues);
    }
    console.log("GTFormSubmit", this, formElem, sendLine, evt);
    GTEndForm(sendLine);
}

// From http://www.sitepoint.com/html5-full-screen-api
var pfx = ["webkit", "moz", "ms", "o", ""];
function RunPrefixMethod(obj, method) {
	var p = 0, m, t;
	while (p < pfx.length && !obj[m]) {
		m = method;
		if (pfx[p] == "") {
			m = m.substr(0,1).toLowerCase() + m.substr(1);
		}
		m = pfx[p] + m;
		t = typeof obj[m];
		if (t != "undefined") {
			pfx = [pfx[p]];
			return (t == "function" ? obj[m]() : obj[m]);
		}
		p++;
	}
}


var gFullpageDisplay = null;
function StartFullpage(display, split) {
    //console.log("StartFullpage: ", display, split);
    gFullpageDisplay = display;
    $("#session-bufscreen").addClass(gFullpageDisplay)
    if (display == "fullpage") {
	if (split) {
	    $("#session-bufellipsis").show();
	    if (gAlwaysSplitScreen && !gSplitScreen)
		SplitScreen("fullpage");
	}
    }

    if (display == "fullwindow" || display == "fullscreen") {
	if (gMobileBrowser) {
	    $("#session-term").addClass("display-footer");
	}
	setTimeout(function() {ScrollTop(null)}, 250); // Scroll background to bottom of screen
    }

    if (display == "fullscreen") {
	try {
	    if (RunPrefixMethod(document, "FullScreen") || RunPrefixMethod(document, "IsFullScreen")) {
		// Already in fullscreen mode
	    } else {
		RunPrefixMethod(document, "RequestFullScreen");
	    }
	} catch(err) {console.log("graphterm: Fullscreen ERROR", err);}
    }
}

function GTFrameDispatcher() {
    this.frameControllers = {};
    this.frameProps = {};
    this.frameIndex = 0;
}

GTFrameDispatcher.prototype.createFrame = function(params, content, url, frameId) {
    url = url || params.url;
    if (!frameId) {
	this.frameIndex += 1;
	frameId = "frame" + this.frameIndex;
    }

    this.frameProps[frameId] = {id: frameId, params: params, content: content, controller: gParams && gParams.controller};
    return '<iframe id="'+frameId+'" class="gterm-iframe" src="'+url+'" width="100%" height="100%"></iframe>';
}

GTFrameDispatcher.prototype.open = function(frameController, frameObj) {
    console.log("GTFrameDispatcher.open", frameController, frameObj);
    var frameId = $(frameObj).attr("id");
    var props = (frameId in this.frameProps) ? this.frameProps[frameId] : {id: frameId, params: {}};
    if (frameController && "open" in frameController) {
	this.frameControllers[frameController.frameName] = {controller: frameController, props: props};
	frameController.open(props);
    }
    if ($("#"+frameId).hasClass("gterm-noheader")) {
	$("#"+frameId).attr("height", "100%");
	$(".gterm-iframeheader").hide();
    }
    $("#"+frameId).focus();
}

GTFrameDispatcher.prototype.updateControl = function(value) {
    for (var frameName in this.frameControllers) {
	try {
	    var frameController = this.frameControllers[frameName].controller;
	    if ("control" in frameController)
		frameController.control(value);
	} catch (err) {
	    console.log("GTFrameDispatcher.updateControl: ERROR "+frameName+": "+err);
	}
    }
}

GTFrameDispatcher.prototype.send = function(toUser, toFrame, msg) {
    if (gWebSocket && gParams.controller)
	gWebSocket.write([["send_msg", toUser, "frame", toFrame, msg]]);
}

GTFrameDispatcher.prototype.write = function(text) {
    if (gWebSocket && gParams.controller)
	gWebSocket.term_input(text);
}

GTFrameDispatcher.prototype.receive = function(fromUser, toUser, frameName, msg) {
    console.log("GTFrameDispatcher.receive: ", fromUser, toUser, frameName, msg)
    if (!(frameName in this.frameControllers))
	return;

    try {
	this.frameControllers[frameName].controller.receive(fromUser, toUser, msg);
    } catch(err) {
	console.log("GTFrameDispatcher.receive: "+err);
    }
}

GTFrameDispatcher.prototype.close = function(frameName, save) {
    console.log("GTFrameDispatcher.close", frameName, save);
    if (!(frameName in this.frameControllers))
	return;

    var props = this.frameControllers[frameName].props;
    if (frameName == "editor") {
	if (!save && gParams.controller && !window.confirm("Discard changes?"))
	    return;
	var newContent = save ? this.frameControllers[frameName].controller.getContent() : null;
	GTEndEdit(newContent, props.content, props.params, save);

	if (props.controller && props.params.action != "buffer") {
	    this.send("*", "editor", ["end", ""]);
	}
    }
    
    delete this.frameControllers[frameName];
    if (gParams.controller)  // Delay sending Control-C so that any data stream sent back by the frame is not pre-empted
	setTimeout(gtermInterruptHandler, 200);
    EndFullpage(props.id);
}

var gFrameDispatcher = new GTFrameDispatcher();

function GTActivateNotebook(filepath, prompts) {
    filepath = filepath || "";
    if (gNotebook)
	return;
    if (!gParams.update_opts.command && filepath && !_.str.endsWith(filepath, ".sh.md") && !_.str.endsWith(filepath, ".sh.gnb.md")) {
	alert("Only *.sh.md files can be opened at shell prompt. Please start appropriate program before opening notebook file: "+filepath);
	return;
    }
    if (gWebSocket && gParams.controller) {
	var share = filepath.indexOf('-share.') > -1;
	gWebSocket.write([["open_notebook", filepath, prompts || [], {share: share}, null]]);
    }
}

function GTCloseNotebook(clear) {
    if (gWebSocket && gParams.controller) {
	gWebSocket.write([["close_notebook", clear||false]]);
    }
}

function GTNotebook(params) {
    this.note_params = params;
    this.fullpage = !params.shell;
    this.slide_mode = false;
    this.autosaved = true;

    if (gNotebookId[0] != gPromptIndex)
	gNotebookId = [gPromptIndex, 0]
    gNotebookId[1] += 1;
    this.notebookId = "gterm-notebook"+gNotebookId[0]+"-"+gNotebookId[1];

    var entry_class = "entry"+gPromptIndex;
    var classes = "entry"+gPromptIndex;

    this.pagelet = $('<div id="'+this.notebookId+'" class="pagelet pagelet-notebook entry '+classes+'" data-gtermcurrentdir="" data-gtermpromptindex="'+gPromptIndex+'"></div>\n').appendTo("#session-bufscreen");

    this.pagelet.on("focus", "textarea.gterm-notecell-input", bind_method(this, this.handleFocus));

    if (this.fullpage) {
	StartFullpage("fullpage", false);
	$("#session-bufellipsis").show();
    }

    this.prefix_key = false;

    this.cellParams = {};
    this.curIndex = 0;
    this.openNext = false;
    this.createNext = false;
					      
    this.lastPollTime = epoch_time();
    this.lastUpdateTime = epoch_time();
    this.lastTextValue = null;
    this.passthru_stdin = false;
    this.handling_tab = null;
    this.handled_tab = false;

    this.focusing = false;
    this.splitting = false;
    this.closed = false;
    this.poll_intervalID = window.setInterval(bind_method(this, this.poll), POLL_SEC*1000);
    var nb_label = "NB: "+this.note_params.name;
    if (!this.note_params.autosave)
	nb_label += " (no autosave)";
    $("#menubar-notelabel").text(nb_label);
}

GTNotebook.prototype.close = function() {
    console.log("GTNotebook.close: ");
    this.closed = true;
    if (this.poll_intervalID) {
	window.clearInterval(this.poll_intervalID);
	this.poll_intervalID = null;
    }

    if (this.fullpage)
	EndFullpage();

    $("#"+this.notebookId).remove();
    $("#menubar-notelabel").text("");

    gNotebook = null;
    $("#terminal").removeClass("gterm-notebook");
    $("#terminal").removeClass("gterm-notebook-submit");
    $("#terminal").removeClass("gterm-noteslides");
    if (gWebSocket && gParams.controller)
	gWebSocket.term_input("\n");
}

GTNotebook.prototype.handleFocus = function(evt) {
    //console.log("GTNotebook.handleFocus: ", this.focusing);
    if (this.closed || this.focusing)
	return;
    var cellId = $(evt.target).attr("id");
    if (!cellId || cellId == this.getCellId(this.curIndex)+"-textarea")
	return;
    try {
	var cellIndex = parseInt(cellId.split("-")[4]);
	gWebSocket.write([["select_cell", cellIndex, false, false]]);
    } catch(err) {
	console.log("GTNotebook.handleFocus: ERROR "+err);
	this.cellFocus(true);
    }
    return false;
}

GTNotebook.prototype.eraseOutput = function(cellIndex) {
    if (cellIndex) {
	$("#"+this.getCellId(cellIndex)+"-output").html("");
	$("#"+this.getCellId(cellIndex)+"-screen").html("");
    } else {
	$(this.pagelet).find(".gterm-notecell-output:not(.gterm-notecell-markdown)").html("");
	$(this.pagelet).find(".gterm-notecell-screen").html("");
    }
}

GTNotebook.prototype.getLastIndex = function() {
    var cellId = $(this.pagelet).children(".gterm-notecell-container").last().attr("id");
    try {
	return parseInt(cellId.split("-")[4]);
    } catch(err) {
	return 0;
    }
}

GTNotebook.prototype.handleOutput = function(evt) {
    var parent = $(evt.target).hasClass("gterm-notecell-markdown") ? $(evt.target) : $(evt.target).parents("div.gterm-notecell-markdown");
    if (this.closed || !parent.length)
	return;
    var cellId = parent.attr("id");
    if (!cellId)
	return;
    try {
	var cellIndex = parseInt(cellId.split("-")[4]);
	if (cellIndex == this.curIndex) {
	    this.renderCell(true, true);
	} else {
	    parent.hide();  // Hide markdown output for target
	    gWebSocket.write([["select_cell", cellIndex, false, false]]);
	}
    } catch(err) {
	console.log("GTNotebook.handleOutput: ERROR "+err);
    }
    return false;
}

GTNotebook.prototype.handleKey = function(ch) {
    if (!gWebSocket || !gParams.controller)
	return;
    if (ch == "a") {
	this.handleCommand("insert_above");
    } else if (ch == "b") {
	this.handleCommand("insert_below");
    } else if (ch == "c") {
	this.handleCommand("markdown", false);
    } else if (ch == "d") {
	this.handleCommand("cell_delete");
    } else if (ch == "j") {
	this.handleCommand("cell_up");
    } else if (ch == "k") {
	this.handleCommand("cell_down");
    } else if (ch == "l") {
	this.handleCommand("page_slide", !this.slide_mode);
    } else if (ch == "m") {
	this.handleCommand("markdown", true);
    } else if (ch == "n") {
	if (this.slide_mode)
	    this.handleCommand("page_next");
	else
	    this.handleCommand("select_next");
    } else if (ch == "p") {
	if (this.slide_mode)
	    this.handleCommand("page_previous");
	else
	this.handleCommand("select_previous");
    } else if (ch == "r") {
	this.handleCommand("cell_read");
    } else if (ch == "s") {
	this.handleCommand("save");
    } else if (ch == "u") {
	this.handleCommand("execute");
    } else if (ch == "w") {
	this.handleCommand("cell_write");
    }
}

GTNotebook.prototype.altSave = function() {
    this.saveNotebook("", {popstatus: "alert", alt_save: true})
}

GTNotebook.prototype.saveNotebook = function(filepath, params) {
    // Save notebook, updating current cell input
    var textElem = $("#"+this.getCellId(this.curIndex)+"-textarea");
    gWebSocket.write([["save_notebook", filepath, textElem.val() || "", params || {}]]);
}

GTNotebook.prototype.handleCommand = function(command, newValue) {
    if (!gWebSocket || !gParams.controller)
	return;
    if (this.note_params.form && (command == "cell_delete" || command == "cell_merge" || command == "cell_split" || command == "cell_read" || command == "cell_up" || command == "cell_down")) {
	alert("Cannot modify cells in fillable notebook");
	return;
    }
    var cellParams = this.cellParams[this.curIndex];
    if (command == "quit_preserve") {
	if (window.confirm("Exit notebook mode and display output?"))
	    GTCloseNotebook();
    } else if (command == "quit_discard") {
	if (window.confirm("Exit notebook mode and discard all data?"))
	    GTCloseNotebook(true);
    } else if (command == "save") {
	var filepath = $.trim(window.prompt("Save as: ", this.note_params.file));
	if (filepath) {
	    this.saveNotebook(filepath, {popstatus: "alert"}); 
	}
    } else if (command == "submit") {
	if (window.confirm("Submit notebook?")) {
	    this.saveNotebook("", {submit: "submit"}); 
	}
    } else if (command == "run" || (!this.note_params.form && command == "runbutton")) {
	if (cellParams.cellType in MARKUP_TYPES) {
	    this.renderCell(false, false);
	    this.update_text(false, false, false);
	    if (this.curIndex == this.getLastIndex())
		gNotebook.remoteAddCell("", "", 0);
	    else
		gWebSocket.write([["select_cell", 0, false, true]]);
	} else {
	    if (!this.note_params.form ||
		(this.note_params.form != "shared" && window.confirm("Proceed to next cell?")) ) {
		var createNew = (command == "run" && !this.note_params.form);
		this.update_text(true, true, createNew);
	    }
	}
    } else if (command == "execute"|| (this.note_params.form && command == "runbutton")) {
	if (cellParams.cellType in MARKUP_TYPES) {
	    this.update_text(false, false, false);
	    this.renderCell(true, false);
	} else {
	    this.update_text(true, false, false);
	}
    } else if (command == "execinsert") {
	if (!this.note_params.form) {
	    if (cellParams.cellType in MARKUP_TYPES) {
		this.renderCell(false, false);
		this.update_text(false, false, false);
		gNotebook.remoteAddCell("", "", 0);
	    } else {
		this.update_text(true, true, true);
	    }
	}
    } else if (command == "markdown") {
	gWebSocket.write([["update_type", newValue ? "markdown" : ""]]);
    } else if (command == "erase_cell") {
	gWebSocket.write([["erase_output", false]]);
    } else if (command == "erase_all") {
	gWebSocket.write([["erase_output", true]]);
    } else if (command == "cell_delete") {
	gWebSocket.write([["delete_cell", false]]);
    } else if (command == "cell_merge") {
	gWebSocket.write([["merge_above"]]);
    } else if (command == "cell_split") {
	this.splitCell();
    } else if (command == "cell_read") {
	var filepath = window.prompt("Read file: ", "");
	if (filepath) {
	    GTGetLocalFile(filepath,  this.note_params.dir, bind_method(this, this.cellValue));
	    gNotebook.cellParams[gNotebook.curIndex].cellFile = filepath;
	}
    } else if (command == "cell_write") {
	var filepath = window.prompt("Write file: ", gNotebook.cellParams[gNotebook.curIndex].cellFile || "");
	if (filepath) {
	    var textElem = $("#"+this.getCellId(this.curIndex)+"-textarea");
	    gWebSocket.write([["save_data", {x_gterm_filepath: filepath,
					     x_gterm_popstatus: "alert",
					     x_gterm_encoding: "base64"}, utf8_to_b64(textElem.val())]]);
	}
    } else if (command == "insert_above") {
	gNotebook.remoteAddCell("", "", -1);
    } else if (command == "insert_below") {
	gNotebook.remoteAddCell("", "", 0);
    } else if (command == "cell_up") {
	gWebSocket.write([["move_cell", true]]);
    } else if (command == "cell_down") {
	gWebSocket.write([["move_cell", false]]);
    } else if (command == "select_previous") {
	gWebSocket.write([["select_cell", 0, true, false]]);
    } else if (command == "select_next") {
	gWebSocket.write([["select_cell", 0, false, false]]);
    } else if (command == "page_previous") {
	gWebSocket.write([["select_page", -1, false, this.slide_mode]]);
    } else if (command == "page_next") {
	gWebSocket.write([["select_page", 1, false, this.slide_mode]]);
    } else if (command == "page_first") {
	gWebSocket.write([["select_page", -1, true, this.slide_mode]]);
    } else if (command == "page_last") {
	gWebSocket.write([["select_page", 1, true, this.slide_mode]]);
    } else if (command == "page_slide") {
	gWebSocket.write([["select_page", 0, false, newValue]]);
    } else if (command == "page_break") {
	gNotebook.remoteAddCell("markdown", "---", -1);
    }
}

GTNotebook.prototype.getCellId = function(cellIndex) {
    return this.notebookId+"-cell-"+cellIndex;
}

GTNotebook.prototype.addCell = function(cellIndex, cellType, beforeCellIndex, inputData) {
    var cellId = this.getCellId(cellIndex);
    var cellParams = { cellType: cellType, cellIndex: cellIndex, cellId: cellId };
    var hidden = (inputData == HIDDEN_STR);
    this.cellParams[cellIndex] = cellParams;
    var cellHtml = '<div id="'+cellId+'" class="gterm-notecell-container"><textarea id="'+cellId+'-textarea" class="gterm-notecell-input gterm-notecell-text" spellcheck="false"></textarea><div class="gterm-notecell-busy">Running...</div><div id="'+cellId+'-output" class="gterm-notecell-output"></div><div id="'+cellId+'-screen" class="gterm-notecell-screen"></div></div>';
    var newElem;
    if (!beforeCellIndex) {
	newElem = $(cellHtml).appendTo(this.pagelet);
    } else {
	newElem = $(cellHtml).insertBefore("#"+this.getCellId(beforeCellIndex));
    }
    newElem.toggleClass("gterm-notecell-hidden", hidden);
    if (this.slide_mode)
	newElem.addClass("gterm-noteslides-show");
    this.curIndex = cellIndex;
    this.cellValue(inputData);
    var textElem = $("#"+this.getCellId(this.curIndex)+"-textarea");
    textElem.toggleClass("gterm-notecell-markup", cellParams.cellType in MARKUP_TYPES);
    textElem.autoResize({extraSpace: 6, limit: 3200});
    //if (!gParams.controller)
    //	textElem.attr("disabled", "disabled");
    $("#"+this.getCellId(this.curIndex)+" div.gterm-notecell-busy").hide();
    $("#"+this.getCellId(this.curIndex)+"-output").bind("dblclick", bind_method(this, this.handleOutput));
    this.renderCell(this.splitting, this.splitting);
    this.splitting = false;
}

GTNotebook.prototype.renderCell = function(showInput, hideOutput, cellIndex) {
    cellIndex = cellIndex || this.curIndex;
    var cellParams = this.cellParams[cellIndex];
    var inputElem = $("#"+this.getCellId(cellIndex)+"-textarea");
    var outputElem = $("#"+this.getCellId(cellIndex)+"-output");
    if (cellParams.cellType in MARKUP_TYPES) {
	outputElem.addClass("gterm-notecell-markdown");
	var text = inputElem.val();
	if (!$.trim(text) && !this.note_params.form)
	    text = "EMPTY MARKDOWN CELL";
	var outputHtml = math_md2html(text);
	outputElem.html(outputHtml);
	if (hideOutput) {
	    outputElem.hide();
	} else {
	    if (_.str.startsWith(outputHtml, MATHCOMMENT))
		GTApplyMathJax(this.getCellId(cellIndex)+"-output");
	    outputElem.show();
	}
	    
	if (showInput)
	    this.cellFocus(true);
	else
	    inputElem.hide();
    } else {
	outputElem.removeClass("gterm-notecell-markdown");
	this.cellFocus(true);
    }
}

GTNotebook.prototype.remoteAddCell = function(cell_type, init_text, before_cell_number) {
    if (this.note_params.form) {
	alert("Cannot add cells to fillable notebook");
    } else {
	gWebSocket.write([["add_cell", cell_type, init_text, before_cell_number]]);
    }
}

GTNotebook.prototype.splitCell = function() {
    var cellParams = this.cellParams[this.curIndex];
    var textElem = $("#"+this.getCellId(this.curIndex)+"-textarea");
    var caretPos = textElem.prop("selectionStart");
    if (caretPos == textElem.prop("selectionEnd")) {
	var textVal = textElem.val();
	var head = textVal.substr(0,caretPos);
	var tail = textVal.substr(caretPos);
	if (_.str.endsWith(head, "\n"))
	    head = head.substr(0,head.length-1);
	textElem.val(head);
	$("#"+this.getCellId(this.curIndex)+"-output").html("");
	$("#"+this.getCellId(this.curIndex)+"-screen").html("");
	this.update_text();
	this.renderCell(false, false);
	this.splitting = true;
	gNotebook.remoteAddCell(cellParams.cellType, tail, 0);
    }
}

GTNotebook.prototype.selectCell = function(cellIndex, nofocus) {
    var cellParams = this.cellParams[this.curIndex];
    if (cellParams.cellType in MARKUP_TYPES) {
	this.renderCell(false, false);
    }
    this.curIndex = cellIndex;
    if (!nofocus)
	this.cellFocus(true);
    this.lastTextValue = null;
}

GTNotebook.prototype.selectPage = function(cellIndex, lastIndex, slide) {
    //console.log("GTNotebook.selectPage: ", cellIndex, lastIndex, slide);
    $("#terminal").toggleClass("gterm-noteslides", slide);
    this.selectCell(cellIndex, slide);
    this.slide_mode = slide;
    if (!slide)
	return;
    if (!this.fullpage) {
	this.fullpage = true;
	StartFullpage("fullpage", false);
    }
    $("#session-bufellipsis").hide();
    var firstId = this.getCellId(cellIndex);
    var lastId = this.getCellId(lastIndex);
    var firstMatch = false;
    var lastMatch = false;
    $(this.pagelet).children(".gterm-notecell-container").each(function() {
	var elemId = $(this).attr("id");
	if (elemId == firstId)
	    firstMatch = true;
	$(this).toggleClass("gterm-noteslides-show", firstMatch && !lastMatch);
	if (elemId == lastId)
	    lastMatch = true;
    });
}

GTNotebook.prototype.moveCell = function(cellIndex, moveUp) {
    var curElem = $("#"+this.getCellId(this.curIndex));
    if (moveUp) {
	curElem.insertBefore("#"+this.getCellId(cellIndex));
    } else {
	curElem.insertAfter("#"+this.getCellId(cellIndex));
    }
    this.cellFocus(true);
}

GTNotebook.prototype.updateType = function(cellIndex, cellType) {
    this.cellParams[this.curIndex].cellType = cellType;
    var textElem = $("#"+this.getCellId(this.curIndex)+"-textarea");
    textElem.toggleClass("gterm-notecell-markup", cellType in MARKUP_TYPES);
    this.cellFocus(true);
}

GTNotebook.prototype.deleteCell = function(deleteIndex, switchIndex) {
    $("#"+this.getCellId(deleteIndex)).remove();
    this.selectCell(switchIndex);
    if (this.cellParams[this.curIndex].cellType in MARKUP_TYPES)
	$("#"+this.getCellId(this.curIndex)+"-output").hide();
}

GTNotebook.prototype.cellValue = function(inputData, cellIndex, render) {
    //console.log("GTNotebook.cellValue: ", render, inputData);
    inputData = inputData || "";
    cellIndex = cellIndex || this.curIndex;
    if (cellIndex == this.curIndex)
	this.lastTextValue = inputData;
    var hidden = (inputData == HIDDEN_STR);
    var cellElem = $("#"+this.getCellId(cellIndex));
    cellElem.toggleClass("gterm-notecell-hidden", hidden);
    var textElem = $("#"+this.getCellId(cellIndex)+"-textarea");
    textElem.val(inputData);
    if (render)
	this.renderCell(false, false, cellIndex)
}

GTNotebook.prototype.cellFocus = function(focus, selectAll, noScroll) {
    //console.log("GTNotebook.cellFocus: ", focus, selectAll, noScroll);
    var textElem = $("#"+this.getCellId(this.curIndex)+"-textarea");
    this.focusing = true;
    if (focus) {
	textElem.show();
	textElem.focus();
	if (selectAll && textElem.length)
	    textElem[0].select();
	textElem.trigger("change");
	this.passthru_stdin = false;
	if (!noScroll)
	    setTimeout(bind_method(this, this.cellScrollInput), 200);
	GTMenuUpdateToggle("notebook_markdown", this.cellParams[this.curIndex].cellType in MARKUP_TYPES);
    } else {
	textElem.blur();
	this.passthru_stdin = true;
    }
    this.focusing = false;
}

GTNotebook.prototype.cellScrollInput = function() {
    var textElem = $("#"+this.getCellId(this.curIndex)+"-textarea");
    scrolledIntoView(textElem, true);
}

GTNotebook.prototype.cellScrollOutput = function() {
    var containerElem = $("#"+this.getCellId(this.curIndex));
    $(window).scrollTop(containerElem.offset().top+containerElem.height()-$(window).height());
}

GTNotebook.prototype.update_text = function(execute, openNext, createNew) {
    if (execute) {
	if (!createNew && this.curIndex == this.getLastIndex()) {
	    this.openNext = false;
	} else {
	    this.openNext = !!openNext;
	    this.createNext = createNew;
	}

	this.cellFocus(false);
	$("#"+this.getCellId(this.curIndex)+" div.gterm-notecell-busy").show();
    }
    var textElem = $("#"+this.getCellId(this.curIndex)+"-textarea");
    var text = textElem.val();
    if (gWebSocket && gParams.controller) {
	var save = !this.note_params.form||openNext;
	gWebSocket.write([["update_cell", this.curIndex, execute, save, text]]);
	this.send("*", this.curIndex, ["cell_input", text]);
	this.lastTextValue = text;
	this.lastUpdateTime = epoch_time();
    }
}

GTNotebook.prototype.poll = function(force) {
    var cur_time = epoch_time();
    if (!force && (cur_time - this.lastPollTime) < 0.5*POLL_SEC)
	return;
    this.lastPollTime = cur_time;
    var textElem = $("#"+this.getCellId(this.curIndex)+"-textarea");
    if (textElem.length != 1)
	return;
    if (gParams.nb_autosave && this.note_params.autosave && !this.autosaved && (cur_time - this.lastUpdateTime) > gParams.nb_autosave) {
	this.lastUpdateTime = cur_time;
	this.autosaved = true;
	this.saveNotebook("", {auto_save: true});
	$("#menubar-notelabel").text("NB: "+this.note_params.name+" (autosaved)");
    }
    var text = textElem.val();
    if (this.lastTextValue === text)
	return;
    if (gParams.nb_autosave && this.note_params.autosave && this.autosaved && (cur_time > this.lastUpdateTime) ) {
	this.autosaved = false;
	$("#menubar-notelabel").text("NB: "+this.note_params.name);
    }

    this.update_text(false, false);
}

GTNotebook.prototype.output = function(update_opts, update_rows, update_scroll) {
    //console.log("GTNotebook.output:", this.handled_tab);
    var selectAll = !this.handling_tab && !this.handled_tab;
    this.handled_tab = false;
    if (!this.curIndex)
	return;
    var cellParams = this.cellParams[this.curIndex];
    if (cellParams.cellType in MARKUP_TYPES)
	return;
    var outElem = $("#"+this.getCellId(this.curIndex)+" div.gterm-notecell-output");
    if (update_opts.reset)
	outElem.html("");

    for (var j=0; j<update_scroll.length; j++) {
	var row_params = update_scroll[j][JPARAMS];
	var row_line = update_scroll[j][JLINE];
	var markup = update_scroll[j][JMARKUP];
	var row_html;
	if (row_params[JTYPE] == "pagelet") {
	    var entry_class = this.notebookId + "-cell-" + this.curIndex;
	    GTAppendPagelet(outElem, row_params, entry_class, "pagelet gterm-notecell-scroll "+entry_class, markup);
	} else {
	    var row_escaped = (markup == null) ? GTEscape(row_line) : markup;
	    if (!this.handling_tab || row_line != this.handling_tab[1])
		$('<pre class="gterm-notecell-scroll">'+row_escaped+'\n</pre>').appendTo(outElem);
	}
    }

    for (var j=0; j<update_rows.length; j++) {
	var row_params = update_rows[j][JPARAMS];
	var add_class = row_params[JOPTS].add_class;
	var row_span = update_rows[j][JLINE];
	note_prompt = !!row_params[JOPTS].note_prompt;
	var row_line = "";
	for (var k=0; k<row_span.length; k++)
	    row_line += row_span[k][1];

	if (this.handling_tab) {
	    var textElem = $("#"+this.getCellId(this.curIndex)+"-textarea");
	    var caretPos = textElem.prop("selectionStart");
	    if (caretPos == this.handling_tab[0]) {
		var insOffset = row_line.indexOf(this.handling_tab[1]);
		if (insOffset >= 0) {
		    var textVal = textElem.val();
		    var appendVal = row_line.substr(insOffset+this.handling_tab[1].length);
		    if (appendVal) {
			textElem.val( textVal.substr(0,caretPos)+appendVal+textVal.substr(caretPos) );
			textElem.caret(caretPos+appendVal.length);
			this.cancelCompletion();
		    }
		}
	    } else {
		this.cancelCompletion();
	    }
	} else {
	    $("#"+this.getCellId(this.curIndex)+" div.gterm-notecell-screen").html('<pre class="row '+add_class+'">'+GTEscape(row_line)+((update_opts.note_prompt || !this.passthru_stdin)?'':GTCursorSpan(' '))+'\n</pre>');
	}
    }

    if (update_opts.note_prompt) {
	// "End of output"
	$("#"+this.getCellId(this.curIndex)+" div.gterm-notecell-busy").hide();
	if (this.openNext) {
	    if (this.createNext || this.curIndex == this.getLastIndex())
		gNotebook.remoteAddCell("", "", 0);
	    else
		gWebSocket.write([["select_cell", 0, false, true]]);
	    this.openNext = false;
	    this.createNext = false;
	} else if (this.curIndex == this.getLastIndex()) {
	    // Last cell
	    this.cellFocus(true, selectAll, true);
	    setTimeout(ScrollTerm, 200);
	} else {
	    this.cellFocus(true, selectAll);
	}
    } else {
	// Scroll on output
	if (this.curIndex == this.getLastIndex())
	    setTimeout(ScrollTerm, 200);
	else
	    setTimeout(bind_method(this, this.cellScrollOutput), 200);
    }
}

GTNotebook.prototype.cancelCompletion = function() {
    //console.log("GTNotebook.cancelCompletion:");
    this.handling_tab = null;
    this.handled_tab = true;
    if (gWebSocket)
	gWebSocket.write([["complete_cell", null]]);
}

GTNotebook.prototype.send = function(toUser, cellIndex, msg) {
    if (gWebSocket && gParams.controller)
	gWebSocket.write([["send_msg", toUser, "notebook", cellIndex, msg]]);
}

GTNotebook.prototype.write = function(text) {
    if (gWebSocket && gParams.controller)
	gWebSocket.term_input(text);
}

GTNotebook.prototype.receive = function(fromUser, toUser, cellIndex, msg) {
    try {
	if (msg[0] == "cell_input") {
	    if (cellIndex == this.curIndex)
		this.cellValue(msg[1]);
	}
    } catch(err) {
	console.log("GTNotebook.receive: "+err);
    }
}

function CloseIFrame(evt) {
    if (gFullpageDisplay) {
	EndFullpage();
	ScrollTop(null);
    }
    var containerId = $(evt.target).attr("gterm-iframe-container");
    if (containerId)
	$("#"+containerId).remove();
    else
	gtermInterruptHandler();
}
function ExpandIFrame(evt) {
    var containerId = $(evt.target).attr("gterm-iframe-container");
    if (containerId)
	window.location = $("#"+containerId+" iframe").attr("src");
    else
	load("full");
}

function EndFullpage(frameId) {
    //console.log("EndFullpage");
    try {
	if (RunPrefixMethod(document, "FullScreen") || RunPrefixMethod(document, "IsFullScreen")) {
	    RunPrefixMethod(document, "CancelFullScreen");
	}
    } catch(err) {}

    $("#session-bufellipsis").hide();
    if (gFullpageDisplay)
	$("#session-bufscreen").removeClass(gFullpageDisplay);
    gFullpageDisplay = null;
    if (gSplitScreen)
	MergeScreen("fullpage");
    $("#session-bufscreen .pagelet.gterm-fullwindow").removeClass("gterm-fullwindow");
}

function SplitScreen(code) {
    //console.log("SplitScreen: ", code);
    $("#session-term").addClass("split-screen");
    gSplitScreen = true;
    ResizeSplitScreen(true);
}

function MergeScreen(code) {
    //console.log("MergeScreen: "+code);
    $("#session-term").removeClass("split-screen");
    gSplitScreen = false;
    ResizeSplitScreen(false);
}

function ResizeSplitScreen(split) {
    //console.log("ResizeSplitScreen:", split);
    gMaxScrollOffset = 0;
    if (split) {
	// NOTE: Does this need to be delayed using SetTimeout?
	$("#session-bufscreen").css("margin-bottom", (10+$("#session-screencontainer").height())+"px");
	$("#session-findercontainer").css("margin-bottom", (10+$("#session-screencontainer").height())+"px");
    } else {
	$("#session-bufscreen").css("margin-bottom", "");
	$("#session-findercontainer").css("margin-bottom", "");
    }
}

function ToggleFooter() {
    var state = $("#session-term").hasClass("display-footer");
    GTMenuUpdateToggle("view_footer", !state);
    if (state)
	HideFooter();
    else
	DisplayFooter()
}

function DisplayFooter() {
    $("#session-term").addClass("display-footer");
    ScrollScreen();
}

function HideFooter() {
    $("#session-term").removeClass("display-footer");
}

function GetFinder(kind) {
    if (gWebSocket && gWebSocket.terminal)
	gWebSocket.write([["get_finder", kind || "", ""]]);
}

function ShowFinder(params, content) {
    //console.log("ShowFinder: ", params);
    gShowingFinder = true;
    var current_dir = params.current_directory;
    var finder_html = '<div class="finder" data-gtermcurrentdir="'+current_dir+'" data-gtermpromptindex="'+gPromptIndex+'">'+content+'</div>\n';

    $("#session-finderbody").html(finder_html);
    
    $('#session-finderbody td .gterm-link:not(.gterm-download)').bindclick(gtermFinderClickHandler)

    if (!gSplitScreen)
	SplitScreen("finder");
    $("#gterm-header").hide();
    $("#session-bufellipsis").hide();
    $("#session-bufscreen").hide();
    $("#session-findercontainer").show();
}

function HideFinder() {
    $("#session-findercontainer").hide();
    $("#session-finderbody").empty();
    $("#session-bufscreen").show();
    $("#gterm-header").show();
    gShowingFinder = false;
    MergeScreen("finder");
    ScrollScreen();
}

// HTML5 Drag/Drop
function GTPreventHandler(evt) {
    if (evt.preventDefault) evt.preventDefault();
    if (evt.stopPropagation) evt.stopPropagation();
    return false;
}

function GTDragBindings(elem) {
    elem.bind('dragstart', GTDragStart);
}

function GTDropBindings(elem) {
    //console.log("GTDropBindings", elem);
    if (!elem.length)
	return;
    try {
    elem.bind('dragover', GTDragOver);
    elem.bind('drop', GTDropHandler);
    } catch(err) {
	//console.log("GTDropBindings:", err);
    }
}

var gtDragElement = null;

function GTDragStart(evt) {
    gtDragElement = this;
    //evt.dataTransfer.effectAllowed = 'move';
    //evt.dataTransfer.setData('text/html', this.innerHTML);
}

function GTDragOver(evt) {
    //console.log("GTDragOver", evt);
    if (evt.originalEvent)
	evt.originalEvent.dropEffect = "copy";
    else
	evt.dropEffect = "none";
    return GTPreventHandler(evt);
}

function GTDropHandler(evt) {
    console.log("GTDropHandler", this, evt);
    var transfer = evt.originalEvent.dataTransfer;
    if (gtDragElement != this) {
	try {
	    var gterm_mime = $(this).attr("data-gtermmime") || "";
	    var gterm_url = makeFileURL($(this).attr("href") || "");
	    if (transfer.files && transfer.files.length) {
		// Handle dropped files
		if (transfer.files.length != 1) {
		    alert("Please select a single file");
		    return;
		}
		var filename = transfer.files[0].name;

		if (gExpectUpload) {
		    GTFileDropHandler.call(transfer, evt.target);
		} else if (gterm_mime == "x-graphterm/directory") {
		    GTFileDropHandler.call(transfer, evt.target);
		    var options = {};
		    options.command = "gupload %(path) && cd %(path) && gls -f";
		    options.dest_url = filename;
		    options.enter = true;
		    gtermClickPaste("", gterm_url, options);
		} else {
		    alert("Must drag-and-drop into directory");
		}
	    } else {
		var text = transfer.getData("text/plain") || "";
		var file_url = "";
		if (text) {
		    var srcText = makeFileURL(text);
		    var srcComps = splitFileURL(srcText);
		    if (srcComps) {
			file_url = srcText;
			text = srcComps[JFILENAME];
			var options = {};
			var dstComps = splitFileURL(gterm_url);
			if (gterm_mime == "x-graphterm/directory") {
			    options.command = "gcp";
			    options.dest_url = gterm_url;
			    options.enter = true;
			    gtermClickPaste("", file_url, options);
			} else if (gterm_mime == "x-graphterm/executable") {
			    options.command = dstComps[JFILEPATH];
			    gtermClickPaste("", file_url, options);
			} else {
			    gtermClickPaste(text, file_url, options);
			}
		    }
		}
	    }
	} catch (err) {
	    console.log("graphterm: GTDropHandler: "+err);
	}
    }

    return GTPreventHandler(evt);
}

function GTFileDrag(evt) {
    $(evt.target).toggleClass("hover", evt.type == "dragover");
    return GTPreventHandler(evt);
}

function GTFileBrowse(evt) {
    console.log("graphterm: GTFileBrowse: ", evt);
    try {
	var target = null;
	if (evt.target) {
	    var newTarget = $(evt.target).parent().find(".gterm-filedrop");
	    if (newTarget.length)
		target = newTarget[0];
	}

	GTFileDropHandler.call(this, target);
	if (evt.target)
	    $(evt.target).addClass("ui-disabled");
    } catch (err) {
	console.log("graphterm: GTFileBrowse: "+err);
    }
    return GTPreventHandler(evt);
}

function GTFileDropHandler(target) {
    if (this.files.length != 1) {
	alert("Please select a single file");
	return;
    }
    var file = this.files[0];
    var reader = new FileReader();
    reader.onload = function(evt) {
	var dataUri = evt.target.result;
	var offset = dataUri.indexOf("base64,");
	var b64_data = dataUri.substr(offset+"base64,".length);
	if (gExpectUpload) {
	    gExpectUpload = null;
	    GTTransmitFile(file.name, file.type, b64_data);
	} else {
	    gUploadFile = [file.name, file.type, b64_data];
	}
    };

    reader.onerror = function(evt) {
	alert("Failed to read file "+file.name+" (code="+evt.target.error.code+")");
    };

    reader.readAsDataURL(file);
}

function GTTransmitFile(filename, mimetype, b64_data) {
    gExpectUpload = null;
    gUploadFile = null;
    $("#session-bufscreen .gterm-upload").remove();
    console.log("GTTransmitFile:", filename, mimetype, b64_data.length);
    if (gWebSocket && gParams.controller) {
	gWebSocket.write([["save_data", {x_gterm_filepath: filename, content_type: mimetype,
					 x_gterm_location: "remote", x_gterm_encoding: "base64"}, b64_data]]);
    }
}

function GTUploadCancel(evt) {
    console.log("GTUploadCancel");
    GTTransmitFile("", "none/none", "");
}

function ScrollEventHandler(event) {
    if (gProgrammaticScroll) {
	gProgrammaticScroll = false;
	gManualScroll = false;
	return
    }

    // Non-programatic scroll event
    //console.log("ScrollEventHandler");
    gManualScroll = true;
    if (gWebSocket && gWebSocket.terminal && !gWebSocket.alt_mode) {
	var nrows = $("#session-screen > span.row").length;
	if (gSplitScreen) {
	    if (gAlwaysSplitScreen) {
		// Unsplit screen if not single command line
		if (nrows != 1 || !$("#session-screen > span.row span.gterm-cmd-prompt").length)
		    MergeScreen("scrollevent");
	    } else {
		// Merge screen if scrolling down to bottom (after scrolling up at least a bit)
		var offset = $("#session-bufscreen").offset().top+$("#session-bufscreen").height() - $("#session-screencontainer").offset().top;
		//console.log("ScrollEvent: offset", offset);
                if (offset < -5 && gMaxScrollOffset > 0)
		    MergeScreen("scrollevent");
		gMaxScrollOffset = Math.max(offset, gMaxScrollOffset);
	    }

	} else if (gAlwaysSplitScreen && nrows == 1 && $("#session-screen > span.row span.gterm-cmd-prompt").length) {
	    // Split screen if command line non-empty
	    var nprompt = $("#session-screen > span.row span.gterm-cmd-prompt").text().length;
	    if ($("#session-screen > span.row").text().length > nprompt+1)
		SplitScreen("scroll");
	}
    }
}

function ScrollTop(offset) {
    if (gAnimatingSplash)
	return;
    gProgrammaticScroll = true;
    if (typeof(offset) == "undefined" || offset == null)
	offset = $(document).height() - $(window).height(); // Scroll to bottom
    if (offset >= 0)
	$(window).scrollTop(offset);
}

function ScrollTerm() {
    // Scroll to bottom of terminal
    var bot_offset = $("#session-term").offset().top + $("#session-term").height();
    $(window).scrollTop(bot_offset - $(window).height());
}

function GTermHelp() {
    GTPopAlert('<b>GraphTerm Help</b>'+
'<p>\n&nbsp;&nbsp;<a href="/_static/docs/html/contents.html" target="_blank">General help information</a>'+
'<p>\n&nbsp;&nbsp;<a href="/_static/docs/html/virtual-lab.html" target="_blank">Virtual computer lab</a>'+
'<p>\n&nbsp;&nbsp;<a href="/_static/docs/html/troubleshooting.html" target="_blank">Troubleshooting</a>'+
'<p>\n&nbsp;&nbsp;<a href="https://groups.google.com/group/graphterm" target="_blank">Mailing list</a> (<b>NEW</b>)',
               true);
}

function GTermAbout() {
    if (gNotebook || gMobileBrowser)
	GTPopAlert(GTAboutText(), true);
    else
	GTShowSplash(true, true, true);
}

function GTAboutText() {
    return '<b>'+GTEscape(gParams.about_description)+"</b><p>\n&nbsp;&nbsp;Version: "+gParams.about_version+
	   '<p>\n&nbsp;&nbsp;Author(s): '+ GTEscape(gParams.about_authors.join(", "))+
           '<p class="gtermsplashalt">\n&nbsp;&nbsp;Website: <a href="'+gParams.about_url+'" target="_blank">'+gParams.about_url+'</a></p>'+
           '<p class="gtermsplashalt">\n&nbsp;&nbsp;Mailing list: <a href="https://groups.google.com/group/graphterm" target="_blank">https://groups.google.com/group/graphterm</a> (<b>NEW</b>)</p>'+
           '<p class="gtermsplashalt">\n&nbsp;&nbsp;Twitter: <a href="https://twitter.com/intent/user?screen_name=graphterm" target="_blank">@graphterm</a></p>';
}

var gSplashText = '<h3>GraphTerm is a <em>graphical terminal interface</em> the blends the command line with the graphical user interface.</h3>'+
                  '<p><h3>Type a Bash shell command or click <em>home</em> on the menubar to get started.</h3>'+
                  '<h3 class="gtermsplashalt">GraphTerm was developed as part of the Mindmeldr project. For more information, see <a target="_blank" href="http://code.mindmeldr.com/graphterm">code.mindmeldr.com/graphterm</a></h3>';

function GTShowSplash(force, animate, about) {
    if (!force && $("#gtermsplash").hasClass("hidesplash"))
	return;
    console.log("GTShowSplash:", force, animate, about);
    $("#gtermsplashtext").html(about ? GTAboutText() : gSplashText);
    if (force && !$("#gtermsplash").hasClass("noshow")) {
	GTHideSplash(true);
	return;
    }

    gShowingSplash = true;
    $("#gtermsplash").attr("style", "").removeClass("hidesplash").removeClass("noshow");

    if ($(window).height() > 3*$("#terminal").height()) {
	ScrollTop(0);
    } else {
	setTimeout(ScrollTop, 200);
    }
}

function GTHideSplash(animate, rotate) {
    console.log("GTHideSplash: ", animate, rotate);
    if ($("#gtermsplash").hasClass("hidesplash"))
	return;
    $("#gtermsplash").addClass("hidesplash");
    gShowingSplash = false;
    if (gAnimatingSplash)
	return;
    if (animate) {
	$("#gtermsplashdiv img").css("top", $("#gtermsplashdiv img").offset().top - $(window).scrollTop());
        $("#gtermsplashdiv").addClass("gtermsplashanchor");
	gAnimatingSplash = true;
	var offset = $("#gtermsplash").offset().top;
	var props = { opacity: 0.0, "gtermAnimate": 1.0};
	if ($(window).height() > offset) {
	    offset = 0;
	    props["margin-top"] ="+=300px";
	}
	$("#gtermsplash").animate(
	props,
        {
           duration: 2500,
	   step: function(now, tween) {
               if (tween && tween.prop === "gtermAnimate") {
		   if (offset > 0)
                       $(window).scrollTop(offset - now*$(window).height());
		   if (rotate) {
                       $("#gtermsplashdiv img").css('width',(200*(1.0-now))+"px");
                       $("#gtermsplashdiv img").css('height',(200*(1.0-now))+"px");
                       $("#gtermsplashdiv img").css('margin-left',(-100*(1.0-now))+"px");
                       $("#gtermsplashdiv img").css('transform','rotate('+(now*75)+'deg)');
		   }
               }
           },
	   complete: GTEndSplashAnimate
       });
    } else {
	GTEndSplashAnimate();
	if ($(window).height() < $("body").height())
	    ScrollTop(null);
	else
	    ScrollTop(0);
    }
}

function GTEndSplashAnimate() {
    //console.log("GTEndSplashAnimate: ");
    $("#gtermsplash").addClass("noshow");
    //$("#gtermsplash").hide();
    $("#gtermsplashdiv").removeClass("gtermsplashanchor");
    $("#gtermsplashdiv img").css("width", "");
    $("#gtermsplashdiv img").css("height", "");
    $("#gtermsplashdiv img").css("margin-left", "");
    $("#gtermsplashdiv img").css("top", "");
    $("#gtermsplashdiv img").css("transform", "");
    $("#gtermsplash").css("gtermAnimate", "0");
    gAnimatingSplash = false;
    if ($(window).height() > $("#terminal").height())
	ScrollTop(0);
}

function ScrollScreen(alt_mode) {
    if (gTestBatchedScroll && !gManualScroll)
	return;
    var screen_id = alt_mode ? "#session-altscreen" : "#session-screencontainer";
    if (!$(screen_id).height())
	screen_id = "#session-term";

    var bot_offset = $(screen_id).offset().top + $(screen_id).height();
    var winHeight = $(window).height();
    if (gMobileBrowser && winHeight != window.innerHeight)
	winHeight = Math.min($(window).height(), window.innerHeight) - (window.orientation?50:25);

    if (bot_offset > winHeight)
	ScrollTop(bot_offset - winHeight + gBottomMargin);
    else
 	ScrollTop(0);
}

function GTLoadMathJax() {
    try{
	var head = document.getElementsByTagName("head")[0], script;
	var script = document.createElement("script");
	script.type = "text/x-mathjax-config";
	script[(window.opera ? "innerHTML" : "text")] =
	  "MathJax.Hub.Config({\n" +
          " tex2jax: {\n" +
          "    inlineMath: [ ['$','$'], ['\\\\(','\\\\)'] ],\n" +
          "    displayMath: [ ['$$','$$'], ['\\\\[','\\\\]'] ],\n" +
          "    processEscapes: true,\n" +
          "    processEnvironments: true\n" +
          " },\n" +
          " skipStartupTypeset: true,\n" +
          " displayAlign: 'left',\n" +
          " 'HTML-CSS': {\n" +
          "    styles: {'.MathJax_Display': {'margin': 0}}\n" +
          " }\n" +
	  "});"
	head.appendChild(script);
	script = document.createElement("script");
	script.type = "text/javascript";
	script.src  = "//cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML";
	head.appendChild(script);
    } catch(ex) {
    }
}

function GTApplyMathJax(elementId) {
    if (!window.MathJax)
	return
    MathJax.Hub.Queue(["Typeset",MathJax.Hub,elementId]);
}

$(window).unload(function() {
    if (gForm)
	GTEndForm("", true);
});

$(document).ready(function() {
    if (!("WebSocket" in window)) {
	$("body").text("This browser does not support the WebSocket interface that is required for GraphTerm to work. Please use another browser that supports it, such as the latest versions of Chrome/Firefox/Safari or IE10.");
	return false;
    }

    try {
	return GTReady();
    } catch(err) {
	$("body").text("Error in starting GraphTerm: "+err+"\n"+err.stack);
	return false;
    }
});

function GTPasteSetup(altImpl, debug) {
    if (debug) {
	gAltPasteImpl = altImpl;
	gPasteDebug = true;
	$("body").unbind("paste");
	$(".gterm-pastedirectclose").unbind("click");
	$(".cursorspan").unbind("paste");
	$(".cursorspan").unbind("click");
	$(".gterm-pastedirect-content").addClass("gterm-paste-debug");
	if (altImpl)
	    $(".gterm-pastedirect").show();
	else
	    $(".gterm-pastedirect").hide();
    }
    if (altImpl) {
	$("body").rebind("paste",  GTAltPasteHandler);
	$(".gterm-pastedirectclose").click(GTAltPasteHandlerAux);
    } else {
	$(".cursorspan").rebind("paste", pasteHandler);
	$(".cursorspan").rebind("click", pasteReadyHandler);
    }
}

function GTReady() {
    console.log("GTReady");
    //LoadHandler();
    $(document).attr("title", window.location.pathname.substr(1));

    if (gMobileBrowser) {
	$("body").addClass("mobilescreen");
	ToggleFooter();
    }
    if (gTouchBrowser) {
	$("body").addClass("touchscreen");
    }
    if (gSafariIPad)
	$("body").addClass("ipadscreen");

    GTMenuSetup();

    setupTerminal();
    popupSetup();
    $("#session-bufellipsis").hide();
    $("#session-bufellipsis").bindclick(EndFullpage);
    $("#session-findercontainer").hide();
    $("#session-widgetcontainer").hide();  // IMPORTANT (else top menu will be invisibly blocked)
    $("#session-footermenu select").change(gtermBottomSelectHandler);
    $("#gterm-header .headfoot-icon").bindclick(gtermMenuClickHandler);
    $("#session-footermenu .headfoot").bindclick(gtermMenuClickHandler);
    $("#menubar-sessionlabel-link").bindclick(gtermCloneSession);
    $("#session-chat-button").bindclick(gtermChatHandler);
    $("#session-alert-button").bindclick(gtermAlert);

    $("#authenticate").hide();
    $("#gterm-terminal-list").hide();

    //window.addEventListener("dragover", GTDragOver);
    window.addEventListener("drop", GTDropHandler);

    $(".gterm-popup").hide();
    $(".gterm-popupmask").hide();
    $(".gterm-popupmask, .gterm-popupclose").click(popupClose);

    $(".gterm-pastedirect").hide();

    if (gAltPasteImpl) {
	GTPasteSetup(true);
    }

    if (gMobileBrowser)
	GTHideSplash();

    $(GTNextEntry()).appendTo("#session-log");

    $(window).scroll(ScrollEventHandler);

    // Bind window keydown/keypress events
    $(document).keydown(keydownHandler);
    $(document).keypress(keypressHandler);

    if (gAndroid) {
	$("#headfoot-keyboard").focus(AltKeyboardFocus);
	$("#headfoot-keyboard").blur(AltKeyboardBlur);
	$("#headfoot-keyboard").keyup(AltKeyboardHandler);
    }

    $(window).resize(handle_resize);

    Connect();
}

function alt_save_notebook() {
    if (gNotebook)
	gNotebook.altSave()
}
