"""
OAuth 2.0 and OpenID Connect Authentication and Authorization Controller.
"""

from __future__ import absolute_import

import logging
import json
import requests

from galaxy import exceptions
from galaxy import web
from galaxy.web import url_for
from galaxy.webapps.base.controller import JSAppLauncher

log = logging.getLogger(__name__)


class OIDC(JSAppLauncher):

    @web.json
    @web.expose
    @web.require_login("list third-party identities")
    def index(self, trans, **kwargs):
        """
        GET /authnz/
            returns a list of third-party identities associated with the user.

        :type  trans: galaxy.web.framework.webapp.GalaxyWebTransaction
        :param trans: Galaxy web transaction.

        :param kwargs: empty dict

        :rtype: list of dicts
        :return: a list of third-party identities associated with the user account.
        """
        rtv = []
        for authnz in trans.user.social_auth:
            rtv.append({'id': trans.app.security.encode_id(authnz.id), 'provider': authnz.provider})
        return rtv

    @web.json
    @web.expose
    def login(self, trans, provider):
        if not trans.app.config.enable_oidc:
            msg = "Login to Galaxy using third-party identities is not enabled on this Galaxy instance."
            log.debug(msg)
            return trans.show_error_message(msg)
        success, message, redirect_uri = trans.app.authnz_manager.authenticate(provider, trans)
        if success:
            return {"redirect_uri": redirect_uri}
        else:
            raise exceptions.AuthenticationFailed(message)

    def get_cilogon_token(self, cilogon_code):
        cilogon_redirect_uri = "http://localhost:8080/authnz/cilogon/callback"
        cilogon_client_id = "" #testing, change later
        cilogon_client_secret = "" #testing, change later

        data = {"grant_type" : "authorization_code",
            "client_id" : cilogon_client_id,
            "client_secret" : cilogon_client_secret,
            "code" : cilogon_code,
            "redirect_uri" : cilogon_redirect_uri}
        
        #heads = {"Content-Type": "text/plain"}
        heads = {"Content-Type": "text/html; charset=utf-8"}
        print("\n\n\n\n\n\n\n\ndata: ", data)
        response = requests.post('https://cilogon.org/oauth2/token', json=data)#, headers=heads)

        print(response)
        print(response.text)
        print(response.status_code)
        print(response.content)

        #token_response = requests.post('https://cilogon.org/oauth2/userinfo', params={"access_token" : cilogon_access_token})
        #print(token_response)


    @web.expose
    def callback(self, trans, provider, **kwargs):
        if (provider == "cilogon"):
            self.get_cilogon_token(kwargs.get('code'))

        user = trans.user.username if trans.user is not None else 'anonymous'
        if not bool(kwargs):
            log.error("OIDC callback received no data for provider `{}` and user `{}`".format(provider, user))
            return trans.show_error_message(
                'Did not receive any information from the `{}` identity provider to complete user `{}` authentication '
                'flow. Please try again, and if the problem persists, contact the Galaxy instance admin. Also note '
                'that this endpoint is to receive authentication callbacks only, and should not be called/reached by '
                'a user.'.format(provider, user))
        if 'error' in kwargs:
            log.error("Error handling authentication callback from `{}` identity provider for user `{}` login request."
                      " Error message: {}".format(provider, user, kwargs.get('error', 'None')))
            return trans.show_error_message('Failed to handle authentication callback from {}. '
                                            'Please try again, and if the problem persists, contact '
                                            'the Galaxy instance admin'.format(provider))
        success, message, (redirect_url, user) = trans.app.authnz_manager.callback(provider,
                                                                                   kwargs['state'],
                                                                                   kwargs['code'],
                                                                                   trans,
                                                                                   login_redirect_url=url_for('/'))
        if success is False:
            return trans.show_error_message(message)
        user = user if user is not None else trans.user
        if user is None:
            return trans.show_error_message("An unknown error occurred when handling the callback from `{}` "
                                            "identity provider. Please try again, and if the problem persists, "
                                            "contact the Galaxy instance admin.".format(provider))
        trans.handle_user_login(user)
        return self.client(trans)

    @web.expose
    @web.require_login("authenticate against the selected identity provider")
    def disconnect(self, trans, provider, **kwargs):
        if trans.user is None:
            # Only logged in users are allowed here.
            return
        success, message, redirect_url = trans.app.authnz_manager.disconnect(provider,
                                                                             trans,
                                                                             disconnect_redirect_url=url_for('/'))
        if success is False:
            return trans.show_error_message(message)
        if redirect_url is None:
            redirect_url = url_for('/')
        return trans.response.send_redirect(redirect_url)