# -*- coding: utf-8 -*-
import socket
import threading
import logging
_logger = logging.getLogger(__name__)

class SessionInitiationProtocol:

    def send_sip_invite(self):
    