// GraphTerm Page Commands

// CONVENTION: All pre-defined GraphTerm Javascript functions and global
//             variables should begin with an upper-case letter.
//             This would allow them to be easily distinguished from
//             user defined functions, which should begin with a lower case
//             letter.


// Global variables

var gMobileBrowser = navigator.userAgent.toLowerCase().indexOf('mobile') > -1;
var gFirefoxBrowser = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
var gWebkitBrowser = navigator.userAgent.toLowerCase().indexOf('webkit') > -1;
var gChromeBrowser = navigator.userAgent.toLowerCase().indexOf('chrome') > -1;
var gSafariBrowser = !gChromeBrowser && navigator.userAgent.toLowerCase().indexOf('safari') > -1;

var gSafariIPad = gSafariBrowser && navigator.userAgent.toLowerCase().indexOf('ipad') > -1;

var FILE_URI_PREFIX = "file:/"+"/"; // Split double slash for minification

var MAX_LINE_BUFFER = 500;

var PYPI_URL = "http://pypi.python.org/pypi/graphterm";
var PYPI_JSON_URL = PYPI_URL + "/json?callback=?";

var WRITE_LOG = function (str) {};
var DEBUG_LOG = function (str) {};
var DEBUG_LOG = function (str) {console.log(str)};

var gRowHeight = 16;
var gColWidth  = 8;
var gBottomMargin = 14;

var gRows = 0;
var gCols = 0;
var gWebSocket = null;

var gEditing = null;

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

function makeFileURI(uri) {
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
	
    var prefix = "/file/";
    if (uri.substr(0,prefix.length) != prefix)
	return "";
    var path = uri.substr(prefix.length);
    var comps = path.split("/");
    if (comps[0] == "local")
	comps[0] = "";
    return FILE_URI_PREFIX + comps.join("/");
}

// Returns [hostname, filename, fullpath, query] for file://host/path URIs
// If not file URI, returns []
function splitFileURI(uri) {
    if (!uri || uri.substr(0,FILE_URI_PREFIX.length) != FILE_URI_PREFIX)
	return [];
    var hostPath = uri.substr(FILE_URI_PREFIX.length);
    var j = hostPath.indexOf("?");
    var query = "";
    if (j >= 0) {
	query = hostPath.substr(j)
	hostPath = hostPath.substr(0,j);
    }
    var comps = hostPath.split("/");
    return [comps[0], comps[comps.length-1], "/"+comps.slice(1).join("/"), query]
}

function getCookie(name) {
    return unescape($.cookie(name, {raw: true}));
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
	return cmdText;
    } else {
	return $(cmd_id).text() || "";
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
	var curtext = GTGetCurCommandText();
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
	newPath = (splitFileURI(fileURI))[2];
    }

    return decodeURIComponent(newPath);
}

