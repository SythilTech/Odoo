# -*- coding: utf-8 -*-
import time

def generate_sdp(self, ip, audio_port, rtp_profiles, session_description=" "):

    sdp = ""

    #Protocol Version ("v=") https://tools.ietf.org/html/rfc4566#section-5.1 (always 0 for us)
    sdp += "v=0\r\n"

    #Origin ("o=") https://tools.ietf.org/html/rfc4566#section-5.2
    username = "-"
    sess_id = int(time.time())
    sess_version = 0
    nettype = "IN"
    addrtype = "IP4"
    sdp += "o=" + username + " " + str(sess_id) + " " + str(sess_version) + " " + nettype + " " + addrtype + " " + ip + "\r\n"

    #Session Name ("s=") https://tools.ietf.org/html/rfc4566#section-5.3
    sdp += "s=" + session_description + "\r\n"

    #Connection Information ("c=") https://tools.ietf.org/html/rfc4566#section-5.7
    sdp += "c=" + nettype + " " + addrtype + " " + ip + "\r\n"

    #Timing ("t=") https://tools.ietf.org/html/rfc4566#section-5.9
    sdp += "t=0 0\r\n"

    #Media Descriptions ("m=") https://tools.ietf.org/html/rfc4566#section-5.14
    sdp += "m=audio " + str(audio_port) + " RTP/AVP"
    for rtp_profile in rtp_profiles:
        sdp += " " + str(rtp_profile)
    sdp += "\r\n"

    sdp += "a=sendrecv\r\n"

    return sdp