from Cryptodome.Cipher import AES
from ecdsa import ECDH, SECP256k1
from requests.auth import HTTPBasicAuth
from django.conf import settings
import base64
import json
import os
import requests


def encrypt(key, msg, nonce):
    '''key hex string; msg string; nonce 12bit bytes'''
    aes_cipher = AES.new(bytes.fromhex(key), AES.MODE_GCM, nonce=nonce)
    msg = str.encode(msg)
    ciphertext, auth_tag = aes_cipher.encrypt_and_digest(msg)
    return base64.b64encode(ciphertext + auth_tag).decode()

def decrypt(key, data, nonce):
    data = base64.b64decode(data)
    ciphertext = data[:-16]
    auth_tag = data[-16:]
    aesCipher = AES.new(bytes.fromhex(key), AES.MODE_GCM, nonce=nonce)
    plaintext = aesCipher.decrypt(ciphertext)
    return plaintext.decode()


# Exception class to hold wallet call error data
class WalletError(Exception):
    def __init__(self, method, params, code, reason):
        self.method = method
        self.params = params
        self.code = code    # may be None, not all errors have a code
        self.reason = reason
        super().__init__(self.reason)

    def __str__(self):
        return f'Calling {self.method} with params {self.params} failed with error code {self.code} because: {self.reason}'


