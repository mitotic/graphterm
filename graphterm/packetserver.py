#!/usr/bin/env python
#

"""
Packet server: for flash etc.
"""

import hashlib
import time

import errno
import functools
import hmac
import hashlib
import logging
import socket
import ssl
import struct
import thread
import traceback
import uuid

try:
    import ujson as json
except ImportError:
    try:
        import json
    except ImportError:
        import simplejson as json

from tornado import ioloop
from tornado import iostream
from tornado import escape

SIGN_SEP = "|"
SIGN_HEXDIGITS = 24
SIGN_HASH = hashlib.sha256

FLASH_POLICY_PORT = 843
FLASH_SOCKET_PORT = 8843

FRAMELEN_FORMAT = "!L"    # Format for frame length prefix
FLASH_DELIMITER = "\0"

POLICY_FILE_REQUEST = "<policy-file-request/>"
MASTER_POLICY_XML_FORMAT = """<cross-domain-policy>
  <site-control permitted-cross-domain-policies="master-only"/>
  <allow-access-from domain="%s" to-ports="%s" />
</cross-domain-policy>
"""
SOCKET_POLICY_XML_FORMAT = """<cross-domain-policy>
  <allow-access-from domain="%s" to-ports="%s" />
</cross-domain-policy>
"""

def dict2kwargs(dct, unicode2str=False):
    """Converts unicode keys in a dict to ascii, to allow it to be used for keyword args.
    If unicode2str, all unicode values to converted to str as well.
    (This is needed when the dict is created from JSON)
    """
    return dict([(str(k), str(v) if unicode2str and isinstance(v, unicode) else v) for k, v in dct.iteritems()])

class UserMessage(Exception):
    """ Exception for sending error messages to client
    """
    pass

class SystemMessage(Exception):
    """ Exception for sending error messages to system administrator
    """
    pass

