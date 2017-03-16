# -*- coding: utf-8 -*-

"""
Copyright (C) 2017, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from contextlib import closing
from uuid import uuid4

# Zato
from zato.common.broker_message import DEFINITION
from zato.common.odb.model import ConnDefAMQP
from zato.common.odb.query import definition_amqp, definition_amqp_list
from zato.server.service.internal import AdminService, AdminSIO, ChangePasswordBase
from zato.server.service.meta import CreateEditMeta, DeleteMeta, GetListMeta

# ################################################################################################################################

elem = 'definition_amqp'
model = ConnDefAMQP
label = 'an AMQP definition'
broker_message = DEFINITION
broker_message_prefix = 'AMQP_'
list_func = definition_amqp_list
skip_input_params = ('password',)

# ################################################################################################################################

def broker_message_hook(self, input, instance, attrs, service_type):
    input.source_server = self.server.get_full_name()
    input.config_cid = 'definition.amqp.{}.{}.{}'.format(service_type, input.source_server, self.cid)

    if service_type == 'create_edit':
        with closing(self.odb.session()) as session:
            input.password = definition_amqp(session, instance.cluster_id, instance.id).password

# ################################################################################################################################

def instance_hook(self, input, instance, attrs):
    if 'create' in self.get_name().lower():
        instance.password = uuid4().hex

# ################################################################################################################################

class GetList(AdminService):
    name = 'zato.definition.amqp.get-list'
    _filter_by = ConnDefAMQP.name,
    __metaclass__ = GetListMeta

# ################################################################################################################################

class Create(AdminService):
    name = 'zato.definition.amqp.create'
    __metaclass__ = CreateEditMeta

# ################################################################################################################################

class Edit(AdminService):
    name = 'zato.definition.amqp.edit'
    __metaclass__ = CreateEditMeta

# ################################################################################################################################

class Delete(AdminService):
    name = 'zato.definition.amqp.delete'
    __metaclass__ = DeleteMeta

# ################################################################################################################################

class ChangePassword(ChangePasswordBase):
    """ Changes the password of an AMQP connection definition.
    """
    name = 'zato.definition.amqp.change-password'

    class SimpleIO(ChangePasswordBase.SimpleIO):
        request_elem = 'zato_definition_amqp_change_password_request'
        response_elem = 'zato_definition_amqp_change_password_response'

    def handle(self):
        def _auth(instance, password):
            instance.password = password

        return self._handle(ConnDefAMQP, _auth, DEFINITION.AMQP_CHANGE_PASSWORD.value)

# ################################################################################################################################

class GetByID(AdminService):
    """ Returns a particular AMQP definition by its ID.
    """
    name = 'zato.definition.amqp.get-by-id'

    class SimpleIO(AdminSIO):
        request_elem = 'zato_definition_amqp_get_by_id_request'
        response_elem = 'zato_definition_amqp_get_by_id_response'
        input_required = ('id', 'cluster_id')
        output_required = ('id', 'name', 'host', 'port', 'vhost', 'username', 'frame_max', 'heartbeat')

    def get_data(self, session):
        return definition_amqp(session, self.request.input.cluster_id, self.request.input.id)

    def handle(self):
        with closing(self.odb.session()) as session:
            self.response.payload = self.get_data(session)

# ################################################################################################################################
