from django.conf import settings

import json
import requests


class NodeError(Exception):
    def __init__(self, method, params, code, reason):
        self.method = method
        self.params = params
        self.code = code    # may be None, not all errors have a code
        self.reason = reason
        super().__init__(self.reason)

    def __str__(self):
        return f'Calling node foreign api {self.method} with params {self.params} failed with error code {self.code} because: {self.reason}'


class NodeV2API:
    def __init__(self):
        node_settings = settings.NODE_API
        self.foreign_api_url = node_settings['URL']
        self.foreign_api_user = node_settings['USERNAME']
        self.foreign_api_password = node_settings['FOREIGN_API_SECRET']
        

    def post(self, method, params):
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params
        }

        response = requests.post(
                self.foreign_api_url, json=payload, 
                auth=(self.foreign_api_user, self.foreign_api_password))
        if response.status_code >= 300 or response.status_code < 200:
            # Requests-level error
            raise NodeError(method, params, response.status_code, response.reason)
        response_json = response.json()

        # https://github.com/mimblewimble/grin-rfcs/blob/master/text/0007-node-api-v2.md#errors
        if "error" in response_json:
            # One version of a node error
            raise NodeError(method, params, response_json["error"]["code"], response_json["error"]["message"])
        if "Err" in response_json:
            # Another version of a node error
            raise NodeError(method, params, None, response_json["result"]["Err"])
        return response_json

    def get_tip(self):
        resp = self.post('get_tip', [])
        return resp["result"]["Ok"]
    
    def get_kernel(self, excess, min_height=None, max_height=None):
        resp = self.post('get_kernel', [excess, min_height, max_height])
        return resp["result"]["Ok"]