class PacketConnector(object):
    """ Serves Flash policy and other requests, delimited by "\0" or framed
    by a frame length prefix (typically using "!L" unsigned 32-bit format)
    Override process request method.
    If max_packet_buf > 0, derived class must explicitly call resend_buffered_packets
    and clear_sent_packets as needed. Can also use self.packet_id to identify packets.
    If max_packet_buf < 0, connection is shutdown if buffer is full.
    To ensure unique connection for each connection_id, call new_connection as soon as
    a new connection is created. (Any previous connection with the same id is closed).
    """
    _all_connections = None   # Must be re-defined to {} in final derived class
    def __init__(self, client=False, server_type="", delimiter=None,
                 framelen_format=None, single_request=False, ssl_options={}, max_packet_buf=0):
        if not delimiter and not framelen_format:
            if server_type == "flash":
                delimiter = FLASH_DELIMITER
            elif server_type == "frame":
                framelen_format = FRAMELEN_FORMAT
            else:
                raise Exception("Must specify delimiter or framelen_format")
        elif delimiter and framelen_format:
                raise Exception("Must specify only one of delimiter or framelen_format")

        self.client = client
        self.server_type = server_type
        self.delimiter = delimiter
        self.framelen_format = framelen_format
        self.fmt_size = struct.calcsize(framelen_format) if framelen_format else 0
        self.single_request = single_request
        self.ssl_options = ssl_options

        self.expect_len = 0
        self.closed = False
        self.stream = None

        self.max_packet_buf = max_packet_buf
        self.packet_id = 1           # ID of next packet to be sent (wraps around)
        self.packet_buf = []
        self.connection_id = ""      # Usually set first on client and then sent to server
        self.last_active_time = 0    # Time when data was last received or sent

    def new_connection(self, connection_id):
        if self._all_connections is None:
            raise Exception("Must define class attribute %s._all_connections = {}" % self.__class__.__name__)
        if self.connection_id:
            if self.connection_id == connection_id:
                return
            raise Exception("Connection id mismatch: old %s != new %s" % (self.connection_id, connection_id))

        self.connection_id = connection_id
        if connection_id:
            old_connection = self._all_connections.get(connection_id)
            self._all_connections[connection_id] = self
            if old_connection:
                # Shutdown any previous connection for this ID
                old_connection.shutdown()

    def shutdown(self):
        # Does not self.close (done by derived class)
        if self.connection_id:
            if self._all_connections.get(self.connection_id) is self:
                del self._all_connections[self.connection_id]
            self.connection_id = ""

    def on_close(self):
        raise Exception("NOT IMPLEMENTED")

    @classmethod
    def shutdown_all(cls):
        while cls._all_connections:
            conn_id, conn = cls._all_connections.popitem()
            conn.shutdown()

    @classmethod
    def get_connection(cls, connection_id):
        return cls._all_connections.get(connection_id)

    @classmethod
    def get_connection_ids(cls):
        return cls._all_connections.keys()

    def process_packet(self, message):
        """ Processes packet; raises exception on error, leading to connection being closed.
        If single_request, will be called with None value if server closes connection.
        Otherwise, message is always non-None.
        OVERRIDE
        """
        raise SystemMessage("NOT IMPLEMENTED")

    def receive_header(self, data=None):
        """ Receives frame length header
        """
        if not self.stream or not data or len(data) != self.fmt_size:
            self.on_close()
            return
        self.expect_len = struct.unpack(self.framelen_format, data)[0]
        self.stream.read_bytes(self.expect_len, self.receive_packet)

    def receive_packet(self, data=None, start=False):
        """ Receives stream request, processes it, and waits for next one
        """
        if not data and not start:
            self.on_close()
            return

        self.last_active_time = time.time()
        if data:
            if self.delimiter:
                # Strip out delimiter
                data = data[:-len(self.delimiter)]
            elif len(data) != self.expect_len:
                # Incomplete frame; close
                self.on_close()
                return

            try:
                self.process_packet(data)
            except Exception, excp:
                logging.warning("PacketConnector: Error in processing packet: %s", excp, exc_info=True)
                self.on_close()
                return

        if not self.stream:
            self.on_close()
            return

        if not start and self.single_request:
            if self.client:
                # Processed response to single request
                self.shutdown()
            # If server, it will be shutdown after response is sent
        else:
            # Process first (or next packet)
            if self.fmt_size:
                self.stream.read_bytes(self.fmt_size, self.receive_header)
            else:
                self.stream.read_until(self.delimiter, self.receive_packet)

    def send_json(self, obj, finish=False, buffer=False, nobuffer=False):
        if not self.closed:
            try:
                json_obj = json.dumps(obj)
                self.send_packet(json_obj, finish=finish, utf8=True, buffer=buffer, nobuffer=nobuffer)
            except Exception, excp:
                logging.warning("PacketConnector.send_json: ERROR: %s", excp)
                raise

    def make_packet(self, data, utf8=False):
        if utf8:
            data = escape.utf8(data)

        if self.framelen_format:
            packet = struct.pack(self.framelen_format, len(data)) + data
        else:
            if self.delimiter in data:
                raise Exception("Delimiter not allowed in message")
            packet = data + self.delimiter
        return packet

    def clear_sent_packets(self, packet_id):
        while self.packet_buf and self.packet_buf[0][0] <= packet_id:
            self.packet_buf.pop(0)

    def resend_buffered_packets(self):
        for packet_id, data, finish, utf8 in self.packet_buf:
            self.send_packet(data, finish=finish, utf8=utf8, nobuffer=True)

    def is_connected(self):
        return self.connected

    def is_writable(self):
        return self.connected or len(self.packet_buf) < abs(self.max_packet_buf)

    def send_packet(self, data, finish=False, utf8=False, buffer=False, nobuffer=False):
        """
        If buffer, packet is not actually sent, just buffered.
        If nobuffer, self.packet_id is not incremented.
        """
        if self.closed:
            return

        if thread.get_ident() != ioloop.IOLoop.instance()._thread_ident:
            raise Exception("PacketConnector.send_packet invoked from non-ioloop thread")
            
        self.last_active_time = time.time()
        if not nobuffer:
            if self.max_packet_buf:
                while len(self.packet_buf) >= abs(self.max_packet_buf):
                    if self.max_packet_buf < 0:
                        # Buffer overflow; close
                        self.on_close()
                        return
                    self.packet_buf.pop(0)
                self.packet_buf.append( (self.packet_id, data, finish, utf8) )
            self.packet_id = (self.packet_id + 1) % 0x40000000

        if finish or self.single_request:
            callback = self.shutdown
        else:
            callback = None

        if self.stream and not buffer:
            try:
                self.stream.write(self.make_packet(data, utf8=utf8), callback)
            except Exception, excp:
                logging.warning("PacketConnector.send_packet: ERROR: %s", excp)
                self.on_close()

