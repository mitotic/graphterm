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

var gMobileBrowser = ('ontouchstart' in window) || gUserAgent.indexOf("android") > -1 || gUserAgent.indexOf("mobile") > -1 || gUserAgent.indexOf("touch") > -1;

var gSafariIPad = gSafariBrowser && gUserAgent.indexOf('ipad') > -1;

var gDefaultEditor = gMobileBrowser ? "ckeditor" : "ace";

var gAltPasteImpl = !gFirefoxBrowser && !gMobileBrowser;  // Alternative paste implemention (using hidden textarea)

var gPasteSpecialKeycode = 20;  // Control-T shortcut for Paste Special

var MAX_LINE_BUFFER = 500;
var MAX_COMMAND_BUFFER = 100;

var REPEAT_MILLISEC = 500;

var RELEASE_NOTES_URL = "http://code.mindmeldr.com/graphterm/release-notes.html";
var PYPI_URL = "http://pypi.python.org/pypi/graphterm";
var PYPI_JSON_URL = PYPI_URL + "/json?callback=?";

var WRITE_LOG = function (str) {};
var DEBUG_LOG = function (str) {};
var DEBUG_LOG = function (str) {console.log(str)};

var OSH_ECHO = true;

var ELLIPSIS = "...";

var gRowHeight = 16;
var gColWidth  = 8;
var gBottomMargin = 14;

var gRows = 0;
var gCols = 0;
var gWebSocket = null;

var gTextEditing = null;

var gFeedback = false;

var gScriptBuffer = [];

var gForm = null;
var gFormIndex = null;

var gDebug = true;
var gDebugKeys = false;
var gDebugMessages = false;

var gTypeAhead = false;   // Does not work very well

var gAlwaysSplitScreen = gMobileBrowser;
var gSplitScreen = false;
var gShowingFinder = false;

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

var gParams = {};

var GTPrompt = "&gt; ";
var GTCurDirURI = "";

// Scroll line array components
var JINDEX = 0
var JOFFSET = 1
var JDIR = 2
var JMARKUP = 3
var JLINE = 4

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

var FILE_URI_PREFIX = "file:/"+"/"; // Split double slash for minification
var FILE_PREFIX = "/file/";
var JSERVER = 0;
var JHOST = 1;
var JFILENAME = 2;
var JFILEPATH = 3;
var JQUERY = 4;

function utf8_to_b64(utf8str) {
    return $.base64.encode(unescape(encodeURIComponent(utf8str)));
}

