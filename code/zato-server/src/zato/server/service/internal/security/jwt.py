# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from contextlib import closing
from httplib import BAD_REQUEST
from traceback import format_exc
from uuid import uuid4

# Cryptography
from cryptography.fernet import Fernet

# Zato
from zato.common import SEC_DEF_TYPE
from zato.common.broker_message import SECURITY
from zato.common.odb.model import Cluster, JWT
from zato.common.odb.query import jwt_list
from zato.server.connection.http_soap import Unauthorized
from zato.server.jwt import JWT as JWTBackend
from zato.server.service import Integer
from zato.server.service.internal import AdminService, AdminSIO, ChangePasswordBase, GetListAdminSIO

# ################################################################################################################################

class GetList(AdminService):
    """ Returns the list of JWT definitions available.
    """
    _filter_by = JWT.name,

    class SimpleIO(GetListAdminSIO):
        request_elem = 'zato_security_jwt_get_list_request'
        response_elem = 'zato_security_jwt_get_list_response'
        input_required = ('cluster_id',)
        output_required = ('id', 'name', 'is_active', 'username', Integer('ttl'))

    def get_data(self, session):
        return self._search(jwt_list, session, self.request.input.cluster_id, None, False)

    def handle(self):
        with closing(self.odb.session()) as session:
            self.response.payload[:] = self.get_data(session)

# ################################################################################################################################

class Create(AdminService):
    """ Creates a new JWT definition.
    """
    class SimpleIO(AdminSIO):
        request_elem = 'zato_security_jwt_create_request'
        response_elem = 'zato_security_jwt_create_response'
        input_required = ('cluster_id', 'name', 'is_active', 'username', Integer('ttl'))
        output_required = ('id', 'name')

    def handle(self):
        input = self.request.input
        input.password = uuid4().hex
        input.secret = Fernet.generate_key()

        with closing(self.odb.session()) as session:
            try:

                # Let's see if we already have a definition of that name before committing
                # any stuff into the database.
                existing_one = session.query(JWT).\
                    filter(Cluster.id==input.cluster_id).\
                    filter(JWT.name==input.name).first()

                if existing_one:
                    raise Exception('JWT definition `{}` already exists on this cluster'.format(input.name))

                item = JWT()
                item.name = input.name
                item.is_active = input.is_active
                item.username = input.username
                item.password = input.password
                item.secret = input.secret
                item.ttl = input.ttl
                item.cluster_id = input.cluster_id

                session.add(item)
                session.commit()

            except Exception, e:
                self.logger.error('Could not create a JWT definition, e:`%s`', format_exc(e))
                session.rollback()

                raise
            else:
                input.id = item.id
                input.action = SECURITY.JWT_CREATE.value
                input.sec_type = SEC_DEF_TYPE.JWT
                self.broker_client.publish(input)

            self.response.payload.id = item.id
            self.response.payload.name = item.name

# ################################################################################################################################

class Edit(AdminService):
    """ Updates a JWT definition.
    """
    class SimpleIO(AdminSIO):
        request_elem = 'zato_security_jwt_edit_request'
        response_elem = 'zato_security_jwt_edit_response'
        input_required = ('id', 'cluster_id', 'name', 'is_active', 'username', Integer('ttl'))
        output_required = ('id', 'name')

    def handle(self):
        input = self.request.input
        with closing(self.odb.session()) as session:
            try:
                existing_one = session.query(JWT).\
                    filter(Cluster.id==input.cluster_id).\
                    filter(JWT.name==input.name).\
                    filter(JWT.id!=input.id).\
                    first()

                if existing_one:
                    raise Exception('JWT definition `{}` already exists on this cluster'.format(input.name))

                item = session.query(JWT).filter_by(id=input.id).one()
                old_name = item.name

                item.name = input.name
                item.is_active = input.is_active
                item.username = input.username
                item.ttl = input.ttl
                item.cluster_id = input.cluster_id

                session.add(item)
                session.commit()

            except Exception, e:
                self.logger.error('Could not update the JWT definition, e:`%s`', format_exc(e))
                session.rollback()

                raise
            else:
                input.action = SECURITY.JWT_EDIT.value
                input.old_name = old_name
                input.sec_type = SEC_DEF_TYPE.JWT
                self.broker_client.publish(input)

                self.response.payload.id = item.id
                self.response.payload.name = item.name

# ################################################################################################################################

class ChangePassword(ChangePasswordBase):
    """ Changes the password of a JWT definition.
    """
    password_required = False

    class SimpleIO(ChangePasswordBase.SimpleIO):
        request_elem = 'zato_security_jwt_change_password_request'
        response_elem = 'zato_security_jwt_change_password_response'

    def handle(self):
        def _auth(instance, password):
            instance.password = password

        return self._handle(JWT, _auth, SECURITY.JWT_CHANGE_PASSWORD.value)

# ################################################################################################################################

class Delete(AdminService):
    """ Deletes a JWT definition.
    """
    class SimpleIO(AdminSIO):
        request_elem = 'zato_security_jwt_delete_request'
        response_elem = 'zato_security_jwt_delete_response'
        input_required = ('id',)

    def handle(self):
        with closing(self.odb.session()) as session:
            try:
                auth = session.query(JWT).\
                    filter(JWT.id==self.request.input.id).\
                    one()

                session.delete(auth)
                session.commit()
            except Exception, e:
                self.logger.error('Could not delete the JWT definition, e:`%s`', format_exc(e))
                session.rollback()

                raise
            else:
                self.request.input.action = SECURITY.JWT_DELETE.value
                self.request.input.name = auth.name
                self.broker_client.publish(self.request.input)

# ################################################################################################################################

class LogIn(AdminService):
    """ Logs user into using JWT-backed credentials and returns a new token if credentials were correct.
    """
    class SimpleIO(AdminSIO):
        input_required = ('username', 'password')
        response_elem = 'zato_security_jwt_log_in_response'
        output_optional = ('token',)

    def handle(self):
        token = JWTBackend(self.kvdb, self.odb, self.server.fs_server_config.misc.jwt_secret).authenticate(
            self.request.input.username, self.request.input.password)

        if token:
            self.response.payload.token = token
            self.response.headers['Authorization'] = token

        else:
            raise Unauthorized(self.cid, 'Invalid username or password', 'jwt')

# ################################################################################################################################

class LogOut(AdminService):
    """ Logs a user out of an existing JWT token.
    """
    class SimpleIO(AdminSIO):
        response_elem = 'zato_security_jwt_log_out_response'
        output_optional = ('result',)

    def handle(self):
        token = self.wsgi_environ.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')

        if not token:
            self.response.status_code = BAD_REQUEST
            self.response.payload.result = 'No JWT found'

        try:
            JWTBackend(self.kvdb, self.odb, self.server.fs_server_config.misc.jwt_secret).delete(token)
        except Exception, e:
            self.logger.warn(format_exc(e))
            self.response.status_code = BAD_REQUEST
            self.response.payload.result = 'Token could not be deleted'

# ################################################################################################################################

class CreateToken(AdminService):
    """ Creates token on behalf of a given user without requiring that user to provide a password. Useful when another application
    obtains the token in lieu the user directly.
    """
    class SimpleIO(AdminSIO):
        input_required = ('username',)
        response_elem = 'zato_security_jwt_create_token_response'
        output_optional = ('token',)

    def handle(self):
        pass

# ################################################################################################################################