class PacketClient(PacketConnector):
    """ Sends one or more packets to server and handles response packets.
    If single_request, send a single request and wait for a single response,
    otherwise, call connect to initiate connection.
    If reconnect_sec, keep reconnecting (after waiting reconnect_sec) until explicit shutdown.
    If reconnect_timeout, stop trying to reconnect after reconnect_timeout secs.
    """
    def __init__(self, host, port, io_loop=None, noresponse=False, server_type="",
                 delimiter=None, framelen_format=None, single_request=False,
                 ssl_options={}, max_packet_buf=0, reconnect_sec=0, reconnect_timeout=0):
        super(PacketClient, self).__init__(client=True, server_type=server_type,
                                 delimiter=delimiter,
                                 framelen_format=framelen_format,
                                 ssl_options=ssl_options,
                                 max_packet_buf=max_packet_buf,
                                 single_request=single_request)
        self.host = host
        self.port = port
        if not io_loop:
            io_loop = ioloop.IOLoop.instance()
        self.io_loop = io_loop
        self.noresponse = noresponse
        self.reconnect_sec = reconnect_sec
        self.reconnect_timeout = reconnect_timeout

        self.request_packet = None
        self.timeout_cb = None
        self.reconnect_cb = None
        self.reconnect_time = 0            # Time when reconnection was initiated
        self.connected = False             # True if connection is currently active
        self.client_opened = False         # True after first succesful connect

    def reset(self):
        if self.timeout_cb:
            try:
                self.io_loop.remove_timeout(self.timeout_cb)
            except Exception, excp:
                pass
            self.timeout_cb = None
        self.connected = False
        self.request_packet = None

    @classmethod
    def get_client(cls, connection_id, connect=(), connect_kw={}):
        """ Return client connection for connection id.
        If connect = (host, port), a connection is initiated, if not found.
        """
        conn = super(PacketClient, cls).get_connection(connection_id)
        if not conn and connect:
            # Create new connection to server and connect
            conn = cls(*connect, **connect_kw)
            conn.new_connection(connection_id)
            conn.connect()
        return conn

    def connect(self, timeout=30):
        self.clear_reconnect()
        if self.closed:
            return
        self.reset()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        if self.ssl_options:
            self.stream = iostream.SSLIOStream(sock, io_loop=self.io_loop, ssl_options=self.ssl_options)
        else:
            self.stream = iostream.IOStream(sock, io_loop=self.io_loop)
        self.stream.set_close_callback(self.on_close)
        if timeout > 0:
            self.timeout_cb = self.io_loop.add_timeout(time.time()+timeout, self.connect_timeout)
        self.stream.connect((self.host, self.port), self.on_connect)

    def on_connect(self):
        if self.closed:
            return
        self.reset()
        self.connected = True
        self.client_opened = True
        self.reconnect_time = 0              # Reconnect succeeded
        self.handle_connect()

        if self.single_request:
            assert self.request_packet
            self.stream.write(self.request_packet, callback=self.single_request_sent)
            self.request_packet = None
        else:
            self.receive_packet(start=True)

    def connect_timeout(self):
       self.timeout_cb = None
       if self.connected or self.closed:
           return
       if self.reconnect_sec > 0:
           self.on_close()
       else:
           self.shutdown()

    def reconnect_callback(self):
        self.reconnect_cb = None
        if self.connected or self.closed:
            return
        self.connect()

    def handle_connect(self):
        """ Called after connecting (or reconnecting) to server
        Override
        """
        pass

    def clear_reconnect(self):
        if not self.reconnect_cb:
            return
        try:
            self.io_loop.remove_timeout(self.reconnect_cb)
        except Exception, excp:
            pass
        self.reconnect_cb = None

    def shutdown(self):
        if self.closed:
            return
        self.closed = True

        self.clear_reconnect()
        self.shutdown_aux()

        if not self.noresponse and self.single_request and self.request_packet:
            # Simulate None response if single request has been sent
            self.request_packet = None
            try:
                self.process_packet(None)
            except Exception:
                pass

        super(PacketClient, self).shutdown()
        self.handle_shutdown()

    def shutdown_aux(self):
        self.reset()
        if self.stream:
            try:
                self.stream.close()
            except Exception:
                pass
        self.stream = None

    def handle_shutdown(self):
        """ Called when connection is shutdown (useful when reconnecting is enabled)
        Override
        """
        pass

    def on_close(self):
        if self.closed:
            return
        self.handle_close()
        cur_time = time.time()
        if self.reconnect_sec <= 0 or (
            self.reconnect_timeout and self.reconnect_time and (cur_time - self.reconnect_time) > self.reconnect_timeout) or (self._all_connections.get(self.connection_id) is not self):
            # No reconnect or reconnect timed out or old connection
            self.shutdown()
        else:
            # Reconnect
            self.shutdown_aux()
            if not self.reconnect_cb:
                if not self.reconnect_time:
                    self.reconnect_time = cur_time
                self.reconnect_cb = self.io_loop.add_timeout(cur_time+self.reconnect_sec, self.reconnect_callback)

    def handle_close(self):
        """ Called when server closes connection (multiple calls, if reconnecting is enabled)
        Override
        """
        pass

    def send_single_request(self, message, utf8=False):
        assert self.single_request
        self.request_packet = self.make_packet(message, utf8=utf8)
        self.connect()

    def single_request_sent(self):
        if self.noresponse:
            self.shutdown()
            return
        self.receive_packet(start=True)