function b64_to_utf8(b64str) {
    return decodeURIComponent(escape($.base64.decode(b64str)));
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
//        or http://server:port/file/host/path, or /file/host/path URLs.
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

function AuthPage(need_user, need_code, msg) {
    $("#authcode").val("");

    if (need_user)
	$("#authusercontainer").show();
    else
	$("#authusercontainer").hide();

    if (need_code)
	$("#authcodecontainer").show();
    else
	$("#authcodecontainer").hide();
	
    $("#authmessage").text(msg||"");
    $("#authenticate").show();

    $("#terminal").hide();
    $("#session-container").hide();
}

function Authenticate() {
    Connect($("#authuser").val(), $("#authcode").val());
}

function Connect(auth_user, auth_code) {
    gWebSocket = new GTWebSocket(auth_user, auth_code);
}

function SignOut() {
    setCookie("GRAPHTERM_AUTH", null);
    $("body").html('Signed out.<p><a href="/">Sign in again</a>');
}

function bind_method(obj, method) {
  return function() {
    return method.apply(obj, arguments);
  }
}

function setupTerminal() {
    gRowHeight = $("#session-screen").height() / 25;
    gColWidth = $("#session-screen-testrow").width() / 80;
    
    $("#session-screen").html("");
    $("#session-term").hide();
    $("#session-altscreen").hide();
    $("#session-log .curentry .input .command").focus();
}

function handle_resize() {
    gRows = Math.floor($(window).height() / gRowHeight) - 1;
    gCols = Math.floor($(window).width() / gColWidth) - 1;
    if (gWebSocket && gParams.controller)
	gWebSocket.write([["set_size", [gRows, gCols]]]);
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

function GTGetCommandText(n) {
    var commandPrefix = (gWebSocket && gWebSocket.terminal) ? "entry" : gCommandPrefix
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
    var innerEditable = gFirefoxBrowser ? "true" : "false";
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
    if (!$("#gtermsplash").hasClass("hidesplash"))
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
    var label_text = "Session: "+gParams.host+"/"+gParams.term+"/"+(gParams.controller ? "control" : "watch");
    $("#menubar-sessionlabel").text(label_text);
    if (gParams.controller)
	window.name = gParams.host+"/"+gParams.term;
    else
	window.name = "";
    if (gParams.controller)
	handle_resize();
}

function GTClearTerminal() {
    $("#session-bufscreen").children().remove();
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

function GTWebSocket(auth_user, auth_code) {
    this.failed = false;
    this.opened = false;
    this.closed = false;
    this.auth_user = auth_user || "";
    this.auth_code = auth_code || "";

    this.icons = false;
    this.terminal = false;

    this.webcast = false;
    this.theme = "default";
    this.alt_mode = false;

    this.repeat_command = "";
    this.repeat_intervalID = null;

    var protocol = (window.location.protocol.indexOf("https") == 0) ? "wss" : "ws";
    this.ws_url = protocol+":/"+"/"+window.location.host+"/_websocket"+window.location.pathname; // Split the double slash to avoid confusing the JS minifier
    if (this.auth_user || this.auth_code)
	this.ws_url += "?" + $.param({user: auth_user, code: auth_code});
    console.log("GTWebSocket url", this.ws_url);
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
	$(this).height($(this).contents().find('body').height() + 25);} ) }, 500 );
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

            } else if (action == "abort") {
		alert(command[1]);
		window.location = "/";

            } else if (action == "alert") {
		alert(command[1]);

            } else if (action == "authenticate") {
		if (getCookie("GRAPHTERM_AUTH"))
		    setCookie("GRAPHTERM_AUTH", null);
		if (window.location.pathname == "/"){
		    AuthPage(command[1], command[2], command[3]);
		} else {
		    window.location = "/";
		}

            } else if (action == "open") {
		OpenNew(command[1], command[2]);

            } else if (action == "redirect") {
		window.location = command[1];

            } else if (action == "update") {
		if (command[1] == "controller") {
		    gParams.controller = command[2];
		    GTUpdateController();
		}

            } else if (action == "setup") {
		$("#authenticate").hide();
		$("#terminal").show();
		$("#session-container").show();
		gParams = command[1];
		GTUpdateController();
		gtermFeedbackStatus(gParams.feedback);

		if (gParams.host_secret)
		    setCookie("GRAPHTERM_HOST_"+gParams.normalized_host, ""+gParams.host_secret);

		if (gParams.state_id)
		    setCookie("GRAPHTERM_AUTH", gParams.state_id);
		if (!gParams.oshell)
		    openTerminal();
		if (gParams.controller && gParams.display_splash && gParams.term != "osh")
		    GTShowSplash();

            } else if (action == "host_list") {
		if (command[1])
		    setCookie("GRAPHTERM_AUTH", command[1]);
		var hosts = command[2];
		var host_html = 'Hosts available:<p><ol>';
		for (var j=0; j<hosts.length; j++)
		    host_html += '<li><a href="/'+hosts[j]+'">'+hosts[j]+'</a></li>';
		host_html += '</ol> <p><a href="#" onclick="SignOut();">Sign out</a>';
		$("body").html(host_html);

            } else if (action == "term_list") {
		if (command[1])
		    setCookie("GRAPHTERM_AUTH", command[1]);
		var host = command[2];
		var terms = command[3];
		var term_html = 'Connect to session:<p><ol>';
		for (var j=0; j<terms.length; j++)
		    term_html += '<li><a href="/'+host+'/'+terms[j]+'">'+terms[j]+'</a></li>';
		term_html += '<li><a href="/'+host+'/new"><b><em>new</em></b></a></li>';
		term_html += '</ol> <p><a href="#" onclick="SignOut();">Sign out</a>';
		$("body").html(term_html);

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
		var frameName = command[3];
		gFrameDispatcher.receive(fromUser, toUser, frameName, command[4]);

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
		    GTPopAlert("File "+cmd_arg[0]+": "+(cmd_arg[1] || "saved"));

 		} else if (cmd_type == "frame_msg") {
		    try {
			var json_msg = JSON.parse(cmd_arg[2]);
			gFrameDispatcher.receive("", cmd_arg[0], cmd_arg[1], json_msg);
		    } catch (err) {
			console.log("ERROR in frame_msg:", err, content);
		    }

		} else if (cmd_type == "graphterm_feedback") {
		    gtermFeedbackStatus(cmd_arg);

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
			    gWebSocket.write([["save_file", response_params.filepath, utf8_to_b64(cmdText)]]);

			} else if (response_params.action == "buffer") {
			    if (response_params.modify) {
				EndFullpage();
				var editText = gScriptBuffer.length ? gScriptBuffer.join("\n")+"\n" : "";
				GTStartEdit(response_params, editText);
			    } else {
				GTBufferScript(content);
			    }
			}

		    } else if (response_type == "edit_file") {
			EndFullpage();
			GTStartEdit(response_params, content);

 		    } else if (response_type == "pagelet_json") {
			try {
			    var json_obj = JSON.parse(content);
			    GTPageletJSON($(".pagelet."+entry_class), json_obj);
			} catch (err) {
			    console.log("ERROR in pagelet_json:", err, content);
			}

		    } else if (!response_type || response_type == "pagelet") {
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
				var prevBlock = $("#session-bufscreen .pagelet.gterm-blockseq:not(.gterm-blockseqtoggle)");
				if (response_params.block && response_params.block == "overwrite" && prevBlock.length == 1 && prevBlock.is($("#session-bufscreen :last-child")) ) {
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
				    prevBlock.addClass("gterm-blockseqtoggle").addClass("gterm-blockseqhide");
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
			    $(pageletSelector+' td .gterm-link').bindclick(gtermPageletClickHandler);
			    $(pageletSelector+' td img').bind("dragstart", function(evt) {evt.preventDefault();});
			    $(pageletSelector+' .gterm-blockseqlink').bindclick(gtermLinkClickHandler);
			    $(pageletSelector+' .gterm-iframeclose').bindclick(gtermInterruptHandler);
			    GTDropBindings($(pageletSelector+' .droppable'));
			} catch(err) {
			    console.log("GTWebSocket.onmessage: Pagelet ERROR: ", err);
			}
		    }
		} else if (cmd_type == "row_update") {
                    var alt_mode    = cmd_arg[0];
                    var reset       = cmd_arg[1];
                    var active_rows = cmd_arg[2];
                    var term_width  = cmd_arg[3];
                    var term_height = cmd_arg[4];
                    var cursor_x    = cmd_arg[5];
                    var cursor_y    = cmd_arg[6];
                    var pre_offset  = cmd_arg[7];
		    var update_rows = cmd_arg[8];
		    var update_scroll = cmd_arg[9];

		    if (alt_mode && !this.alt_mode) {
			this.alt_mode = true;
			if (gSplitScreen)
			    MergeScreen("alt_mode");
			$("#session-screen").hide();
			$("#session-altscreen").show();
		    } else if (!alt_mode && this.alt_mode) {
			this.alt_mode = false;
			$("#session-screen").show();
			$("#session-altscreen").hide();
		    }

		    // Note: Paste operation pastes DOM elements with "span.row" class into screen
                    // Therefore, need to restrict selector to immediate children of #session-screen
		    var nrows = $("#session-screen > span.row").length;

		    if (!alt_mode && (reset || nrows != active_rows)) {
			if (reset) {
			    $("#session-screen").empty();
			    nrows = 0;
			    if (gSplitScreen)
				MergeScreen("reset");
			}

			if (gSplitScreen && active_rows != 1)
			    MergeScreen("rows");

			if (active_rows < nrows) {
			    for (var k=active_rows; k<nrows; k++)
				$("#gterm-pre"+k).remove();
			} else if (active_rows > nrows) {
			    for (var k=nrows; k<active_rows; k++)
				$('<span id="'+"gterm-pre"+k+'" class="row">\n</span>').appendTo("#session-screen");
			    if (gSplitScreen)
				ResizeSplitScreen(true);
			}
		    }

		    if (alt_mode && (reset || !$("#session-altscreen span.row").length)) {
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
			    if (row_num == cursor_y) {
				gCursorAtEOL = (cursor_x == row_line.length);
				var cursor_char = gCursorAtEOL ? ' ' : row_line.substr(cursor_x,1);
				line_html += GTEscape(row_line.substr(0,cursor_x), pre_offset, prompt_offset)+GTCursorSpan(cursor_char)+GTEscape(row_line.substr(cursor_x+1));
			    } else {
				line_html += GTEscape(row_line, pre_offset, prompt_offset);
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
			    if (row_num == cursor_y && cursor_x >= row_line.length) {
				// Cursor at end of line; pad with spaces to extend to cursor location
				for (var k=row_line.length; k<cursor_x; k++)
				    line_html+= " ";
				// Display cursor
				line_html += GTCursorSpan(' ');
			    }
			}
			var idstr = (alt_mode ? "gterm-alt" : "gterm-pre") + row_num;
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
			$(".cursorspan").rebind("paste", pasteHandler);
			$(".cursorspan").rebind("click", pasteReadyHandler);
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
			    if (prompt_offset) {
				entry_class += " promptrow";
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
			    var markup = update_scroll[j][JMARKUP];
			    var row_escaped = (markup == null) ? GTEscape(update_scroll[j][JLINE], pre_offset, prompt_offset, prompt_id) : markup;
			    var row_html = '<pre id="'+entry_id+'" class="row entry '+entry_class+'">'+row_escaped+"\n</pre>";
			    $(row_html).appendTo("#session-bufscreen");
			    $("#"+entry_id+" .gterm-link").bindclick(gtermLinkClickHandler);
			}
		    }

		    if (gScrollTop) {
			gScrollTop = false;
			ScrollTop(0);
		    } else if (!$("body").hasClass("three-d")) {
			if (!gSplitScreen)
			    ScrollScreen(alt_mode);
		    } else {
			$("#session-term").scrollTop($("#session-term")[0].scrollHeight - $("#session-term").height())
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
	console.log("GTWebSocket.onmessage", err);
	this.write([["errmsg", ""+err]]);
	this.close();
    }
}

