# -*- coding: utf-8 -*-
import sys
import socket
import re
import random
import hashlib
import threading
import time
import logging
_logger = logging.getLogger(__name__)

class SIPSession:

    USER_AGENT = "Ragnarok"
    rtp_threads = []
    sip_history = {}

    def __init__(self, ip, username, domain, password, auth_username=False, outbound_proxy=False, account_port="5060", display_name="-"):
        self.ip = ip
        self.username = username
        self.domain = domain
        self.password = password
        self.auth_username = auth_username
        self.outbound_proxy = outbound_proxy
        self.account_port = account_port
        self.display_name = display_name
        self.call_accepted = EventHook()
        self.call_rejected = EventHook()
        self.call_ended = EventHook()
        self.call_error = EventHook()
        self.call_ringing = EventHook()
        self.message_sent = EventHook()
        self.message_received = EventHook()
        self.register_ok = EventHook()

        #Each account is bound to a different port
        self.sipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sipsocket.bind(('', 0))
        self.bind_port = self.sipsocket.getsockname()[1]

        #Don't block the main thread with all the listening
        sip_listener_starter = threading.Thread(target=self.sip_listener, args=())
        sip_listener_starter.start()

    def H(self, data):
        return hashlib.md5( data.encode() ).hexdigest()

    def KD(self, secret, data):
        return self.H(secret + ":" + data)

    def http_auth(self, authheader, method, address):
        realm = re.findall(r'realm="(.*?)"', authheader)[0]
        uri = "sip:" + address
        nonce = re.findall(r'nonce="(.*?)"', authheader)[0]

        if self.auth_username:
            username = self.auth_username
        else:
            username = self.username

        A1 = username + ":" + realm + ":" + self.password
        A2 = method + ":" + uri

        if "qop=" in authheader:
            qop = re.findall(r'qop="(.*?)"', authheader)[0]
            nc = "00000001"
            cnonce = ''.join([random.choice('0123456789abcdef') for x in range(32)])
            response = self.KD( self.H(A1), nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + self.H(A2) )
            return 'Digest username="' + username + '",realm="' + realm + '",nonce="' + nonce + '",uri="' + uri + '",response="' + response + '",cnonce="' + cnonce + '",nc=' + nc + ',qop=auth,algorithm=MD5' + "\r\n"
        else:
            response = self.KD( self.H(A1), nonce + ":" + self.H(A2) )
            return 'Digest username="' + username + '",realm="' + realm + '",nonce="' + nonce + '",uri="' + uri + '",response="' + response + '",algorithm=MD5' + "\r\n"

    def answer_call(self, sip_invite, sdp):

        call_id = re.findall(r'Call-ID: (.*?)\r\n', sip_invite)[0]
        call_from = re.findall(r'From: (.*?)\r\n', sip_invite)[0]
        call_to = re.findall(r'To: (.*?)\r\n', sip_invite)[0]

        reply = ""
        reply += "SIP/2.0 200 OK\r\n"
        for (via_heading) in re.findall(r'Via: (.*?)\r\n', sip_invite):
            reply += "Via: " + via_heading + "\r\n"
        record_route = re.findall(r'Record-Route: (.*?)\r\n', sip_invite)[0]
        reply += "Record-Route: " + record_route + "\r\n"
        reply += "Contact: <sip:" + str(self.username) + "@" + str(self.ip) + ":" + str(self.bind_port) + ">\r\n"
        reply += "To: " + call_to + "\r\n"
        reply += "From: " + call_from + "\r\n"
        reply += "Call-ID: " + str(call_id) + "\r\n"
        reply += "CSeq: 1 INVITE\r\n"
        reply += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        reply += "Content-Type: application/sdp\r\n"
        reply += "Supported: replaces\r\n"
        reply += "User-Agent: " + str(self.USER_AGENT) + "\r\n"
        reply += "Content-Length: " + str(len(sdp)) + "\r\n"
        reply += "\r\n"
        reply += sdp

        self.sipsocket.sendto(reply.encode(), (self.to_server, self.account_port) )

    def send_sip_message(self, to_address, message_body):
        call_id = ''.join([random.choice('0123456789abcdef') for x in range(32)])

        message_string = ""
        message_string += "MESSAGE sip:" + str(self.username) + "@" + str(self.domain) + " SIP/2.0\r\n"
        message_string += "Via: SIP/2.0/UDP " + str(self.ip) + ":" + str(self.bind_port) + ";rport\r\n"
        message_string += "Max-Forwards: 70\r\n"
        message_string += 'To: <sip:' + to_address + ">;messagetype=IM\r\n"
        message_string += 'From: "' + str(self.display_name) + '"<sip:' + str(self.username) + "@" + str(self.domain) + ":" + str(self.account_port) + ">\r\n"
        message_string += "Call-ID: " + str(call_id) + "\r\n"
        message_string += "CSeq: 1 MESSAGE\r\n"
        message_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        message_string += "Content-Type: text/html\r\n"
        message_string += "User-Agent: " + str(self.USER_AGENT) + "\r\n"
        message_string += "Content-Length: " + str(len(message_body)) + "\r\n"
        message_string += "\r\n"
        message_string += message_body

        if self.outbound_proxy:
            to_server = self.outbound_proxy
        else:
            to_server = self.domain

        self.sipsocket.sendto(message_string.encode(), (to_server, self.account_port) )
        self.sip_history[call_id] = []
        self.sip_history[call_id].append(message_string)
        return call_id

    def send_sip_register(self, register_address, register_frequency=3600):

        call_id = ''.join([random.choice('0123456789abcdef') for x in range(32)])

        register_string = ""
        register_string += "REGISTER sip:" + self.domain + ":" + str(self.account_port) + " SIP/2.0\r\n"
        register_string += "Via: SIP/2.0/UDP " + str(self.ip) + ":" + str(self.bind_port) + ";rport\r\n"
        register_string += "Max-Forwards: 70\r\n"
        register_string += "Contact: <sip:" + str(self.username) + "@" + str(self.ip) + ":" + str(self.bind_port) + ">\r\n"
        register_string += 'To: "' + str(self.display_name) + '"<sip:' + str(self.username) + "@" + str(self.domain) + ":" + str(self.account_port) + ">\r\n"
        register_string += 'From: "' + str(self.display_name) + '"<sip:' + str(self.username) + "@" + str(self.domain) + ":" + str(self.account_port) + ">\r\n"
        register_string += "Call-ID: " + str(call_id) + "\r\n"
        register_string += "CSeq: 1 REGISTER\r\n"
        register_string += "Expires: " + str(register_frequency) + "\r\n"
        register_string += "Allow: NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        register_string += "User-Agent: " + str(self.USER_AGENT) + "\r\n"
        register_string += "Content-Length: 0\r\n"
        register_string += "\r\n"

        if self.outbound_proxy:
            self.to_server = self.outbound_proxy
        else:
            self.to_server = self.domain

        self.sip_history[call_id] = []
        self.sip_history[call_id].append(register_string)

        #Reregister to keep the session alive
        reregister_starter = threading.Thread(target=self.reregister, args=(register_string, register_frequency,))
        reregister_starter.start()

    def reregister(self, register_string, register_frequency):
        try:
            _logger.error(register_string)
            self.sipsocket.sendto(register_string.encode(), (self.to_server, self.account_port) )
            time.sleep(register_frequency)
            self.reregister(register_string, register_frequency)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            _logger.error(e)
            _logger.error("Line: " + str(exc_tb.tb_lineno) )

    def send_sip_invite(self, to_address, call_sdp):

        call_id = ''.join([random.choice('0123456789abcdef') for x in range(32)])

        invite_string = ""
        invite_string += "INVITE sip:" + to_address + ":" + str(self.account_port) + " SIP/2.0\r\n"
        invite_string += "Via: SIP/2.0/UDP " + str(self.ip) + ":" + str(self.bind_port) + ";rport\r\n"
        invite_string += "Max-Forwards: 70\r\n"
        invite_string += "Contact: <sip:" + str(self.username) + "@" + str(self.ip) + ":" + str(self.bind_port) + ">\r\n"
        invite_string += 'To: <sip:' + to_address + ":" + str(self.account_port) + ">\r\n"
        invite_string += 'From: "' + str(self.display_name) + '"<sip:' + str(self.username) + "@" + str(self.domain) + ":" + str(self.account_port) + ">\r\n"
        invite_string += "Call-ID: " + str(call_id) + "\r\n"
        invite_string += "CSeq: 1 INVITE\r\n"
        invite_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        invite_string += "Content-Type: application/sdp\r\n"
        invite_string += "Supported: replaces\r\n"
        invite_string += "User-Agent: " + str(self.USER_AGENT) + "\r\n"
        invite_string += "Content-Length: " + str(len(call_sdp)) + "\r\n"
        invite_string += "\r\n"
        invite_string += call_sdp

        to_server = ""
        if self.outbound_proxy:
            to_server = self.outbound_proxy
        else:
            to_server = self.domain

        _logger.error(invite_string)

        self.sipsocket.sendto(invite_string.encode(), (to_server, self.account_port) )
        self.sip_history[call_id] = []
        self.sip_history[call_id].append(invite_string)
        return call_id

    def sip_listener(self):

        try:

            _logger.error("Listening for SIP messages on " + str(self.bind_port) )

            #Wait and send back the auth reply
            stage = "WAITING"
            while stage == "WAITING":

                data, addr = self.sipsocket.recvfrom(2048)

                data = data.decode()

                _logger.error(data)

                #Send auth response if challenged
                if data.split("\r\n")[0] == "SIP/2.0 407 Proxy Authentication Required" or data.split("\r\n")[0] == "SIP/2.0 407 Proxy Authentication required":

                    authheader = re.findall(r'Proxy-Authenticate: (.*?)\r\n', data)[0]
                    call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]
                    cseq = re.findall(r'CSeq: (.*?)\r\n', data)[0]
                    cseq_number = cseq.split(" ")[0]
                    cseq_type = cseq.split(" ")[1]
                    call_to_full = re.findall(r'To: (.*?)\r\n', data)[0]
                    call_to = re.findall(r'<sip:(.*?)>', call_to_full)[0]
                    if ":" in call_to: call_to = call_to.split(":")[0]

                    #Resend the initial message but with the auth_string
                    reply = self.sip_history[call_id][0]
                    auth_string = self.http_auth(authheader, cseq_type, call_to)

                    #Add one to sequence number
                    reply = reply.replace("CSeq: " + str(cseq_number) + " ", "CSeq: " + str(int(cseq_number) + 1) + " ")

                    #Add the Proxy Authorization line before the User-Agent line
                    idx = reply.index("User-Agent:")
                    reply = reply[:idx] + "Proxy-Authorization: " + auth_string + reply[idx:]

                    self.sipsocket.sendto(reply.encode(), addr)
                elif data.split("\r\n")[0] == "SIP/2.0 401 Unauthorized":

                    authheader = re.findall(r'WWW-Authenticate: (.*?)\r\n', data)[0]
                    call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]
                    cseq = re.findall(r'CSeq: (.*?)\r\n', data)[0]
                    cseq_number = cseq.split(" ")[0]
                    cseq_type = cseq.split(" ")[1]
                    call_to_full = re.findall(r'To: (.*?)\r\n', data)[0]
                    call_to = re.findall(r'<sip:(.*?)>', call_to_full)[0]
                    if ":" in call_to: call_to = call_to.split(":")[0]

                    #Resend the initial message but with the auth_string
                    reply = self.sip_history[call_id][0]
                    auth_string = self.http_auth(authheader, cseq_type, call_to)

                    #Add one to sequence number
                    reply = reply.replace("CSeq: " + str(cseq_number) + " ", "CSeq: " + str(int(cseq_number) + 1) + " ")

                    #Add the Authorization line before the User-Agent line
                    idx = reply.index("User-Agent:")
                    reply = reply[:idx] + "Authorization: " + auth_string + reply[idx:]

                    _logger.error(reply)
                    self.sipsocket.sendto(reply.encode(), addr)
                elif data.split("\r\n")[0] == "SIP/2.0 403 Forbidden":
                    #Likely means call was rejected
                    self.call_rejected.fire(self, data)
                    stage = "Forbidden"
                    return False
                elif data.startswith("MESSAGE"):
                    #Extract the actual message to make things easier for devs
                    message = data.split("\r\n\r\n")[1]
                    if "<isComposing" not in message:
                        self.message_received.fire(self, data, message)
                elif data.startswith("INVITE"):

                    call_from = re.findall(r'From: (.*?)\r\n', data)[0]
                    call_to = re.findall(r'To: (.*?)\r\n', data)[0]
                    call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]

                    #Send Trying
                    trying = ""
                    trying += "SIP/2.0 100 Trying\r\n"
                    for (via_heading) in re.findall(r'Via: (.*?)\r\n', data):
                        trying += "Via: " + via_heading + "\r\n"
                    trying += "To: " + call_to + "\r\n"
                    trying += "From: " + call_from + "\r\n"
                    trying += "Call-ID: " + str(call_id) + "\r\n"
                    trying += "CSeq: 1 INVITE\r\n"
                    trying += "Content-Length: 0\r\n"
                    trying += "\r\n"

                    self.sipsocket.sendto(trying.encode(), addr)

                    #Even automated calls can take a second to get ready to answer
                    ringing = ""
                    ringing += "SIP/2.0 180 Ringing\r\n"
                    for (via_heading) in re.findall(r'Via: (.*?)\r\n', data):
                        ringing += "Via: " + via_heading + "\r\n"
                    record_route = re.findall(r'Record-Route: (.*?)\r\n', data)[0]
                    ringing += "Record-Route: " + record_route + "\r\n"
                    ringing += "Contact: <sip:" + str(self.username) + "@" + str(self.ip) + ":" + str(self.bind_port) + ">\r\n"
                    ringing += "To: " + call_to + "\r\n"
                    ringing += "From: " + call_from + "\r\n"
                    ringing += "Call-ID: " + str(call_id) + "\r\n"
                    ringing += "CSeq: 1 INVITE\r\n"
                    ringing += "User-Agent: " + str(self.USER_AGENT) + "\r\n"
                    ringing += "Allow-Events: talk, hold\r\n"
                    ringing += "Content-Length: 0\r\n"
                    ringing += "\r\n"

                    self.sipsocket.sendto(ringing.encode(), addr)

                    self.call_ringing.fire(self, data)
                elif data.startswith("BYE"):
                    #Do stuff when the call is ended by client
                    self.call_ended.fire(self, data)
                    stage = "BYE"
                    return True
                elif data.split("\r\n")[0] == "SIP/2.0 200 OK":

                    cseq = re.findall(r'CSeq: (.*?)\r\n', data)[0]
                    cseq_type = cseq.split(" ")[1]

                    #200 OK is used by REGISTER, INVITE and MESSAGE, so the code logic gets split up
                    if cseq_type == "INVITE":
                        cseq_number = cseq.split(" ")[0]
                        contact_header = re.findall(r'Contact: <(.*?)>\r\n', data)[0]
                        record_route = re.findall(r'Record-Route: (.*?)\r\n', data)[0]
                        call_from = re.findall(r'From: (.*?)\r\n', data)[0]
                        call_to = re.findall(r'To: (.*?)\r\n', data)[0]
                        call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]

                        #Send the ACK
                        reply = ""
                        reply += "ACK " + contact_header + " SIP/2.0\r\n"
                        reply += "Via: SIP/2.0/UDP " + str(self.ip) + ":" + str(self.bind_port) + ";rport\r\n"
                        reply += "Max-Forwards: 70\r\n"
                        reply += "Route: " + record_route + "\r\n"
                        reply += "Contact: <sip:" + self.username + "@" + str(self.ip) + ":" + str(self.bind_port) + ">\r\n"
                        reply += 'To: ' + call_to + "\r\n"
                        reply += "From: " + call_from + "\r\n"
                        reply += "Call-ID: " + str(call_id) + "\r\n"
                        reply += "CSeq: " + str(cseq_number) + " ACK\r\n"
                        reply += "User-Agent: " + str(self.USER_AGENT) + "\r\n"
                        reply += "Content-Length: 0\r\n"
                        reply += "\r\n"

                        self.sipsocket.sendto(reply.encode(), addr)

                        self.call_accepted.fire(self, data)
                    elif cseq_type == "MESSAGE":
                        self.message_sent.fire(self, data)
                    elif cseq_type == "REGISTER":
                        self.register_ok.fire(self, data)
                elif data.split("\r\n")[0].startswith("SIP/2.0 4"):
                    self.call_error.fire(self, data)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            _logger.error(e)
            _logger.error("Line: " + str(exc_tb.tb_lineno) )

class EventHook(object):

    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def fire(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)

    def clearObjectHandlers(self, inObject):
        for theHandler in self.__handlers:
            if theHandler.im_self == inObject:
                self -= theHandler