class PacketConnection(PacketConnector):
    """ Serves Flash policy and other requests, delimited by "\0" or framed
    by a frame length prefix (typically using "!L" unsigned 32-bit format)
    Override process request method.
    """
    def __init__(self, stream, address, server_address, server_type="",
                 delimiter=None, framelen_format=None, ssl_options={},
                 max_packet_buf=0, single_request=False):
        super(PacketConnection, self).__init__(client=False, server_type=server_type,
                                 delimiter=delimiter,
                                 framelen_format=framelen_format,
                                 ssl_options=ssl_options,
                                 max_packet_buf=max_packet_buf,
                                 single_request=single_request)

        self.server_address = server_address
        self.address = address
        self.source ="%s:%s" % address
        if server_type:
            self.source = server_type + ":" + self.source
            
        self.connected = True         # Server-side socket is connected from start
        self.stream = stream
        self.stream.set_close_callback(self.on_close)

    def shutdown(self):
        self.on_close()
        try:
            self.stream.close()
        except Exception:
            pass
        self.stream = None
        super(PacketConnection, self).shutdown()

    def on_close(self):
        if self.closed:
            return
        self.closed = True
        self.handle_close()
        self.shutdown()

    def handle_close(self):
        """ Called when connection is closed
        Override
        """
        pass

    def map_name_to_host(self, message):
        """ Maps group name to host:port, returning id@host:port/path, where path may be a null string
        """
        raise SystemMessage("NOT IMPLEMENTED")

    @classmethod
    def connection_ready(cls, server_address, io_loop, sock, fd, events, **kwargs):
        ssl_options = kwargs.get("ssl_options", {})
        while True:
            try:
                connection, address = sock.accept()
            except socket.error, e:
                if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                    raise
                return
            connection.setblocking(0)
            logging.debug("Policy connection: %s", address)
            if ssl_options:
                stream_class = iostream.SSLIOStream
            else:
                stream_class = iostream.IOStream
            stream = stream_class(connection, io_loop=io_loop)
            handler = cls(stream, address, server_address, **kwargs)
            handler.receive_packet(start=True)

    @classmethod
    def start_tcp_server(cls, host, port, io_loop=None, **kwargs):
        """ Listens for TCP requests.
        If io_loop is not specified, a new io_loop is created and started (blocking)
        Returns socket
        """
        ssl_options = kwargs.get("ssl_options", {})
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)
        server_address = (host, port)
        sock.bind(server_address)
        if ssl_options:
            sock = ssl.wrap_socket(sock, server_side=True, **ssl_options)
        sock.listen(128)

        start_loop = False
        if not io_loop:
            start_loop = True
            io_loop = ioloop.IOLoop.instance()

        callback = functools.partial(cls.connection_ready, server_address, io_loop, sock, **kwargs)
        io_loop.add_handler(sock.fileno(), callback, io_loop.READ)

        logging.warning("%s: listening on %s:%d", cls.__name__, host, port)
        if start_loop:
            io_loop.start()

        return sock

    @classmethod
    def stop_tcp_server(cls, sock, io_loop=None):
        if io_loop:
            io_loop.remove_handler(sock.fileno())
        sock.close()

