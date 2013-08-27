# -*- coding: utf-8 -*-

"""
Copyright (C) 2013 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
from contextlib import closing
from json import dumps, loads

# Zato
from zato.server.service import AsIs
from zato.server.service.internal import AdminService
from zato.server.service.internal.pattern.delivery import target_def_class

class GetList(AdminService):
    """ Returns a batch of instances that are in the in-doubt state.
    """
    class SimpleIO(object):
        request_elem = 'zato_pattern_delivery_in_doubt_get_list_request'
        response_elem = 'zato_pattern_delivery_in_doubt_get_list_response'
        input_required = ('def_name',)
        input_optional = ('batch_size', 'current_batch', 'start', 'stop')
        output_required = ('def_name', 'target_type', AsIs('task_id'), 'creation_time_utc', 'in_doubt_created_at_utc', 
            'source_count', 'target_count', 'resubmit_count', 'retry_repeats', 'check_after', 'retry_seconds')
        output_repeated = True

    def handle(self):
        input = self.request.input
        input['batch_size'] = input['batch_size'] or 25
        input['current_batch'] = input['current_batch'] or 1
        
        self.response.payload[:] = self.delivery_store.get_in_doubt_instance_list(self.server.cluster_id, input)

class GetDetails(AdminService):
    """ Returns details of a particular delivery definition that is in-doubt.
    """
    class SimpleIO(object):
        request_elem = 'zato_pattern_delivery_in_doubt_get_list_request'
        response_elem = 'zato_pattern_delivery_in_doubt_get_list_response'
        input_required = (AsIs('task_id'),)
        input_optional = ('batch_size', 'current_batch', 'start', 'stop')
        output_required = ('def_name', 'target_type', AsIs('task_id'), 'creation_time_utc', 'in_doubt_created_at_utc', 
            'source_count', 'target_count', 'resubmit_count', 'retry_repeats', 'check_after', 'retry_seconds')
        output_optional = ('payload', 'args', 'kwargs', 'target')
        output_repeated = True

    def handle(self):
        with closing(self.odb.session()) as session:
            instance = session.merge(self.delivery_store.get_delivery(self.request.input.task_id))
            self.response.payload = self.delivery_store.get_delivery_instance(self.request.input.task_id, instance.definition.__class__)