# Grin Wallet Owner API V3
class WalletV3:
    def __init__(self):
        wallet_settings = settings.WALLET_API
        self.api_url = wallet_settings['URL']
        self.api_user = wallet_settings['USERNAME']
        self.owner_api_secret = wallet_settings['OWNER_API_SECRET']
        # get random point on secp256k1, will be used to derive share_secret
        # from the returned secret
        self.ecdh = ECDH(curve=SECP256k1)
        self.public_key = self.ecdh.generate_private_key().to_string('compressed').hex()
        # share_secret is ECDH shared secret, we calculate it when we initialize
        # secure api
        self.share_secret = ''
        # when you open a wallet, you get a token which you need to pass with
        # each call
        self.token = ''

    @classmethod
    def get_wallet_api(cls, wallet_name='default'):
        # initialize wallet api, that's basically WalletV3()
        wallet_api = cls()
        # call init_secure_api to get the shared key
        wallet_api.init_secure_api()
        # we open the wallet so we get the token to make api calls on that wallet
        wallet_api.open_wallet(wallet_name)
        return wallet_api

    def post(self, method, params):
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params
        }
        response = requests.post(
                self.api_url, json=payload, 
                auth=(self.api_user, self.owner_api_secret))
        if response.status_code >= 300 or response.status_code < 200:
            # Requests-level error
            raise WalletError(method, params, response.status_code, response.reason)
        response_json = response.json()
        if "error" in response_json:
            # One version of a wallet error
            raise WalletError(method, params, response_json["error"]["code"], response_json["error"]["message"])
        if "Err" in response_json:
            # Another version of a wallet error
            raise WalletError(method, params, None, response_json["result"]["Err"])
        return response_json

    def post_encrypted(self, method, params):
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params
        }
        nonce = os.urandom(12)
        encrypted = encrypt(self.share_secret, json.dumps(payload), nonce)
        resp = self.post('encrypted_request_v3', {
            'nonce': nonce.hex(),
            'body_enc': encrypted
        })
        nonce2 = bytes.fromhex(resp['result']['Ok']['nonce'])
        encrypted2 = resp['result']['Ok']['body_enc']
        response_json = json.loads(decrypt(self.share_secret, encrypted2, nonce2))
        if "error" in response_json:
            # One version of a wallet error
            raise WalletError(method, params, response_json["error"]["code"], response_json["error"]["message"])
        if "Err" in response_json:
            # Another version of a wallet error
            raise WalletError(method, params, None, response_json["result"]["Err"])
        return response_json

    ##
    # The API: https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.init_secure_api
    def init_secure_api(self):
        resp = self.post('init_secure_api', {'ecdh_pubkey': self.public_key})
        remote_pubkey = resp['result']['Ok']
        # calculate shared ECDH secret based on the returned pubkey
        self.ecdh.load_received_public_key_bytes(bytes.fromhex(remote_pubkey))
        self.share_secret = self.ecdh.generate_sharedsecret_bytes().hex()
        return self.share_secret

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.open_wallet
    def open_wallet(self, name='default'):
        params = {
            'name': name,
            'password': settings.WALLET_API['PASSWORD'],
        }
        resp = self.post_encrypted('open_wallet', params)
        self.token = resp['result']['Ok']
        return self.token

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.node_height
    def node_height(self):
        params = { 'token': self.token }
        resp = self.post_encrypted('node_height', params)
        return resp['result']['Ok']

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.retrieve_txs
    def retrieve_txs(self, tx_id=None, tx_slate_id=None, refresh=True):
        params = {
            'token': self.token,
            'refresh_from_node': refresh,
            'tx_id': tx_id,
            'tx_slate_id': tx_slate_id,
        }
        resp = self.post_encrypted('retrieve_txs', params)
        if refresh and not resp["result"]["Ok"][0]:
            # We requested refresh but data was not successfully refreshed
            raise WalletError("retrieve_outputs", params, None, "Failed to refresh data from the node")
        return resp["result"]["Ok"][1]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.retrieve_outputs
    def retrieve_outputs(self, include_spent=False, tx_id=None, refresh=True):
        params = {
            'token': self.token,
            'include_spent': include_spent,
            'refresh_from_node': refresh,
            'tx_id': tx_id,
        }
        resp = self.post_encrypted('retrieve_outputs', params)
        if refresh and not resp["result"]["Ok"][0]:
            # We requested refresh but data was not successfully refreshed
            raise WalletError("retrieve_outputs", params, None, "Failed to refresh data from the node")
        return resp["result"]["Ok"][1]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.retrieve_summary_info
    def retrieve_summary_info(self, minimum_confirmations=1, refresh=True):
        params = {
            'token': self.token,
            'minimum_confirmations': minimum_confirmations,
            'refresh_from_node': refresh,
        }
        resp = self.post_encrypted('retrieve_summary_info', params)
        if refresh and not resp["result"]["Ok"][0]:
            # We requested refresh but data was not successfully refreshed
            raise WalletError("retrieve_outputs", params, None, "Failed to refresh data from the node")
        return resp["result"]["Ok"][1]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.cancel_tx
    def cancel_tx(self, tx_id=None, tx_slate_id=None, refresh=True):
        params = {
            'token': self.token,
            'tx_id': tx_id,
            'tx_slate_id': tx_slate_id,
        }
        resp = self.post_encrypted('cancel_tx', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.scan
    def scan(self, start_height=0, delete_unconfirmed=False):
        params = {
            'token': self.token,
            'start_height': start_height,
            'delete_unconfirmed': delete_unconfirmed,
        }
        resp = self.post_encrypted('scan', params)
        return True
    
    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.finalize_tx
    def finalize_tx(self, slate):
        params = {
            'token': self.token,
            'slate': slate,
        }
        resp = self.post_encrypted('finalize_tx', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.get_stored_tx
    def get_stored_tx(self, id=None, slate_id=None):
        params = {
            'token': self.token,
            'id': id,
            'slate_id': slate_id,
        }
        resp = self.post_encrypted('get_stored_tx', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.init_send_tx
    def init_send_tx(self, args):
        params = {
            'token': self.token,
            'args': args,
        }
        resp = self.post_encrypted('init_send_tx', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.issue_invoice_tx
    def issue_invoice_tx(self, args):
        params = {
            'token': self.token,
            'args': args,
        }
        resp = self.post_encrypted('issue_invoice_tx', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.post_tx
    def post_tx(self, slate, fluff=False):
        params = {
            'token': self.token,
            'slate': slate,
            'fluff': fluff,
        }
        resp = self.post_encrypted('post_tx', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.process_invoice_tx
    def process_invoice_tx(self, slate, args):
        params = {
            'token': self.token,
            'slate': slate,
            'args': args,
        }
        resp = self.post_encrypted('process_invoice_tx', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.tx_lock_outputs
    def tx_lock_outputs(self, slate):
        params = {
            'token': self.token,
            'slate': slate,
        }
        resp = self.post_encrypted('tx_lock_outputs', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.accounts
    def accounts(self):
        params = {
            'token': self.token,
        }
        resp = self.post_encrypted('accounts', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.change_password
    def change_password(self, old, new, name):
        params = {
            'name': name,
            'old': old,
            'new': new,
        }
        resp = self.post_encrypted('change_password', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.close_wallet
    def close_wallet(self, name=None):
        params = {
            'name': name,
        }
        resp = self.post_encrypted('close_wallet', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.create_account_path
    def create_account_path(self, label):
        params = {
            'token': self.token,
            'label': label,
        }
        resp = self.post_encrypted('create_account_path', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.create_config
    def create_config(self, chain_type="Mainnet", wallet_config=None, logging_config=None, tor_config=None):
        params = {
            'chain_type': chain_type,
            'wallet_config': wallet_config,
            'logging_config': logging_config,
            'tor_config': tor_config,
        }
        resp = self.post_encrypted('create_config', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.create_slatepack_message
    def create_slatepack_message(self, slate, recipients, sender_index=None):
        params = {
            'token': self.token,
            'slate': slate,
            'recipients': recipients,
            'sender_index': sender_index,
        }
        resp = self.post_encrypted('create_slatepack_message', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.delete_wallet
    def delete_wallet(self, name=None):
        params = {
            'name': name,
        }
        resp = self.post_encrypted('delete_wallet', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.get_mnemonic
    def get_mnemonic(self, password, name=None):
        params = {
            'name': name,
            'password': password,
        }
        resp = self.post_encrypted('get_mnemonic', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.get_slatepack_address
    def get_slatepack_address(self, derivation_index=0):
        params = {
            'token': self.token,
            'derivation_index': derivation_index,
        }
        resp = self.post_encrypted('get_slatepack_address', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.get_slatepack_secret_key
    def get_slatepack_secret_key(self, derivation_index=0):
        params = {
            'token': self.token,
            'derivation_index': derivation_index,
        }
        resp = self.post_encrypted('get_slatepack_secret_key', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.get_top_level_directory
    def get_top_level_directory(self):
        params = {}
        resp = self.post_encrypted('get_top_level_directory', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.get_updater_messages
    def get_updater_messages(self, count=1):
        params = {
            'count': count,
        }
        resp = self.post_encrypted('get_updater_messages', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.retrieve_payment_proof
    def retrieve_payment_proof(self, refresh=True, tx_id=None, tx_slate_id=None):
        params = {
            'token': self.token,
            'refresh_from_node': refresh_from_node,
            'tx_id': tx_id,
            'tx_slate_id': tx_slate_id,
        }
        resp = self.post_encrypted('retrieve_payment_proof', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.set_active_account
    def set_active_account(self, label):
        params = {
            'token': self.token,
            'label': label,
        }
        resp = self.post_encrypted('set_active_account', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.set_top_level_directory
    def set_top_level_directory(self, dir):
        params = {
            'dir': dir,
        }
        resp = self.post_encrypted('set_top_level_directory', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.set_tor_config
    def set_tor_config(self, tor_config=None):
        params = {
            'tor_config': tor_config,
        }
        resp = self.post_encrypted('set_tor_config', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.slate_from_slatepack_message
    def slate_from_slatepack_message(self, message, secret_indices):
        params = {
            'token': self.token,
            'message': message,
            'secret_indices': secret_indices,
        }
        resp = self.post_encrypted('slate_from_slatepack_message', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.start_updater
    def start_updater(self, frequency):
        params = {
            'token': self.token,
            'frequency': frequency,
        }
        resp = self.post_encrypted('start_updater', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.stop_updater
    def stop_updater(self):
        params = {}
        resp = self.post_encrypted('stop_updater', params)
        return True

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.verify_payment_proof
    def verify_payment_proof(self, proof):
        params = {
            'token': self.token,
            'proof': proof,
        }
        resp = self.post_encrypted('verify_payment_proof', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.create_wallet
    def create_wallet(self, password, name=None, mnemonic=None, mnemonic_length=0):
        params = {
            'password': password,
            'name': name,
            'mnemonic': mnemonic,
            'mnemonic_length=': mnemonic_length,
        }
        resp = self.post_encrypted('create_wallet', params)
        return resp["result"]["Ok"]

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.retrieve_outputs
    def contract_new(self, net_change, counterparty_addr, is_payjoin=True, num_participants=2):
        params = {
            'token': self.token,
            'args': {
                'setup_args': {
                    'net_change': net_change,
                    'num_participants': num_participants,
                    'early_lock': False,
                    'is_payjoin': is_payjoin,
                    'use_inputs': None,
                },
            },
        }
        resp = self.post_encrypted('contract_new', params)
        slate = resp["result"]["Ok"]
        return slate

    # https://docs.rs/grin_wallet_api/5.0.1/grin_wallet_api/trait.OwnerRpc.html#tymethod.retrieve_outputs
    def contract_sign(self, expected_net_change, slate, is_payjoin=True, num_participants=2):
        params = {
            'token': self.token,
            'slate': slate,
            'args': {
                'setup_args': {
                    'net_change': expected_net_change,
                    'num_participants': num_participants,
                    'early_lock': False,
                    'is_payjoin': is_payjoin,
                    'use_inputs': None,
                },
            },
        }
        resp = self.post_encrypted('contract_sign', params)
        slate = resp["result"]["Ok"]
        return slate