class RPCLink(object):
    """ Implements Remote Procedure Calls, using messages of the form
        [0, ["setup",    ["connection_id", key_version, nonce, server_token or None] ] for setup
        [0, ["validate", [server/client_rpc_token, last_received_id], {state}] ] for validation
        [0, ["shutdown", [err_message] ]
        [n, ["method", [args], {kwargs}]
        [-n, retval], where -n acknowledges packet n, and non-null retval implies error message.
        Mixin *before* PacketConnection/PacketClient, and implement derived methods of the form
        remote_<method>(self, args, kwargs)
    """
    rpc_key_secret = None         # Set for server/client
    rpc_key_version = None        # Set for server/client
    def __init__(self, *args, **kwargs):
        """ Arguments:
        connection_id (str) required for clients.
        key_secret (str) optional
        key_version (int) optional
              
        """
        self.connection_id = kwargs.pop("connection_id", "")
        if "key_secret" in kwargs:
            self.rpc_key_secret = kwargs.pop("key_secret") 
        if "key_version" in kwargs:
            self.rpc_key_version = kwargs.pop("key_version")
        self.rpc_expect = "connect"

        self.rpc_ready = False
        self.rpc_nonce = None
        self.rpc_unvalidated_id = None
        self.rpc_client_token = None
        self.rpc_state = {}   # (Optional) Initial state variable for connection
        self.rpc_peer_state = {}     # Initial state variable for peer
        self.received_id = 0         # Last received packet ID
        super(RPCLink, self).__init__(*args, **kwargs)

    def set_rpc_state(self, value={}):
        self.rpc_state = value

    def on_connect(self):
        super(RPCLink, self).on_connect()
        if not self.connection_id:
            self.shutdown()
            raise Exception("Must specify connection_id for RPC connection setup")
        self.rpc_nonce = uuid.uuid4().hex
        self.rpc_expect = "connect"
        self.send_json([0, ["connect", [self.connection_id, self.rpc_key_version, self.rpc_nonce, None]] ],
                           nobuffer=True)

    def rpc_connect(self, connection_id, key_version, nonce, token):
        self.rpc_expect = "validate"
        if self.client:
            client_token, server_token = self.sign_token(self.connection_id, self.rpc_nonce, nonce)
            if token != server_token:
                self.send_json([0, ["shutdown", ["Invalid server token"]] ], nobuffer=True)
                self.shutdown()
                logging.warning("RPCLink.rpc_connect: Invalid server token")
                return
            self.rpc_client_token = client_token
            self.send_json([0, ["validate", [self.rpc_client_token, self.received_id], self.rpc_state]], nobuffer=True)
        else:
            # Server
            self.rpc_nonce = uuid.uuid4().hex
            if key_version != self.rpc_key_version:
                self.send_json([0, ["shutdown", ["Invalid key version: %s" % key_version]] ],
                               nobuffer=True)
                self.shutdown()
                logging.warning("RPCLink.rpc_connect: Invalid key version: %s", key_version)
                return

            self.rpc_unvalidated_id = connection_id
            client_token, server_token = self.sign_token(connection_id, nonce, self.rpc_nonce)
            self.rpc_client_token = client_token
            self.send_json([0, ["connect", [None, None, self.rpc_nonce, server_token]] ],
                           nobuffer=True)
        
    def rpc_server_validate(self, token):
        if token != self.rpc_client_token:
            self.send_json([0, ["shutdown", ["Invalid client token"]] ], nobuffer=True)
            self.shutdown()
            logging.warning("RPCLink.rpc_server_validate: Invalid client token")
            return False
        self.new_connection(self.rpc_unvalidated_id)
        self.send_json([0, ["validate", [None, self.received_id], self.rpc_state]], nobuffer=True)
        return True

    def sign_token(self, connection_id, client_nonce, server_nonce):
        """ Returns client_token, server_token
        For servers with non-None key_version, key_secret is treated as a master key,
        and the string key_version+SIGN_SEP+connection_id is "signed" with the master
        to generate the actual signing key.
        """
        key_secret = self.rpc_key_secret
        if self.client or self.rpc_key_version is None:
            key_secret = self.rpc_key_secret
        else:
            key_secret = hmac.new(str(self.rpc_key_secret), str(self.rpc_key_version)+SIGN_SEP+connection_id, digestmod=SIGN_HASH).hexdigest()[:SIGN_HEXDIGITS]

        prefix = SIGN_SEP.join([connection_id, client_nonce, server_nonce]) + SIGN_SEP
        return [hmac.new(str(key_secret), prefix+conn_type, digestmod=SIGN_HASH).hexdigest()[:SIGN_HEXDIGITS] for conn_type in ("client", "server")]

    def send_request_threadsafe(self, method, *args, **kwargs):
        ioloop.IOLoop.instance().add_callback(functools.partial(self.send_request, method, *args, **kwargs))

    def send_request(self, method, *args, **kwargs):
        self.send_json([self.packet_id, [method, args, kwargs]], buffer=(not self.rpc_ready))

    @classmethod
    def send_to_connection(cls, connection_id, method, *args, **kwargs):
       """ Sends RPC to connection_id, or raises exception if not connected.
       """
       conn = cls.get_connection(connection_id)
       if not conn or not conn.is_writable():
           raise Exception("Unable to write to %s" % connection_id)
       conn.send_request(method, *args, **kwargs)

    @classmethod
    def shutdown_connection(cls, connection_id):
        conn = cls.get_connection(connection_id)
        if conn:
            conn.shutdown()

    def process_packet(self, data):
        try:
            packet_id, msg_obj = json.loads(data)
            if (packet_id and self.rpc_expect) or (not packet_id and msg_obj[0] != self.rpc_expect and msg_obj[0] != "shutdown"):
                # Drop packet
                logging.info("RPCLink.process_packet: Dropped packet %s", msg_obj[0])
                return
                    
            if not packet_id:
                if msg_obj[0] == "shutdown":
                    self.shutdown()
                    logging.info("RPCLink.process_packet: shutdown: %s", msg_obj[1][0])
                elif msg_obj[0] == "connect":
                    connection_id, key_version, nonce, token = msg_obj[1]
                    self.rpc_connect(connection_id, key_version, nonce, token)
                elif msg_obj[0] == "validate":
                    token, last_received_id = msg_obj[1]
                    if not self.client:
                        # Note: client-side validation already completed
                        if not self.rpc_server_validate(token):
                            return
                    self.rpc_peer_state = msg_obj[2]
                    self.clear_sent_packets(last_received_id)
                    self.resend_buffered_packets()
                    self.rpc_expect = ""
                    self.rpc_ready = True
                return
        except Exception, excp:
            logging.warning("RPCLink.process_packet: Error in RPC message processing: %s", excp)
            if not self.connection_id:
                self.shutdown()
            return

        if packet_id < 0:
            # Ack for outbound message; pop out ack'ed and older packets in buffer
            if msg_obj:
                logging.debug("Return value: %s: %s", self.connection_id, msg_obj)
            self.clear_sent_packets(-packet_id)
        elif not self.connection_id:
            self.shutdown()
            raise packetserver.SystemMessage("Expected setup packet")
        else:
            # New inbound message of the form [method, args_array, kwargs_dict]
            retval = None
            try:
                args = msg_obj[1] if len(msg_obj) > 1 else []
                kwargs = dict2kwargs(msg_obj[2]) if len(msg_obj) > 2 else {}
                bound_method = getattr(self, "remote_"+msg_obj[0], None)
                if bound_method:
                    retval = bound_method(*args, **kwargs)
                else:
                    retval = self.invoke_method(msg_obj[0], *args, **kwargs)
            except Exception, excp:
                retval = "Error: %s: %s\n%s" % (msg_obj[0], excp, "".join(traceback.format_exc()))
                logging.warning("RPCLink.process_packet: %s: %s", self.connection_id, retval)

            if packet_id > 0:
                # Acknowledge message
                self.received_id = packet_id
                try:
                    self.send_json([-packet_id, retval])
                except Exception, excp:
                    pass

    def invoke_method(self, method, *args, **kwargs):
        retval = "Error: Invalid remote method %s" % method
        logging.warning("RPCLink.invoke_method: %s: %s", self.connection_id, retval)
        return retval

