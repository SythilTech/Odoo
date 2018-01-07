# -*- coding: utf-8 -*-
import socket
import re
import random
import hashlib
import threading
import logging
_logger = logging.getLogger(__name__)

class SIPSession:

    USER_AGENT = "Ragnarok"
    rtp_threads = []
    
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
        
    def H(self, data):
        return hashlib.md5(data).hexdigest()

    def KD(self, secret, data):
        return self.H(secret + ":" + data)
        
    def http_auth(self, authheader, method, address):
        realm = re.findall(r'realm="(.*?)"', authheader)[0]
        uri = "sip:" + address
        nonce = re.findall(r'nonce="(.*?)"', authheader)[0]

        A1 = self.username + ":" + realm + ":" + self.password
        A2 = method + ":" + uri

        if "qop=" in authheader:
            qop = re.findall(r'qop="(.*?)"', authheader)[0]
            nc = "00000001"
            cnonce = ''.join([random.choice('0123456789abcdef') for x in range(32)])
            response = self.KD( self.H(A1), nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + self.H(A2) )
            return 'Digest username="' + self.username + '",realm="' + realm + '",nonce="' + nonce + '",uri="' + uri + '",response="' + response + '",cnonce="' + cnonce + '",nc=' + nc + ',qop=auth,algorithm=MD5' + "\r\n"
        else:
            response = self.KD( self.H(A1), nonce + ":" + self.H(A2) )
            return 'Digest username="' + self.username + '",realm="' + realm + '",nonce="' + nonce + '",uri="' + uri + '",response="' + response + '",algorithm=MD5' + "\r\n"

    def send_sip_invite(self, to_address, call_sdp):
                
        call_id = ''.join([random.choice('0123456789abcdef') for x in range(32)])
        self.call_id = call_id
        self.to_address = to_address

        #Don't block the main thread with all the listening
        sip_listener_starter = threading.Thread(target=self.sip_listener, args=(call_id, to_address, call_sdp,))
        sip_listener_starter.start()
        
    def sip_listener(self, call_id, to_address, call_sdp):

        sipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sipsocket.bind(('', 0))
        bind_port = sipsocket.getsockname()[1]
        
        invite_string = ""
	invite_string += "INVITE sip:" + to_address + ":" + str(self.account_port) + " SIP/2.0\r\n"
	invite_string += "Via: SIP/2.0/UDP " + str(self.ip) + ":" + str(bind_port) + ";rport\r\n"
	invite_string += "Max-Forwards: 70\r\n"
	invite_string += "Contact: <sip:" + self.username + "@" + self.ip + ":" + str(bind_port) + ">\r\n"
	invite_string += 'To: <sip:' + to_address + ":" + str(self.account_port) + ">\r\n"
	invite_string += 'From: "' + self.display_name + '"<sip:' + self.username + "@" + self.domain + ":" + str(self.account_port) + ">\r\n"
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

        sipsocket.sendto(invite_string, (to_server, self.account_port) )
        
        #Wait and send back the auth reply
        stage = "WAITING"
        while stage == "WAITING":
            sipsocket.settimeout(3600)
            data, addr = sipsocket.recvfrom(2048)
            _logger.error(data)
 
            #Send auth response if challenged
            if data.split("\r\n")[0] == "SIP/2.0 407 Proxy Authentication Required" or data.split("\r\n")[0] == "SIP/2.0 407 Proxy Authentication required":

                authheader = re.findall(r'Proxy-Authenticate: (.*?)\r\n', data)[0]
                        
                auth_string = self.http_auth(authheader, "INVITE", to_address)

                #Add one to sequence number
                reply = invite_string
                reply = reply.replace("CSeq: 1 ", "CSeq: 2 ")
                
                #Add the Proxy Authorization line before the supported line
                idx = reply.index("Supported:")
                reply = reply[:idx] + "Proxy-Authorization: " + auth_string + reply[idx:]
                
                sipsocket.sendto(reply, addr)
            elif data.split("\r\n")[0] == "SIP/2.0 401 Unauthorized":

                authheader = re.findall(r'WWW-Authenticate: (.*?)\r\n', data)[0]

                auth_string = self.http_auth(authheader, "INVITE", to_address)

                #Add one to sequence number
                reply = invite_string
                reply = reply.replace("CSeq: 1 ", "CSeq: 2 ")
                
                #Add the Authorization line before the supported line
                idx = reply.index("Supported:")
                reply = reply[:idx] + "Authorization: " + auth_string + reply[idx:]
                             
                sipsocket.sendto(reply, addr)
            elif data.split("\r\n")[0] == "SIP/2.0 403 Forbidden":
                #Likely means call was rejected
                self.call_rejected.fire(self, data)
                stage = "Forbidden"
                return False
            elif data.startswith("BYE"):
                #Do stuff when the call is ended by client
                self.call_ended.fire(data)
                stage = "BYE"
                return True
            elif data.split("\r\n")[0] == "SIP/2.0 200 OK":

                contact_header = re.findall(r'Contact: <(.*?)>\r\n', data)[0]
                record_route = re.findall(r'Record-Route: (.*?)\r\n', data)[0]
                call_from = re.findall(r'From: (.*?)\r\n', data)[0]
                call_to = re.findall(r'To: (.*?)\r\n', data)[0]
                
                #Send the ACK
                reply = ""
                reply += "ACK " + contact_header + " SIP/2.0\r\n"
                reply += "Via: SIP/2.0/UDP " + str(self.ip) + ":" + str(bind_port) + ";rport\r\n"
                reply += "Max-Forwards: 70\r\n"
                reply += "Route: " + record_route + "\r\n"
                reply += "Contact: <sip:" + self.username + "@" + str(self.ip) + ":" + str(bind_port) + ">\r\n"
                reply += 'To: ' + call_to + "\r\n"
                reply += "From: " + call_from + "\r\n"
                reply += "Call-ID: " + str(call_id) + "\r\n"
                reply += "CSeq: 2 ACK\r\n"
                reply += "User-Agent: " + str(self.USER_AGENT) + "\r\n"
                reply += "Content-Length: 0\r\n"
                reply += "\r\n"

                sipsocket.sendto(reply, addr)
                
                self.call_accepted.fire(self, data)
            elif data.split("\r\n")[0].startswith("SIP/2.0 4"):
                self.call_error.fire(self, data)
                
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