function GTReceivedUserInput(source) {
    gControlActive = false;
    if (!$("#gtermsplash").hasClass("hidesplash"))
	GTHideSplash(true);
    $("#headfoot-control").removeClass("gterm-headfoot-active");
    if (source != "select") {
	gCommandBuffer = null;
	$("#gterm-pre0 .cmd-completion").text("");
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

    var protocol = (window.location.protocol.indexOf("https") == 0) ? "wss" : "ws";
    var ws_url = protocol+":/"+"/"+window.location.host+"/_websocket"+window.location.pathname; // Split the double slash to avoid confusing the JS minifier
    if (this.auth_user || this.auth_code)
	ws_url += "?" + $.param({user: auth_user, code: auth_code});
    console.log("GTWebSocket url", ws_url);
    this.ws = new WebSocket(ws_url);
    this.ws.onopen = bind_method(this, this.onopen);
    this.ws.onmessage = bind_method(this, this.onmessage);
    this.ws.onclose = bind_method(this, this.onclose);
    console.log("GTWebSocket.__init__: ");
}

GTWebSocket.prototype.term_input = function(text, type_ahead) {
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
    GTReceivedUserInput("key");
    this.write([["keypress", text]]);
    GTCurDirURI = "";
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

            if (action == "abort" || action == "authenticate") {
		if (getCookie("GRAPHTERM_AUTH"))
		    setCookie("GRAPHTERM_AUTH", null);
		if (window.location.pathname == "/"){
		    if (action == "authenticate")
			AuthPage(command[1], command[2], command[3]);
		    else
			alert(command[1]);
		} else {
		    window.location = "/";
		}

            } else if (action == "open") {
		OpenNew(command[1], command[2]);

            } else if (action == "redirect") {
		window.location = command[1];

            } else if (action == "setup") {
		$("#authenticate").hide();
		$("#terminal").show();
		$("#session-container").show();
		gParams = command[1];
		var label_text = "Session: "+gParams.host+"/"+gParams.term+"/"+(gParams.controller ? "control" : "watch");
		$("#menubar-sessionlabel").text(label_text);
		setCookie("GRAPHTERM_HOST_"+gParams.lterm_host, ""+gParams.lterm_cookie);

		if (gParams.controller)
		    handle_resize();
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
		var logtype = command[1] || "log";
		var prefix = logtype.toUpperCase()+": ";
		console.log(prefix+command[3]);
		$('<pre class="gterm-log">'+prefix+command[3]+'</pre>').appendTo("#session-log .curentry");
		$("#session-log .curentry .gterm-log .gterm-link").bindclick(otraceClickHandler);

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
		if (action == "html_output") {
		    var pagelet_html = '<div class="pagelet">'+command[1]+'</div>\n';
		    var new_elem = $(pagelet_html).hide().appendTo("#session-log .curentry");
		    $("#session-log .curentry .pagelet .gterm-rowimg").addClass("icons");
		    if (!gWebSocket.icons)
			$("#session-log .curentry .pagelet .gterm-rowimg").hide();
		    $("#session-log .curentry .pagelet .gterm-link").bindclick(otraceClickHandler);
		    new_elem.show();
		} else {
		    $(command[1]).appendTo("#session-log .curentry");
		}
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

		var scroll_msec = 0;
		if (scroll_msec && $("#session-log .preventry").length) {
		    var scrollY = $("#session-log .preventry").offset().top + $("#session-log .preventry").height() - 20;
		    $("html:not(:animated), body:not(:animated)").animate({scrollTop: scrollY}, scroll_msec,
                               "linear", function() {$("#session-log .curentry .input .command").focus();});
		} else {
		    // Last prompt will appear at bottom of window
		    $("#session-log .curentry .input .command").focus();
		}

            } else if (action == "terminal") {
		if (!this.terminal)
		    openTerminal();
		var cmd_type = command[1];
		var cmd_arg = command[2];
		if (cmd_type == "errmsg") {
		    alert("ERROR: "+cmd_arg[0]);
		} else if (cmd_type == "save_status") {
		    alert("File "+cmd_arg[0]+": "+(cmd_arg[1] || "saved"));
		} else if (cmd_type == "graphterm_output") {
		    var entry_class = "entry"+gPromptIndex;
		    var params = cmd_arg[0];
		    var content = cmd_arg[1];
		    if (content)
			content = $.base64.decode(content);
		    var content_type = params.headers.content_type;
		    var response_type = params.headers.x_gterm_response;
		    var response_params = params.headers.x_gterm_parameters;
		    //console.log("graphterm_output: params: ", params);
		    if (response_type == "error_message") {
			alert(content);
		    } else if (response_type == "open_terminal") {
			gWebSocket.write([["open_terminal", [response_params.term_name,
							     response_params.command]]]);
		    } else if (response_type == "display_finder") {
			ShowFinder(response_params, content);

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
			if (pagelet_display.substr(0,4) == "full") {
			    // Hide previous entries, removing previous pagelets for this entry
			    if (response_params.form_input) {
				StartFullpage(pagelet_display, false);
				GTStartForm(response_params, gPromptIndex);
			    } else {
				StartFullpage(pagelet_display, true);
			    }
			    $("#session-bufscreen").children(".pagelet."+entry_class).remove();
			    if ("scroll" in response_params && response_params.scroll != "down")
				gScrollTop = true;
			} else {
			    // New pagelet entry; show previous entries
			    EndFullpage();
			}
			var current_dir = ("current_directory" in params.headers) ? params.headers.current_directory : "";
			var pagelet_html = (content_type == "text/html") ? '<div class="pagelet '+entry_class+'" data-gtermcurrentdir="'+current_dir+'" data-gtermpromptindex="'+gPromptIndex+'">'+content+'</div>\n' : '<pre class="plaintext">'+content+'</pre>\n';

			try {
			    var new_elem = $(pagelet_html).hide().appendTo("#session-bufscreen");
			    if (response_params.form_input) {
				new_elem.find(".gterm-form-button").bindclick(GTFormCommand);
				new_elem.find(".gterm-form-label").bind("hover", GTFormHelp);
			    }
			    $("#session-bufscreen .pagelet .gterm-rowimg").addClass("icons");
			    if (!gWebSocket.icons)
				$("#session-bufscreen .pagelet .gterm-rowimg").hide();

			    $('#session-bufscreen .pagelet."'+entry_class+'" td .gterm-link').bindclick(gtermPageletClickHandler);
			    $('#session-bufscreen .pagelet."'+entry_class+'" td img').bind("dragstart", function(evt) {evt.preventDefault();});

			    GTDropBindings($('#session-bufscreen .pagelet."'+entry_class+'" .droppable'));
			    new_elem.show();
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
		    if (update_rows.length) {
			$(".cursorspan").rebind('paste', pasteHandler);
			$(".cursorspan").rebind('click', pasteReadyHandler);
		    }

		    if (update_scroll.length) {
			for (var j=0; j<update_scroll.length; j++) {
			    if ($("#session-bufscreen pre.row").length >= MAX_LINE_BUFFER)
				$("#session-bufscreen pre.row:first").remove();
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
			    var row_html = '<pre id="'+entry_id+'" class="row '+entry_class+'">'+row_escaped+"\n</pre>";
			    $(row_html).appendTo("#session-bufscreen");
			    $("#"+entry_id+" .gterm-link").bindclick(gtermLinkClickHandler);
			}
		    }

		    if (gScrollTop) {
			gScrollTop = false;
			ScrollTop(0);
		    } else if (this.theme == "default") {
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
		var content = command[2];

		GTStartEdit(editParams, content);

            } else if (action == "errmsg") {
		alert(command[1]);

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
  if (this.opened) {
  } else {
    this.failed = true;
  }
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
  this.opened = false;
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
	    var pasteStart = elem.attr("data-gtermpastestart");
	    var pasteEnd = elem.attr("data-gtermpasteend");
	    if (pasteText && pasteStart && pasteEnd) {
		var startOffset = parseInt(pasteStart); 
		var endOffset = parseInt(pasteEnd);
		if (startOffset == 0 && endOffset == 0) {
		    pasteText = pasteText.substr(0,pasteText.length-1);
		} else if (startOffset == 1 && endOffset == 1) {
		    pasteText = pasteText.substr(1);
		}
	    } else if (pasteText) {
		console.log("pasteHandler: ERROR no paste offset defined")
		pasteText = "";
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
	else if (selectedOption == "reconnect")
	    ReconnectHost();
	else if (selectedOption == "steal")
	    StealSession();
	break;

    case "icons":
	gWebSocket.icons = (selectedOption == "on");
        if (gWebSocket.icons) {
            $(".noicons").hide();
            $(".icons").show();
        } else {
            $(".noicons").show();
            $(".icons").hide();
        }
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
	alert("Help not yet implemented");
	break;
    case "collapse":
	$("#session-bufscreen .oldentry").addClass("gterm-hideoutput");
	break;
    case "expand":
	$("#session-bufscreen .oldentry").removeClass("gterm-hideoutput");
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
    case "clear":
	text = "\x01\x0B";  // Ctrl-A Ctrl-K
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

function gtermClickPaste(text, file_uri, options) {
    gWebSocket.write([["click_paste", text, file_uri, options]]);
    if (!gSplitScreen)
	SplitScreen("paste");
}

function gtermLinkClickHandler(event) {
    var contextMenu = gControlActive;
    GTReceivedUserInput("click");
    var text = $(this).text();
    var file_uri = "";
    var options = {}

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
	gtermClickPaste(text, file_uri, options);
    } if ($(this).hasClass("gterm-cmd-path")) {
	file_uri = makeFileURI($(this).attr("href"));
	gtermClickPaste("", file_uri, options);
    }
    if (contextMenu) {
	alert("Context menu not yet implemented");
	return false;
    }

    console.log("gtermLinkClickHandler", file_uri, options);
    return false;
}

function gtermPageletClickHandler(event) {
    var contextMenu = gControlActive;
    GTReceivedUserInput("click");
    var text = $(this).text();
    var pagelet = $(this).closest(".pagelet");
    var file_uri = makeFileURI($(this).attr("href"));

    if (contextMenu) {
	alert("Context menu not yet implemented");
	return false;
    }

    var options = {enter: true}
    options.command = $(this).attr("data-gtermcmd");
    var cd_command = (options.command.indexOf("cd ") == 0);
    options.clear_last = (pagelet.length && cd_command) ? pagelet.attr("data-gtermpromptindex") : "0";
    gtermClickPaste("", file_uri, options);
    if (cd_command)
	GTCurDirURI = file_uri;
    //console.log("gtermPageletClickHandler", file_uri, options);
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
	else if (selectedOption == "tab")
	    text = String.fromCharCode(9);
	else if (selectedOption == "escape")
	    text = String.fromCharCode(27);
	else if (selectedOption == "controlc")
	    text = String.fromCharCode(3);
	else if (selectedOption == "controld")
	    text = String.fromCharCode(4);
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
    var file_uri = makeFileURI($(this).attr("href"));

    if (contextMenu) {
	alert("Context menu not yet implemented");
	return false;
    }

    var options = {clear_last: 0};
    options.command = $(this).attr("data-gtermcmd");
    console.log("gtermFinderClickHandler", text, file_uri, options);
    gtermClickPaste("", file_uri, options);
    HideFinder();
    return false;
}

function otraceClickHandler(event) {
    var prev_command = $("#session-log .preventry").length ? GTStrip($("#session-log .preventry .input .command").text()) : "";
    var cur_command = GTStrip(GTGetCurCommandText());
    var file_uri = makeFileURI($(this).attr("data-gtermuri") || $(this).attr("href"));
    var filepath = GTGetFilePath(file_uri, GTCurDirURI);

    console.log("otraceClickHandler", GTCurDirURI);
    if (cur_command.length) {
	GTSetCommandText(cur_command + " " + filepath);
	GTSetCursor(gCommandId);
	$("#session-log .curentry .input .command").focus();
	GTExpandCurEntry(false);
    } else {
	var new_command = $(this).attr("data-gtermcmd");
	var command_line = (new_command == "cdls") ? new_command+" "+filepath : new_command.replace("%(path)", filepath);

	if ((new_command == "cdls" || new_command.indexOf("cdls ") == 0) &&
	    (prev_command == "cdls" || prev_command.indexOf("cdls ") == 0)) {
	    // Successive open commands; consolidate by preparing to overwrite previous entry
	    var saved_uri = $("#session-log .preventry .prompt").attr("data-gtermsaveduri");
	    if (!saved_uri) {
		saved_uri = $("#session-log .preventry .prompt").attr("data-gtermuri");
	        $("#session-log .preventry .prompt").attr("data-gtermsaveduri", saved_uri);
	    }
	    var alt_filepath = GTGetFilePath(file_uri, saved_uri);
	    var alt_command_line = new_command+" "+alt_filepath;
	    $("#session-log .curentry .prompt").attr("data-gtermsaveduri", saved_uri);
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

    if (gEditing || gForm)
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
	else if (gWebSocket)
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

    if (gEditing || gForm)
	return true;

    if (evt.which == 13) {
	// Enter key
	var text = GTStrip(GTGetCurCommandText());  // Unescaped text
	gWebSocket.write([["input", text, null]]);
	return false;
    }

    return true;
}

function HandleArrowKeys(keyCode) {
    //console.log("HandleArrowKeys", keyCode, gCursorAtEOL);
    if (!gCursorAtEOL || gWebSocket.alt_mode)
	return true;
    // Cursor at end of command line
    if (keyCode == 38 || keyCode == 40) {
	// Up/down arrows; command history recall
	return GTHandleHistory((keyCode == 38));

    } else if (keyCode == 39) {
	// Right arrow; command history completion
	if ($("#gterm-pre0 .cmd-completion").length) {
	    var comptext = $("#gterm-pre0 .cmd-completion").text();
	    $("#gterm-pre0 .cmd-completion").text("");
	    if (comptext) {
		gWebSocket.term_input(String.fromCharCode(5)+comptext);
		return false;
	    }
	}
    }
    // Default handling
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

    var formSubmitter = ".pagelet.entry"+gPromptIndex+" .gterm-form-command";
    if (kc == 13 && gForm && $(formSubmitter).length == 1) {
	$(formSubmitter).click();
	return false;
    }

    if (!evt.ctrlKey && !gControlActive && (gEditing || gForm)) {
	// Not Ctrl character; editing/processing form
	return true;
    }

    if (evt.altKey) {
	if (kc>=65 && kc<=90)
	    kc+=32;
	if (kc>=97 && kc<=122) {
	    k=String.fromCharCode(27)+String.fromCharCode(kc);
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
	console.log("graphterm.AjaxKeypress2", kc, k, k.charCodeAt(0));

    if (gForm && k == String.fromCharCode(3)) {
	// Ctrl-C exit from form
	GTEndForm("", true);
    } else if (gEditing || gForm) {
	// Editing or processing form
	return true;
    }

    if (k.length) {
	if (k.charCodeAt(k.length-1) == 13) {
	    // Enter key
	    if (gShowingFinder)
		HideFinder();
	    if (gCommandMatchPrev)
		HandleArrowKeys(39); // Simulate right arrow for command completion
	}
	gWebSocket.term_input(k, true);
    }
    evt.cancelBubble = true;
    return GTPreventHandler(evt);
}

function OpenNew(term_name, options) {
    var tty = term_name || "";
    var new_url = window.location.protocol+"/"+"/"+window.location.host+"/"+gParams.host+"/"+tty; // Split the double slash to avoid confusing the JS minifier
    console.log("open", new_url);
    window.open(new_url, target="_blank");
}

function GTermAbout() {
    alert("GraphTerm: A Graphical Terminal Interface\n\nVersion: "+gParams.version+"\n\nhttp://info.mindmeldr.com/code/graphterm");
}

function CheckUpdates() {
    $.getJSON(PYPI_JSON_URL, function(data) {
	if (gParams.version == data.info.version) {
	    alert("GraphTerm is up-to-date (version: "+gParams.version+").");
	} else {
	    alert("New version "+data.info.version+" is available.\nUse 'easy_install --upgrade graphterm'\n or download from from "+PYPI_URL);
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
var gPopupType = "";
var gPopupParams = null;
var gPopupConfirmClose = null;

function popupSetup() {
  // Initialize bindings for popup handling
  $(".gterm-popup").hide();
  $(".gterm-popupmask").hide();
  $(".gterm-popupmask, .gterm-popupclose").click(popupClose);
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
  gPopupType = "";
  gPopupParams = null;
  gPopupConfirmClose = null;
}

function popupShow(elementId, popupType, popupParams, popupConfirmClose) {
  // Display elementId as modal popup window
  var maskId = elementId + "_mask";

  gPopupType = popupType || "";
  gPopupParams = popupParams || null;
  gPopupConfirmClose = popupConfirmClose || null;

  var animateMs = 0;

  // Get screen height/width
  var maxWidth = 1600;
  var minWidth = 100;

  var winWidth = $(window).width();
  var winHeight = $(window).height();
  var docHeight = $(document).height();

  // Fade in mask
  ScrollTop(0);
  $(maskId).css({width: winWidth, height: docHeight});

  //$(maskId).fadeIn(1000);
  $(maskId).fadeTo(0.6*animateMs, 0.7);

  // Position popup window
  //$(elementId).css("top", winHeight/2 - $(elementId).outerHeight()/2);
  $(elementId).css("top", 0);
  $(elementId).css("left", (winWidth/2) - ($(elementId).outerWidth()/2));

  // Fade in popup
  $(elementId).fadeIn(1.0*animateMs);

  $(elementId).find("textarea").focus();
  $(elementId).find("input:text").focus();
}

function GTStartEdit(params, content) {
    $("#terminal").hide();
    gEditing = {params: params, content: content};
    if (gEditing.params.editor == "web") {
	$("#pop_editarea_content").val(content);
	popupShow("#pop_editarea", "editarea");
    } else {
	if ($("#acearea_content").length)
	    $("#acearea_content").remove();
	$('<div name="acearea_content" id="acearea_content">/div>').appendTo("#acearea");
	$("#acearea").show();
	gEditing.ace = ace.edit("acearea_content");
	try {
	    if (params.filetype)
		gEditing.ace.getSession().setMode("ace/mode/"+params.filetype);
	} catch(err) {
	    console.log("ERROR in mode:", params.filetype, err);
	}
	gEditing.ace.getSession().setValue(content);
    }
}

function GTEndEdit(save) {
    var newContent;
    if (gEditing.params.editor == "web") {
	newContent = $("#pop_editarea_content").val();
    } else {
	newContent = gEditing.ace.getSession().getValue();
    }
    if (gEditing.params.modify && newContent != gEditing.content) {
	if (save) {
	    if (gEditing.params.command) {
		gWebSocket.write([["input", gEditing.params.command, newContent]]);
	    } else {
		gWebSocket.write([["save_file", gEditing.params.filepath, newContent]]);
	    }
	} else if (!window.confirm("Discard changes?")) {
	    return false;
	}
    }
    if (gEditing.params.editor == "web") {
	popupClose(false);
    } else {
	$("#acearea").hide();
	$("#acearea_content").remove();
    }
    gEditing = null;
    $("#terminal").show();
    ScrollScreen();
    return false;
}

function GTStartForm(params, promptIndex) {
    gForm = params || {};
    gFormIndex = promptIndex || 0;
    $("#session-screen").hide();
}

function GTEndForm(text, cancel) {
    text = text || "";
    console.log("GTEndForm: ", text, cancel);
    $("#session-screen").show();
    if (cancel) {
	$("#session-bufscreen").children(".pagelet.entry"+gFormIndex).remove();
    } else {
	gWebSocket.write([["clear_last_entry", gFormIndex+""]]);
	gWebSocket.term_input(text+"\n");
    }
    gForm = null;
    gFormIndex = null;
}

function GTFormSubmit(text, cancel) {
    GTEndForm(text, cancel);
}

function GTFormHelp(evt) {
    var helpStr = $(this).attr("data-gtermhelp");
}

function GTFormCommand(evt) {
    if ($(this).hasClass("gterm-form-cancel"))
	GTEndForm("", true);

    var formElem = $(this).closest(".gterm-form");
    var argNames = $(this).attr("data-gtermformargs").split(",");
    var command = $(this).attr("data-gtermformcmd");
    var argStr = "";
    for (var j=0; j<argNames.length; j++) {
	var argName = argNames[j];
	var inputElem = formElem.find("[name="+argName+"]");
        var inputValue = inputElem.serializeArray()[0]["value"];
	if (inputValue.indexOf(" ") > -1)
	    inputValue = '"' + inputValue + '"';
        if (inputValue) {
	    if (argName.substr(0,3) == "arg") {
		// Command line arguments
		argStr += ' ' + inputValue; 
	    } else {
		// Command options
		command += ' --' + argName + '=' + inputValue;
	    }
	}
    }
    command += argStr;
    console.log("GTFormCommand", this, formElem, command, evt);
    GTEndForm(command);
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
    $("#session-bufscreen").addClass("fullpage");
    if (split) {
	$("#session-bufellipsis").show();
	if (gAlwaysSplitScreen && !gSplitScreen)
	    SplitScreen("fullpage");
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
}

function ExitFullpage() {
    EndFullpage();
    var offset = $(document).height() - $(window).height();
    if (offset > 0)
 	ScrollTop(offset);
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
    $("#session-finderbody .gterm-rowimg").addClass("icons");
    if (!gWebSocket.icons)
	$("#session-finderbody .gterm-rowimg").hide();
    
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
	    var gterm_uri = makeFileURI($(this).attr("href") || "");
	    if (evt.originalEvent.dataTransfer.files.length) {
	    } else {
		var text = evt.originalEvent.dataTransfer.getData("text/plain") || "";
		var file_uri = "";
		if (text) {
		    var srcText = makeFileURI(text);
		    var srcComps = splitFileURI(srcText);
		    if (srcComps.length) {
			file_uri = srcText;
			text = srcComps[1];
			var options = {};
			var dstComps = splitFileURI(gterm_uri);
			if (gterm_mime == "x-graphterm/directory") {
			    options.command = (srcComps[0] == dstComps[0]) ? "mv" : "gcp";
			    options.dest_uri = gterm_uri;
			    options.enter = true;
			    gtermClickPaste("", file_uri, options);
			} else if (gterm_mime == "x-graphterm/executable") {
			    options.command = dstComps[2];
			    gtermClickPaste("", file_uri, options);
			} else {
			    gtermClickPaste(text, file_uri, options);
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
	}, 1000, function() { $("#gtermsplash").hide(); });
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

$(document).ready(function() {
    //LoadHandler();
    console.log("Ready");
    $(document).attr("title", window.location.pathname.substr(1));

    if (gSafariIPad)
	$("body").addClass("ipadscreen");

    setupTerminal();
    $("#acearea").hide();
    $("#session-bufellipsis").hide();
    $("#session-findercontainer").hide();
    $(".menubar-select").change(gtermSelectHandler);
    $(".session-footermenu select").change(gtermBottomSelectHandler);
    $("#session-headermenu .headfoot").bindclick(gtermMenuClickHandler);
    $("#session-footermenu .headfoot").bindclick(gtermMenuClickHandler);

    //window.addEventListener("dragover", GTDragOver);
    window.addEventListener("drop", GTDropHandler);

    $(".gterm-popup").hide();
    $(".gterm-popupmask").hide();
    $(".gterm-popupmask, .gterm-popupclose").click(popupClose);

    if (gMobileBrowser)
	GTHideSplash();

    $(GTNextEntry()).appendTo("#session-log");

    $(window).scroll(ScrollEventHandler);


    // Bind window keydown/keypress events
    $(document).keydown(keydownHandler);
    $(document).keypress(keypressHandler);

    $(window).resize(handle_resize);

    Connect();
});