GTWebSocket.prototype.onclose = function(e) {
  console.log("GTWebSocket.onclose: ");
  if (!this.opened && !this.closed && !this.failed) {
      this.failed = true;
      alert("Failed to open websocket: "+this.ws_url);
  }
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
    var commandId = gCommandPrefix+gEntryIndex;
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
    var elem = $(this);
    setTimeout(function() {
	var cursor_char = elem.attr("data-gtermcursorchar");
	var pasteText = "";
	var innerElem = elem.children(".cursorloc");

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

function GTAltPasteHandler() {
    console.log("GTAltPasteHandler:");
    if (gPopupActive || gForm)
	return true;

    setTimeout(GTAltPasteHandlerAux, 100);
    $("#gterm-pastedirect-content").val("");
    $(".gterm-pastedirect").show();
    $("#gterm-pastedirect-content").focus();
    return true;
}

function GTAltPasteHandlerAux() {
    $(".gterm-pastedirect").hide();
    var text = $("#gterm-pastedirect-content").val();
    $("#gterm-pastedirect-content").val("");
    console.log("GTAltPasteHandlerAux: ");
    if (text)
	gWebSocket.term_input(text);
    //setTimeout(function() { ScrollTop(null); }, 100);
}

function GTExportEnvironment() {
    if (gWebSocket && gWebSocket.terminal)
	gWebSocket.write([["export_environment"]]);
}

function gtermSelectHandler(event) {
    var idcomps = $(this).attr("id").split("-");
    var selectedOption = $(this).val();
    console.log("gtermSelectHandler: ", idcomps[1], selectedOption);

    GTReceivedUserInput("select");
    switch (idcomps[1]) {
    case "actions":
	$(this).val(1);

	if (selectedOption == "about")
	    GTermAbout();
	else if (selectedOption == "updates")
	    CheckUpdates();
	else if (selectedOption == "export_env")
	    GTExportEnvironment();
	else if (selectedOption == "paste_special")
	    GTPasteSpecialBegin();
	else if (selectedOption == "reconnect")
	    ReconnectHost();
	else if (selectedOption == "steal")
	    StealSession();
	break;

    case "icons":
	gWebSocket.icons = (selectedOption == "on");
	$("#terminal").toggleClass("showicons", gWebSocket.icons);
	break;

      case "webcast":
         // Webcast
	Webcast(selectedOption == "on");
      break;

      case "theme":
       // Select theme
       var three_d = (selectedOption.substr(selectedOption.length-2) == "3d");
       var base_theme = three_d ? selectedOption.substr(0, selectedOption.length-2) : selectedOption;

       if (gWebSocket.theme && gWebSocket.theme != "default")
	   $("body").removeClass(gWebSocket.theme);
       if (base_theme && base_theme != "default")
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
    }
}

function gtermMenuClickHandler(event) {
    var idcomps = $(this).attr("id").split("-");
    console.log("gtermMenuClickHandler", $(this).attr("id"), idcomps[1]);
    var text = "";
    switch (idcomps[1]) {
    case "home":
	if (gWebSocket)
	    gWebSocket.term_input("cd; gls\n");
	break;
    case "bottom":
	ScrollScreen();
	break;
    case "help":
	GTermHelp()
	break;
    case "collapse":
	$("#session-bufscreen .oldentry").addClass("gterm-hideoutput");
	break;
    case "expand":
	$("#session-bufscreen .oldentry").removeClass("gterm-hideoutput");
	break;
    case "clear":
	GTClearTerminal();
	if (gWebSocket && gWebSocket.terminal)
	    gWebSocket.write([["clear_term"]]);
	//text = "\x01\x0B";  // Ctrl-A Ctrl-K
	break;
    case "detach":
	window.location = "/";
	break;
    case "new":
	OpenNew();
	break;
    case "control":
	$("#headfoot-control").toggleClass("gterm-headfoot-active");
	gControlActive = $("#headfoot-control").hasClass("gterm-headfoot-active");
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
	text = "\n";
	if (gShowingFinder)
	    HideFinder();
	break;
    }
    if (text.length && gWebSocket) {
	gWebSocket.term_input(text);
    }
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
    ScrollTop(null);
}

function gtermFeedbackStatus(status) {
    gFeedback = status;
    $("#session-term").toggleClass("gterm-feedback", gFeedback);
}

function gtermFeedbackHandler(event) {
    gFeedbackText = "";
    $("#gterm-feedbackarea-content").val("");
    popupShow("#gterm-feedbackarea", gtermFeedbackAction, gtermFeedbackConfirmClose, "feedback");
}

gFeedbackText = null;
function gtermFeedbackConfirmClose() {
  if (gFeedbackText == $("#gterm-feedbackarea-content").val()) {
    // No changes
    return true
  }
  return false;
}

function gtermFeedbackAction(buttonElem) {
    var action = $(buttonElem).attr("name");
    var text = $("#gterm-feedbackarea-content").val();
    //console.log("popupButton", action, text);
    if (action == "send")
	gWebSocket.write([["feedback", text+"\n"]]);
    popupClose();
}

function gtermClickPaste(text, file_url, options) {
    gWebSocket.write([["click_paste", text, file_url, options]]);
    if (!gSplitScreen)
	SplitScreen("paste");
}

function gtermInterruptHandler(event) {
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

    } if ($(this).hasClass("gterm-cmd-text")) {
	gtermClickPaste($(this).text(), file_url, options);

    } if ($(this).hasClass("gterm-cmd-path")) {
	file_url = makeFileURL($(this).attr("href"));
	gtermClickPaste("", file_url, options);

    } if ($(this).hasClass("gterm-blockseqlink")) {
	$(this).parent(".gterm-blockseqtoggle").toggleClass("gterm-blockseqhide");
    }

    if (contextMenu) {
	alert("Context menu not yet implemented");
	return false;
    }

    console.log("gtermLinkClickHandler", file_url, options);
    return false;
}

function gtermPageletClickHandler(event) {
    var confirm = $(this).attr("data-gtermconfirm");
    if (confirm) {
	if (!window.confirm(confirm)) {
	    return false;
	}
    }

    var contextMenu = gControlActive;
    GTReceivedUserInput("click");
    var text = $(this).text();
    var pagelet = $(this).closest(".pagelet");
    var file_url = makeFileURL($(this).attr("href"));

    if (contextMenu) {
	alert("Context menu not yet implemented");
	return false;
    }

    var options = {enter: true}
    options.command = $(this).attr("data-gtermcmd");
    var cd_command = (options.command.indexOf("cd ") == 0);
    options.clear_last = (pagelet.length && cd_command) ? pagelet.attr("data-gtermpromptindex") : "0";

    gtermClickPaste("", file_url, options);
    //console.log("gtermPageletClickHandler", file_url, options);
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
    if (text.length && gWebSocket) {
	gWebSocket.term_input(text);
    }
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

function keydownHandler(evt) {
    var activeTag = "";
    var activeType = "";
    var activeElem = $(document.activeElement);

    if (GTCaptureInput())
	return true;

    if (gDebugKeys)
	console.log("graphterm.keydownHandler: ", evt.keyCode, evt.which, evt);

    GTExpandCurEntry(false);

    if (evt.which >= 33 && evt.which <= 46) {
	// Special keys (arrow keys etc.)
	if (evt.which==0 || (gWebkitBrowser && evt.charCode==0) ) {
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

function pasteKeyHandler(evt) {
    //console.log("graphterm.pasteKeyHandler: code ", evt.keyCode, evt.which, evt);
    if (evt.ctrlKey && (evt.which == gPasteSpecialKeycode || evt.which == (gPasteSpecialKeycode+64) || evt.which == (gPasteSpecialKeycode+96))) {
	GTPasteSpecialEnd($("#gterm-pastearea-pastetext"));
	return false;
    }
    return true;
}

function keypressHandler(evt) {
    if (gDebugKeys)
	console.log("graphterm.keypressHandler: code ", evt.keyCode, evt.which, evt);

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

    if (kc == 13 && gScriptBuffer.length && (evt.ctrlKey || gControlActive)) {
	// Scripted command
	var scriptText = gScriptBuffer.shift();
	if (scriptText.length)
	    gWebSocket.term_input(scriptText+"\n", null, true);
	return false;
    }

    var formSubmitter = ".pagelet.entry"+gPromptIndex+" .gterm-form-command";
    if (kc == 13 && gForm && gParams.controller && $(formSubmitter).length == 1) {
	$(formSubmitter).click();
	return false;
    }

    if (!evt.ctrlKey && !gControlActive && GTCaptureInput()) {
	// Not Ctrl character; editing/processing form
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

    } else if (evt.which==0 || (gWebkitBrowser && evt.charCode==0 && kc >=33 && kc <= 46) ) {
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

    if (gForm && k == String.fromCharCode(3)) {
	// Ctrl-C exit from form
	GTEndForm("", true);
    } else if (gPopupType && k == String.fromCharCode(3)) {
	// Ctrl-C exit from popup
	popupClose();
	return false;
    } else if (GTCaptureInput()) {
	// Editing or processing form
	return true;
    }

    if (k.length) {
	if (evt.ctrlKey && k.charCodeAt(0) == gPasteSpecialKeycode) {
	    // Paste Special shortcut
	    GTPasteSpecialBegin();
            k = "";
	} else if (k.charCodeAt(k.length-1) == 13) {
	    // Enter key
	    if (gShowingFinder)
		HideFinder();
	    if (gCommandMatchPrev) {
		// Simulate right arrow for command completion
		if (!CompleteCommand(true))
		    k = "";
	    }
	}
	if (k)
	    gWebSocket.term_input(k, true);
    }
    evt.cancelBubble = true;
    return GTPreventHandler(evt);
}

function OpenNew(host, term_name, options) {
    host = host || gParams.host;
    term_name = term_name || "new";
    var path = host + "/" + term_name;
    var new_url = window.location.protocol+"/"+"/"+window.location.host+"/"+path; // Split the double slash to avoid confusing the JS minifier
    console.log("open", new_url);
    var target = (term_name == "new") ? "_blank" : path;
    window.open(new_url, target=target);
}

function GTermAbout() {
    GTPopAlert('<b>'+GTEscape(gParams.about_description)+"</b><p>\n&nbsp;&nbsp;Version: "+gParams.about_version+
	       '<p>\n&nbsp;&nbsp;Author(s): '+ GTEscape(gParams.about_authors.join(", "))+
               '<p>\n&nbsp;&nbsp;Website: <a href="'+gParams.about_url+'" target="_blank">'+gParams.about_url+'</a>'+
               '<p>\n&nbsp;&nbsp;Mailing list: <a href="https://groups.google.com/group/graphterm" target="_blank">https://groups.google.com/group/graphterm</a> (<b>NEW</b>)'+
               '<p>\n&nbsp;&nbsp;Twitter: <a href="https://twitter.com/intent/user?screen_name=graphterm" target="_blank">@graphterm</a>',
               true);
}

function GTermHelp() {
    GTPopAlert('<b>GraphTerm Help</b>'+
'<p>\n&nbsp;&nbsp;<a href="/static/docs/html/usage.html" target="_blank">General usage information</a>'+
'<p>\n&nbsp;&nbsp;<a href="/static/docs/html/troubleshooting.html" target="_blank">Troubleshooting</a>'+
'<p>\n&nbsp;&nbsp;<a href="https://groups.google.com/group/graphterm" target="_blank">Mailing list</a> (<b>NEW</b>)',
               true);
}

function CheckUpdates() {
    $.getJSON(PYPI_JSON_URL, function(data) {
	if (gParams.about_version == data.info.version) {
	    GTPopAlert('GraphTerm is up-to-date (version: '+gParams.about_version+').<p> There is  now a <a href="https://groups.google.com/group/graphterm" target="_blank">Mailing list</a> for GraphTerm.', true);
	} else {
	    GTPopAlert('A new release of GraphTerm ('+data.info.version+') is available!<br>See <a href="'+RELEASE_NOTES_URL+'" target="_blank">Release Notes</a> for details.<br> There is also a <em>new</em> <a href="https://groups.google.com/group/graphterm" target="_blank">Mailing list</a> for GraphTerm.<p>Upgrade using <b>sudo easy_install --upgrade graphterm</b><br>Followed by <b>sudo gterm_setup</b><br> OR download from the <a href="'+PYPI_URL+'" target="_blank">Python Package Index</a>', true);
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
    var steal_url = window.location.protocol+"/"+"/"+window.location.host+"/"+gParams.host+"/"+gParams.term+"/steal"; // Split the double slash to avoid confusing the JS minifier
    console.log("StealSession: ", steal_url);
    window.location = steal_url;
}

function Webcast(start) {
    console.log("Webcast", start);
    if (!gWebSocket)
	return;
    if (start && !window.confirm('Make terminal publicly viewable ("webcast")?'))
	return;

    $("#terminal").toggleClass("webcast", start);
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
    return gForm || (gTextEditing && gParams.controller) || gPopupType;
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
    console.log("GTStartEdit", editor, params);
    $("#terminal").hide();
    if (params.editor == "textarea") {
	gTextEditing = {params: params, content: content, editor: editor};
	$("#gterm-texteditarea-content").val(content);
	popupShow("#gterm-texteditarea", "editarea");
    } else {
	var editor = params.editor ? params.editor : gDefaultEditor;
	var url = gParams.apps_url+"/"+editor+".html";
	gFrameDispatcher.createFrame(params, content, url, "gterm-editframe");
	$("#gterm-editframe").attr("src", url);
	$("#gterm-editframe").show();
    }
}

function GTEndEditArea(save) {
    if (!gTextEditing)
	return;
    var newContent = $("#gterm-texteditarea-content").val();
    GTEndEdit(newContent, gTextEditing.content, gTextEditing.params, save);
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
		gWebSocket.write([["save_file", params.filepath, utf8_to_b64(newContent)]]);
	    }
	}
    }

    if (params.editor == "textarea") {
	$("#gterm-texteditarea-content").val("");
	popupClose(false);
	gTextEditing = null;
    } else {
	$("#gterm-editframe").attr("src", "");
	$("#gterm-editframe").hide();
    }
    $("#terminal").show();
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
	if (gForm && gForm.form_command)
	    gWebSocket.term_input(text+"\n", false, gForm.form_command);
    }
    if (gFormIndex)
	$("#session-bufscreen").children(".pagelet.entry"+gFormIndex).remove();
    $("#session-screen").show();
    gForm = null;
    gFormIndex = null;
}

function GTHelpLink(evt) {
    var helpStr = $(this).attr("data-gtermhelp");
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
    var argStr = "";
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
			formCommand += ' --' + inputName;
		    else
			formCommand += ' --' + inputName + '=' + inputValue;
		}
	    }
	} else {
	    if (inputValue.indexOf(" ") >= 0 && inputValue.substr(0,1) == '"' && inputValue.substr(inputValue.length-1) == '"')
		inputValue = inputValue.substr(1,inputValue.length-2);
	    formValues[inputName] = inputValue;
	}
    }
    if (formCommand)
	formCommand += argStr;
    else
	formCommand = JSON.stringify(formValues);
    console.log("GTFormSubmit", this, formElem, formCommand, evt);
    GTEndForm(formCommand);
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
    gFullpageDisplay = display;
    if (display == "fullpage") {
	$("#session-bufscreen").addClass("fullpage");
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
    this.frameProps = null;
    this.frameIndex = 0;
}

GTFrameDispatcher.prototype.createFrame = function(params, content, url, frameId) {
    url = url || params.url;
    if (!frameId) {
	this.frameIndex += 1;
	frameId = "frame" + this.frameIndex;
    }

    this.frameProps = {id: frameId, params: params, content: content,
                       controller: (gParams && gParams.controller)};
    return '<iframe id="'+frameId+'" src="'+url+'" width="100%" height="100%></iframe>';
}

GTFrameDispatcher.prototype.open = function(frameController, frameObj) {
    this.frameControllers[frameController.frameName] = {controller: frameController, props: this.frameProps};

    var frameId = $(frameObj).attr("id");
    if (frameController && "open" in frameController && this.frameProps && this.frameProps.id == frameId) {
	frameController.open(this.frameProps);
    }
    if (!gMobileBrowser) {
	$("#"+frameId).addClass("noheader");
	$("#"+frameId).attr("height", "100%");
	$(".gterm-iframeheader").hide();
    }
    $("#"+frameId).focus();
}

GTFrameDispatcher.prototype.send = function(toUser, toFrame, msg) {
    if (gWebSocket && gParams.controller)
	gWebSocket.write([["send_msg", toUser, toFrame, msg]]);
}

GTFrameDispatcher.prototype.write = function(text) {
    if (gWebSocket && gParams.controller)
	gWebSocket.term_input(text);
}

GTFrameDispatcher.prototype.receive = function(fromUser, toUser, frameName, msg) {
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
	if (!save && !window.confirm("Discard changes?"))
	    return;
	var newContent = save ? this.frameControllers[frameName].controller.getContent() : null;
	GTEndEdit(newContent, props.content, props.params, save);

	if (props.controller && props.params.action != "buffer") {
	    this.send("*", "editor", ["end", ""]);
	}
    }
    
    delete this.frameControllers[frameName];
    if (gWebSocket && gParams.controller)
	gWebSocket.term_input("\x03");
    EndFullpage();
}

var gFrameDispatcher = new GTFrameDispatcher();

function EndFullpage() {
    //console.log("EndFullpage");
    gFullpageDisplay = null;
    try {
	if (RunPrefixMethod(document, "FullScreen") || RunPrefixMethod(document, "IsFullScreen")) {
	    RunPrefixMethod(document, "CancelFullScreen");
	}
    } catch(err) {}

    $("#session-bufellipsis").hide();
    $("#session-bufscreen").removeClass("fullpage");
    if (gSplitScreen)
	MergeScreen("fullpage");

    $("#session-bufscreen .pagelet.gterm-fullwindow").removeClass("gterm-fullwindow");
}

function ExitFullpage() {
    EndFullpage();
    ScrollTop(null);
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
    if ($("#session-term").hasClass("display-footer"))
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
    
    $('#session-finderbody td .gterm-link').bindclick(gtermFinderClickHandler)

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
    if (gtDragElement != this) {
	try {
	    var gterm_mime = $(this).attr("data-gtermmime") || "";
	    var gterm_url = makeFileURL($(this).attr("href") || "");
	    if (evt.originalEvent.dataTransfer.files.length) {
	    } else {
		var text = evt.originalEvent.dataTransfer.getData("text/plain") || "";
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
    gProgrammaticScroll = true;
    if (offset == null)
	offset = $(document).height() - $(window).height(); // Scroll to bottom
    if (offset >= 0)
	$(window).scrollTop(offset);
}

function GTShowSplash(animate) {
    if ($("#gtermsplash").hasClass("hidesplash"))
	return;
    $("#gtermsplash").removeClass("noshow");
}

function GTHideSplash(animate) {
    if ($("#gtermsplash").hasClass("hidesplash"))
	return;
    $("#gtermsplash").addClass("hidesplash");
    if (animate) {
	$("#gtermsplash").animate({ 
            "margin-top": "+=300px",
            opacity: 0.0,
	}, 2000, function() { $("#gtermsplash").hide(); });
    } else {
	$("#gtermsplash").hide();
    }
}

function ScrollScreen(alt_mode) {
    if (gTestBatchedScroll && !gManualScroll)
	return;
    var screen_id = alt_mode ? "#session-altscreen" : "#session-screencontainer";
    var bot_offset = $(screen_id).offset().top + $(screen_id).height();
    var winHeight = $(window).height();
    if (gMobileBrowser && winHeight != window.innerHeight)
	winHeight = Math.min($(window).height(), window.innerHeight) - (window.orientation?50:25);
    if (bot_offset > winHeight)
	ScrollTop(bot_offset - winHeight + gBottomMargin);
    else
 	ScrollTop(0);
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
	$("body").text("Error in starting GraphTerm: "+err);
	return false;
    }
});

function GTReady() {
    console.log("GTReady");
    //LoadHandler();
    $(document).attr("title", window.location.pathname.substr(1));

    if (gMobileBrowser) {
	$("body").addClass("mobilescreen");
	ToggleFooter();
    }
    if (gSafariIPad)
	$("body").addClass("ipadscreen");

    setupTerminal();
    popupSetup();
    $("#gterm-editframe").hide();
    $("#session-bufellipsis").hide();
    $("#session-findercontainer").hide();
    $("#session-widgetcontainer").hide();  // IMPORTANT (else top menu will be invisibly blocked)
    $(".menubar-select").change(gtermSelectHandler);
    $("#session-footermenu select").change(gtermBottomSelectHandler);
    $("#session-headermenu .headfoot").bindclick(gtermMenuClickHandler);
    $("#session-footermenu .headfoot").bindclick(gtermMenuClickHandler);
    $("#session-feedback-button").bindclick(gtermFeedbackHandler);

    //window.addEventListener("dragover", GTDragOver);
    window.addEventListener("drop", GTDropHandler);

    $(".gterm-popup").hide();
    $(".gterm-popupmask").hide();
    $(".gterm-popupmask, .gterm-popupclose").click(popupClose);

    $(".gterm-pastedirect").hide();

    if (gAltPasteImpl) {
	$("body").rebind("paste",  GTAltPasteHandler);
	$(".gterm-pastedirectclose").click(GTAltPasteHandlerAux);
    }

    if (gMobileBrowser)
	GTHideSplash();

    $(GTNextEntry()).appendTo("#session-log");

    $(window).scroll(ScrollEventHandler);


    // Bind window keydown/keypress events
    $(document).keydown(keydownHandler);
    $(document).keypress(keypressHandler);

    $(window).resize(handle_resize);

    Connect();
}
