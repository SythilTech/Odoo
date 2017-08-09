# -*- coding: utf-8 -*-
from openerp.http import request
import datetime
import logging
import socket
import threading
_logger = logging.getLogger(__name__)
import time
from random import randint
from hashlib import sha1
import hmac
import hashlib
import random
import string
import passlib
import struct
import zlib
from openerp.exceptions import UserError
import binascii
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import api, fields, models

class VoipCall(models.Model):

    _name = "voip.call"

    from_partner_id = fields.Many2one('res.partner', string="From", help="From can be blank if the call comes from outside of the system")
    partner_id = fields.Many2one('res.partner', string="To")
    status = fields.Selection([('pending','Pending'), ('missed','Missed'), ('accepted','Accepted'), ('rejected','Rejected'), ('active','Active'), ('over','Complete')], string='Status', default="pending", help="Pending = Calling person\nActive = currently talking\nMissed = Call timed out\nOver = Someone hit end call\nRejected = Someone didn't want to answer the call")
    start_time = fields.Datetime(string="Answer Time", help="Time the call was answered, create_date is when it started dialing")
    end_time = fields.Datetime(string="End Time", help="Time the call end")
    duration = fields.Char(string="Duration", help="Length of the call")
    transcription = fields.Text(string="Transcription", help="Automatic transcription of the call")
    notes = fields.Text(string="Notes", help="Additional comments outside the transcription")
    client_ids = fields.One2many('voip.call.client', 'vc_id', string="Client List")
    type = fields.Selection([('internal','Internal'),('external','External')], string="Type")
    mode = fields.Selection([('videocall','video call'), ('audiocall','audio call'), ('screensharing','screen sharing call')], string="Mode", help="This is only how the call starts, i.e a video call can turn into a screen sharing call mid way")
    sip_tag = fields.Char(string="SIP Tag")
    direction = fields.Selection([('internal','Internal'), ('incoming','Incoming'), ('outgoing','Outgoing')], string="Direction")
    ice_password = fields.Char(string="ICE Password")

    def accept_call(self):
        """ Mark the call as accepted and send response to close the notification window and open the VOIP window """
        
        if self.status == "pending":
            self.status = "accepted"

        #call_client = request.env['voip.call.client'].search([('vc_id','=', voip_call.id ), ('partner_id','=', request.env.user.partner_id.id) ])
        #call_client.sip_addr_host = request.httprequest.remote_addr
        
        #Notify caller and callee that the call was accepted
        for voip_client in self.client_ids:
            notification = {'call_id': self.id, 'status': 'accepted', 'type': self.type}
            self.env['bus.bus'].sendone((request._cr.dbname, 'voip.response', voip_client.partner_id.id), notification)

    def reject_call(self):
        """ Mark the call as rejected and send the response so the notification window is closed on both ends """
    
        if self.status == "pending":
            self.status = "rejected"
        
        #Notify caller and callee that the call was rejected
        for voip_client in self.client_ids:
            notification = {'call_id': self.id, 'status': 'rejected'}
            self.env['bus.bus'].sendone((request._cr.dbname, 'voip.response', voip_client.partner_id.id), notification)
    
    def miss_call(self):
        """ Mark the call as missed, both caller and callee will close there notification window due to the timeout """

        if self.status == "pending":
            self.status = "missed"
        
    def begin_call(self):
        """ Mark the call as active, we start recording the call duration at this point """
        
        if self.status == "accepted":
            self.status = "active"

        self.start_time = datetime.datetime.now()

    def end_call(self):
        """ Mark the call as over, we can calculate the call duration based on the start time, also send notification to both sides to close there VOIP windows """
        
        if self.status == "active":
            self.status = "over"
            
            self.end_time = datetime.datetime.now()
            diff_time = datetime.datetime.strptime(self.end_time, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.datetime.strptime(self.start_time, DEFAULT_SERVER_DATETIME_FORMAT)
            self.duration = str(diff_time.seconds) + " Seconds"

        #Notify both caller and callee that the call is ended
        for voip_client in self.client_ids:
            notification = {'call_id': self.id}
            self.env['bus.bus'].sendone((self._cr.dbname, 'voip.end', voip_client.partner_id.id), notification)

    def generate_call_sdp(self):
    
        sdp_response = ""
                
        #Protocol Version ("v=") https://tools.ietf.org/html/rfc4566#section-5.1 (always 0 for us)
        sdp_response += "v=0\r\n"

        #Origin ("o=") https://tools.ietf.org/html/rfc4566#section-5.2 (Should come up with a better session id...)
        sess_id = int(time.time()) #Not perfect but I don't expect more then one call a second
        sess_version = 0 #Will always start at 0
        _logger.error( str(sess_id) )
        sdp_response += "o=- " + str(sess_id) + " " + str(sess_version) + " IN IP4 0.0.0.0\r\n"        
        
        #Session Name ("s=") https://tools.ietf.org/html/rfc4566#section-5.3 (We don't need a session name, information about the call is all displayed in the UI)
        sdp_response += "s= \r\n"
        
        #Timing ("t=") https://tools.ietf.org/html/rfc4566#section-5.9 (For now sessions are infinite but we may use this if for example a company charges a price for a fixed 30 minute consultation)
        sdp_response += "t=0 0\r\n"
        
        #In later versions we might send the missed call mp3 via rtp
        sdp_response += "a=sendrecv\r\n"

        #TODO generate before call fingerprint...
        sdp_response += "a=fingerprint:sha-256 DA:52:67:C5:2A:2E:91:13:A2:7D:3A:E1:2E:A4:F3:28:90:67:71:0E:B7:6F:7B:56:79:F4:B2:D1:54:4B:92:7E\r\n"
        #sdp_response += "a=setup:actpass\r\n"
        sdp_response += "a=setup:passive\r\n"
        #sdp_response += "a=setup:active\r\n"
        
        #Sure why not
        sdp_response += "a=ice-options:trickle\r\n"

        #Sigh no idea
        sdp_response += "a=msid-semantic:WMS *\r\n"

        #Random stuff, left here so I don't have get it a second time if needed
        #example supported audio profiles: 109 9 0 8 101
        #sdp_response += "m=audio 9 UDP/TLS/RTP/SAVPF 109 101\r\n"
                
        #Media Descriptions ("m=") https://tools.ietf.org/html/rfc4566#section-5.14 (Message bank is audio only for now)
        audio_codec = "9" #Use G722 Audio Profile
        sdp_response += "m=audio 9 UDP/TLS/RTP/SAVPF " + audio_codec + "\r\n"
        
        #Connection Data ("c=") https://tools.ietf.org/html/rfc4566#section-5.7 (always seems to be 0.0.0.0?)
        sdp_response += "c=IN IP4 0.0.0.0\r\n"

        #ICE creds (https://tools.ietf.org/html/rfc5245#page-76)
        ice_ufrag = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
        ice_pwd = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(22))
        self.ice_password = ice_pwd
        sdp_response += "a=ice-ufrag:" + str(ice_ufrag) + "\r\n"
        sdp_response += "a=ice-pwd:" + str(ice_pwd) + "\r\n"

        #Ummm naming each media?!?
        sdp_response += "a=mid:sdparta_0\r\n"
        
        #Description of audio 101 / 109 profile?!?
        #sdp_response += "a=sendrecv\r\n"
        #sdp_response += "a=fmtp:109 maxplaybackrate=48000;stereo=1;useinbandfec=1\r\n"
        #sdp_response += "a=fmtp:101 0-15\r\n"
        #sdp_response += "a=msid:{3778521f-c0cd-47a8-aa20-66c06fbf184e} {7d104cf0-8223-49bf-9ff4-6058cf92e1cf}\r\n"
        #sdp_response += "a=rtcp-mux\r\n"
        #sdp_response += "a=rtpmap:109 opus/48000/2\r\n"
        #sdp_response += "a=rtpmap:101 telephone-event/8000\r\n"

        #sdp_response += "a=ssrc:615080754 cname:{22894fcb-8532-410d-ad4b-6b8e58e7631a}\r\n"
    
        return {"type":"answer","sdp": sdp_response}

    def message_bank(self, sdp):

        _logger.error("Message Bank")

        server_sdp = self.generate_call_sdp()

        _logger.error(server_sdp)
        
        notification = {'call_id': self.id, 'sdp': server_sdp }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.sdp', self.from_partner_id.id), notification)

        #RTP
        #port = 62382
        #Random even number
        port = randint(16384 /2, 32767 / 2) * 2
        server_ice_candidate = self.env['voip.server'].generate_server_ice(port, 1)
        self.start_rtc_listener(port, "RTP")
        notification = {'call_id': self.id, 'ice': server_ice_candidate }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', self.from_partner_id.id), notification)

        #RTCP
        #port += 1
        #server_ice_candidate = self.env['voip.server'].generate_server_ice(port, 2)
        #self.start_rtc_listener(port, "RTCP")
        #notification = {'call_id': self.id, 'ice': server_ice_candidate }
        #self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', self.from_partner_id.id), notification)

    def voip_call_sdp(self, sdp):
        """Store the description and send it to everyone else"""

        _logger.error(sdp)
        
        if self.type == "internal":
            for voip_client in self.client_ids:
                if voip_client.partner_id.id == self.env.user.partner_id.id:
                    voip_client.sdp = sdp
                else:
                    notification = {'call_id': self.id, 'sdp': sdp }
                    self.env['bus.bus'].sendone((self._cr.dbname, 'voip.sdp', voip_client.partner_id.id), notification)
                    
        elif self.type == "external":
            if self.direction == "incoming":
                #Send the 200 OK repsonse with SDP information
                from_client = self.env['voip.call.client'].search([('vc_id', '=', self.id), ('partner_id', '=', self.from_partner_id.id) ])
                to_client = self.env['voip.call.client'].search([('vc_id', '=', self.id), ('partner_id', '=', self.partner_id.id) ])                

                sip_dict = self.env['voip.voip'].sip_read_message(from_client.sip_invite)
                
                _logger.error("From: " + sip_dict['From'].strip().replace(":",">;") )
                _logger.error("To: " + sip_dict['To'].strip().replace(":",">;"))
                _logger.error("CSeq: " + sip_dict['CSeq'].strip())
                _logger.error("Contact: " + sip_dict['Contact'].strip())

                reply = ""
                reply += "SIP/2.0 200 OK\r\n"
                reply += "From: " + from_client.name + "<" + sip_dict['From'].strip() + "\r\n"
                reply += "To: " + to_client.name + "<" + sip_dict['To'].strip() + ";tag=" + str(self.sip_tag) + "\r\n"
                reply += "CSeq: " + sip_dict['CSeq'].strip() + "\r\n"
                reply += "Contact: <sip:" + to_client.name + "@" + to_client.sip_addr_host + ">\r\n"
                reply += "Content-Type: application/sdp\r\n"
                reply += "Content-Disposition: session\r\n"
                reply += "Content-Length: " + str( len( sdp_data['sdp'] ) ) + "\r\n"
                reply += "\r\n"
                reply += sdp_data['sdp'].strip()
                
                serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                serversocket.sendto(reply, (from_client.sip_addr_host,from_client.sip_addr_port) )

                _logger.error("200 OK: " + reply )


                from_partner_sdp_data = from_client.sip_invite.split("\r\n\r\n")[1]
                from_partner_sdp_data_json = json.dumps({'sdp': from_partner_sdp_data})

                #Send the caller dsp data to the calle now
                for voip_client in self.client_ids:
                    if voip_client.partner_id.id == self.env.user.partner_id.id:
                        notification = {'call_id': self.id, 'sdp': from_partner_sdp_data_json }
                        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.sdp', voip_client.partner_id.id), notification)

            elif self.direction == "outgoing":
                #Send the INVITE
                from_sip = self.env.user.partner_id.sip_address.strip()
                to_sip = self.partner_id.sip_address.strip()
                reg_from = from_sip("@")[1]
                reg_to = to_sip.split("@")[1]

                register_string = ""
                register_string += "REGISTER sip:" + reg_to + " SIP/2.0\r\n"
                register_string += "Via: SIP/2.0/UDP " + reg_from + "\r\n"
                register_string += "From: sip:" + from_sip + "\r\n"
                register_string += "To: sip:" + to_sip + "\r\n"
                register_string += "Call-ID: " + "17320@" + reg_to + "\r\n"
                register_string += "CSeq: 1 REGISTER\r\n"
                register_string += "Expires: 7200\r\n"
                register_string += "Contact: " + self.env.user.partner_id.name + "\r\n"

                serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                serversocket.sendto(register_string, ('91.121.209.194', 5060) )

                _logger.error("REGISTER: " + register_string)

                #reply = ""
                #reply += "INVITE sip:" + to_sip + " SIP/2.0\r\n"
                #reply += "From: " + request.env.user.partner_id.name + "<sip:" + from_sip + ">; tag = odfgjh\r\n"
                #reply += "To: " + voip_call.partner_id.name.strip + "<sip:" + voip_call.partner_id.sip_address + ">\r\n"
                #reply += "CSeq: 1 INVITE\r\n"
                #reply += "Content-Length: " + str( len( sdp_data['sdp'] ) ) + "\r\n"
                #reply += "Content-Type: application/sdp\r\n"
                #reply += "Content-Disposition: session\r\n"
                #reply += "\r\n"
                #reply += sdp_data['sdp']
                
                #serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                #serversocket.sendto(reply, ('91.121.209.194', 5060) )

                #_logger.error("INVITE: " + reply )        

    def voip_call_ice(self, ice):
        """Forward ICE to everyone else"""
        
        #_logger.error("ICE: ")
        #_logger.error(ice)        

        for voip_client in self.client_ids:
            
            #Don't send ICE back to yourself
            if voip_client.partner_id.id != self.env.user.partner_id.id:
                notification = {'call_id': self.id, 'ice': ice }
                self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', voip_client.partner_id.id), notification)        

    def close_message_bank(self):
        
        #Notify the caller that the call is ended due to message bank timeout
        notification = {'call_id': self.id}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.end', self.from_partner_id.id), notification)
        
        #TODO trancode G722 to a format that can be listened to within a browser
        
        #TODO save the transcoded file to the call so it can be listened to later (Only keep for 48 hours to save space also legal requirements in some places)
        
    def rtp_stun_listener(self, d, addr):

        if d[1] == "00" and d[2] == "01":
            message_type = "Binding Request"
                
        message_length = int( d[3] + d[4], 16)
        _logger.error(message_length)
        message_cookie = ' '.join(d[5:9])
        transaction_id = ' '.join(d[9:21])

        #----Compose binding request-----
        send_data = ""
        
        #Message Type (Binding Success Response)
        send_data += "01 01"

        #Message Length (a static 12 only because our output is mostly fixed)
        send_data += " 00 0c"

        #Magic Cookie (always set to 0x2112A442)
        send_data += " 21 12 a4 42"

        #96 bit (12 byte) transaction ID (has to be the same as the bind request)
        send_data += transaction_id



        
        #XOR mapped address attribute
        send_data += " 00 20"

        #Attribute Length (In this controlled environment it will always be 44)
        send_data += " 00 2C"

        #Reservered (reserved for what...)
        send_data += " 00"

        #Protocol Family (Always IPv4 for now...)
        send_data += " 01"
        
        #Port XOR (Need to figure this one out...)
        client_port = addr[1]
        send_data += " " + format( client_port ^ 0x2112 , '04x')
        
        #IP XOR-d (Figure this out too...)
        #server_ip = addr[0]
        server_ip = "13.54.58.172"
        server_ip_int = struct.unpack("!I", socket.inet_aton(server_ip))[0]
        send_data += " " + format( server_ip_int ^ 0x2112A442 , '08x')


            
        try:
            #How to get shared secret password???
                        
            #Test tool (https://caligatio.github.io/jsSHA/)
            _logger.error("HMAC")
            hmac_input = send_data.replace(" ","")
            #stun_password = self.ice_password

            #Example code (works) (http://pythonexample.com/snippet/python/stun-message-integrity-verifier)
            #hmac_input = "000100542112a442e4e8b0fd9c22943265a6f9fd0006000c617957763a653343660000000024000478ffffff80290008000000003033323380540004310000008070000400000002"
            #stun_password = u"xa/ykWBKUukRHCxH8O1hkQbo"
            #Expected output: eb7db09217a9a9cdded592c200f3c372dd1c7417


            #MS Example (works) (https://blogs.msdn.microsoft.com/openspecification/2016/02/23/verifying-stun-message-integrity-for-lync-and-skype-for-business-ice-traffic/)
            #hmac_input = "000100542112A442BEEBD6F17710B6A1B6A92CBD0006000C764F614D3A66764173000000002400046EFFFEFF80290008000000000001E6E4805400043100000080700004000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
            #stun_password = u"ydYldnHIRgbOUr1MYUGy4t0g"
            #Expected output: b87d4d8d56fc76794667aacae3593e58e1dbfe97
            
            #RFC example (doesn't???) (https://tools.ietf.org/html/rfc5769)
            hmac_input = "0101003c2112a442b7e7a701bc34d686fa87dfae8022000b7465737420766563746f7220002000080001a147e112a643" #48 bytes
            stun_password = u"VOkJxbRl1RmTxUk/WvJxBt"
            #Expected output: 2b91f599fd9e90c38c7489f92af9ba53f06be7d7
            
            #Wireshark example (doesn't???)
            #ice 1 (raw): 4f9b6cb3a46d69c31f8e4e81593e87c5
            #ice 2 (raw): 8af63ee16bd97224f01a3e8aee4791d1
            #hmac_input = "0001004c2112a4428797acd4f4bd5dd741edbfa90006001138633063626663313a3333386634343961000000002400046e7e00ff8029000817ae03baa3d911ce"
            #expected output : 87 92 09 e5 c5 88 ba 67 e9 3c 6d cc 11 64 5d d7 d6 30 05 99


            #Pad send_data to fit 64 bytes
            send_data_length = len(hmac_input.decode("hex"))
            _logger.error(send_data_length)
            
            if send_data_length % 64 != 0:
                for _ in range(64 - (send_data_length % 64) ):
                    hmac_input += "00"

            _logger.error(len(hmac_input.decode("hex")))
            
            key = passlib.utils.saslprep( stun_password )

            #Not tested
            mess_hmac = hmac.new( str(key), msg=hmac_input.decode("hex"), digestmod=hashlib.sha1).digest().encode('hex')
            
            _logger.error(mess_hmac)
        except Exception as e:
            _logger.error(e)
        
        #Message Integrity Attribute
        send_data += " 00 08"
        
        #Attribute Length (Always 20 bytes)
        send_data += " 00 14"
        
        #HMAC-SHA1
        send_data += mess_hmac
        
        
        #send_data += " 9e 6c 30 f6 5c 10 8a 0d 49 69 69 dd f4 e0 6d 16 d7 07 cf 81"



        crc32_int = binascii.crc32( binascii.a2b_hex(  send_data.replace(" ","") ) )  % (1<<32)
        crc_hex = format( crc32_int ^ 0x5354554e, '08x')

        #Fingerprint Attribute
        send_data += " 80 28"
        
        #Atrribute Length (CRC-32 is alyways 4 bytes)
        send_data += " 00 04"
        
        #Fingerprint (TODO)
        send_data += " " + crc_hex



        _logger.error(send_data)
        
        #Ok now convert it back so we can send it
        return send_data.replace(" ","").decode('hex')
    
    def rtp_server_listener(self, port, message_bank_duration):
        
        
        #First Message we get is the conectivity test (STUN Binding Request User)
        
        #Second is DTLSv1.2 or more specifically dtls-strp
        
        #3rd is the stream with the G722 Audio payload        
        
        _logger.error("Start RTP Listening on Port " + str(port) )
                        
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.bind(('', port));

        start = time.time()
        stage = "STUN"
        hex_string = ""
        
        
        #Code is easier to understand if we start at 1 rather then 0...
        hex_data = ['FF']
        
        while time.time() < start + message_bank_duration:
            data, addr = serversocket.recvfrom(2048)

            #Convert to hex so we can human interpret each byte
            for rtp_char in data:
                hex_format = "{0:02x}".format(ord(rtp_char))
                hex_data.append(hex_format)
                hex_string += hex_format + " "
 
            _logger.error(addr)
            _logger.error("HEX DATA: " + hex_string)            
            
            if stage is "STUN":
                send_data = self.rtp_stun_listener(hex_data, addr)
                serversocket.sendto(send_data, addr )                
        
        #End the call and do any post call processing
        with api.Environment.manage():
            # As this function is in a new thread, i need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))

            self.close_message_bank()

            #Have to manually commit the new cursor?
            self.env.cr.commit()
        
            self._cr.close()

        _logger.error("END MESSAGE BANK")
                
    def start_rtc_listener(self, port, mode):
    
        message_bank_duration = self.env['ir.values'].get_default('voip.settings', 'message_bank_duration')
                
        #Start a new thread so you don't block the main Odoo thread
        if mode is "RTP":
            rtc_listener_starter = threading.Thread(target=self.rtp_server_listener, args=(port,message_bank_duration,))
            rtc_listener_starter.start()
        #elif mode is "RTCP":
        #    For now we don't use RTCP...
        #    rtc_listener_starter = threading.Thread(target=self.rtcp_server_listener, args=(port,message_bank_duration,))
        #    rtc_listener_starter.start()
 
class VoipCallClient(models.Model):

    _name = "voip.call.client"
    
    vc_id = fields.Many2one('voip.call', string="VOIP Call")
    partner_id = fields.Many2one('res.partner', string="Partner")
    name = fields.Char(string="Name", help="Can be a number if the client is from outside the system")
    state = fields.Selection([('invited','Invited'),('joined','joined'),('media_access','Media Access')], string="State", default="invited")
    sdp = fields.Char(string="SDP")
    sip_invite = fields.Char(string="SIP INVITE Message")
    sip_addr = fields.Char(string="Address")
    sip_addr_host = fields.Char(string="SIP Address Host")
    sip_addr_port = fields.Char(string="SIP Address Port")