class PolicyServer(PacketConnection):
    def __init__(self, stream, address, server_address, allow_domain="*", allow_ports="843"):
        super(PolicyServer, self).__init__(stream, address, server_address,
                                           single_request=True, server_type="flash")
        self.allow_domain = allow_domain
        self.allow_ports = allow_ports

    def process_packet(self, message):
        """ Processes request packet ; raises exception on error
        """
        request = message.strip()
        if not request:
            self.shutdown()
            return

        logging.debug("Policy request: %s", request)
        if request.startswith(POLICY_FILE_REQUEST):
            policy_file = MASTER_POLICY_XML_FORMAT % (self.allow_domain, self.allow_ports)
            self.send_packet(policy_file, utf8=True)
        else:
            host_port = self.map_id_to_host(message)
            self.send_packet(host_port, utf8=True)

    def map_id_to_host(self, group_zid):
        """ Maps group zid to host:port, returning host:port/path, where path may be a null string
        """
        raise SystemMessage("NOT IMPLEMENTED")


class FlashSocket(PacketConnection):
    COOKIE_SEP = "|"

    def __init__(self, stream, address, server_address, allow_domain=""):
        """Specify allow_domain to allow socket to also serve policy files
        """
        self.allow_domain = allow_domain
        self.message_count = 0
        self.group_zid = None
        self.user_code = None
        self.group_code = None
        self.open_access = None
        self.controller_type = None
        self.authenticated = False

        self.client_nonce = None
        self.client_type = None
        self.client_params = None
        self.server_nonce = "snonce"
        self.client_signature = None
        self.server_signature = None
        super(FlashSocket, self).__init__(stream, address, server_address, server_type="flash")

    def map_id_to_host(self, group_zid):
        """ Maps group zid to host:port, returning host:port/path, where path may be a null string
        """
        raise SystemMessage("NOT IMPLEMENTED")

    def process_packet(self, message):
        """ Processes flash request; raises exception on error
        """
        if self.allow_domain and message.startswith(POLICY_FILE_REQUEST):
            policy_file = SOCKET_POLICY_XML_FORMAT % (self.allow_domain, self.server_address[1])
            self.send_packet(policy_file, utf8=True)
            return

        try:
            self.process_flash_request(message)
        except Exception, excp:
            logging.warning("FlashSocket: Error in processing request: %s", excp, exc_info=True)
            if isinstance(excp, UserMessage) and excp.args:
                errmsg, sep, tail = excp.args[0].partition("\n")
            else:
                errmsg = "Server error in processing request"
            self.send_json(["ERROR", errmsg], finish=True)
            return

    def process_flash_request(self, message):
        if not self.message_count and message.startswith("FLASH"):
            # Strip any HTTP-like headers prefix (used for proxying)
            headers, sep, message = message.partition("\r\n\r\n")

        if message.startswith("Map-Name:"):
            header, sep, value = message.partition(":")
            self.send_packet(self.map_name_to_host(value.strip()), finish=True, utf8=true)
            return
        elif not message.startswith("["):
            host_port = self.map_id_to_host(message)
            self.send_packet(host_port, utf8=True)
            return

        self.message_count += 1
        message_obj = json.loads(message)
        if self.message_count == 1:
            if message_obj[0] != "C_HANDSHAKE1":
                raise SystemMessage("Expecting C_HANDSHAKE1 but received %s" % message_obj[0])

            command, self.group_zid, self.user_code, key_version, self.client_nonce, self.client_type, self.client_params = message_obj
            logging.info("Connection request from %s for group %s and user %s with key %s", self.client_type, self.group_zid, self.user_code, key_version)

            self.open_access, access_secret = self.get_access_info(key_version)
            if not self.open_access and not access_secret:
                raise UserMessage("Invalid access key for group/user %s/%s" % (self.group_zid, self.user_code))

            server_prefix = FlashSocket.COOKIE_SEP.join([self.group_zid, key_version, self.client_nonce,
                                                         self.server_nonce])+FlashSocket.COOKIE_SEP
            self.client_signature = hashlib.sha1(server_prefix+"client"+access_secret).hexdigest()
            self.server_signature = hashlib.sha1(server_prefix+"server"+access_secret).hexdigest()
            self.send_json(["S_HANDSHAKE1", self.server_nonce, self.server_signature])

        elif self.message_count == 2:
            if message_obj[0] != "C_HANDSHAKE2":
                raise SystemMessage("Expecting C_HANDSHAKE2 but received %s" % message_obj[0])
            if message_obj[1] == self.client_signature:
                self.authenticated = True
            elif self.user_code or not self.open_access:
                raise UserMessage("Client authentication failed")
            self.register_flash_socket()
        else:
            try:
                self.handle_message_obj(message_obj)
            except UserMessage:
                raise
            except Exception, excp:
                logging.error("FlashSocket.ProcessRequest: Error - %s", excp, exc_info=True)

    def get_access_info(self, key_version):
        raise SystemMessage("NOT IMPLEMENTED")

    def register_flash_socket(self):
        """ Register socket with controlling com_channel for session
        Returns session/task params dict
        Raises exception on failure
        """
        raise SystemMessage("NOT IMPLEMENTED")

    def handle_close(self):
        raise SystemMessage("NOT IMPLEMENTED")

    def handle_message_obj(self, message_obj):
        raise SystemMessage("NOT IMPLEMENTED")


if __name__ == "__main__":
    Flash_socket = None
    class TestPolicyServer(PolicyServer):
        def map_id_to_host(self, group_zid):
            return "localhost:%s" % FLASH_SOCKET_PORT

    class TestFlashSocket(FlashSocket):
        def get_access_info(self, key_version):
            return False, self.group_zid+","+key_version

        def register_flash_socket(self):
            global Flash_socket
            if Flash_socket:
                Flash_socket.shutdown()
            Flash_socket = self
            return {"task": 1, "choice_count": 3}

        def handle_message_obj(self, message_obj):
            data = ["CHAT", "testuser", "black", "Test message!"]
            self.send_json(data)

        def handle_close(self):
            pass

    HOST = "localhost"
    IO_loop = ioloop.IOLoop.instance()
    TestPolicyServer.start_tcp_server(HOST, FLASH_POLICY_PORT, io_loop=IO_loop)
    TestFlashSocket.start_tcp_server(HOST, FLASH_SOCKET_PORT, io_loop=IO_loop)
    IO_loop.start()
