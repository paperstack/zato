# -*- coding: utf-8 -*-

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals


# Zato
from zato.zmq_ import Base

# ################################################################################################################################

class Simple(Base):
    """ An outgoing ZeroMQ connection of a type other than Majordomo (MDP).
    """
    def _start(self):
        super(Simple, self)._start()
        self.init_simple_socket()

    def send(self, msg):
        self.impl.send_string(msg)
