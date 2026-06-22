import re
import passlib

from string import ascii_letters, digits

from odoo import tools

VERSION = '2'
BASE_URL = '/api/v{}'.format(VERSION)

REST_ROUTING_TYPE = 'rest'
JSON_MIMETYPE = 'application/json'

CONTENT_TYPE_HEADER_KEY = 'Content-Type'
CONTENT_TYPE_HEADER_VALUE = 'application/json; charset=utf-8'

TOKEN_INDEX = 10
KEY_CRYPT_CONTEXT = passlib.context.CryptContext(
    ['pbkdf2_sha512'], pbkdf2_sha512__rounds=6000,
)

GRANT_RESPONSE_MAP = {
    'authorization_code': ['code'],
    'implicit': ['token'],
}

UNICODE_ASCII_CHARACTERS = ascii_letters + digits

SAFE_URL_CHARS = set(
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ' 
    'abcdefghijklmnopqrstuvwxyz'
    '0123456789' '_.-' 
    '=&;:%+~,*@!()/?'
)

INVALID_HEX_PATTERN = re.compile(
    r'%[^0-9A-Fa-f]|%[0-9A-Fa-f][^0-9A-Fa-f]'
)

DBNAME_PATTERN = '^[a-zA-Z0-9][a-zA-Z0-9_.-]+$'

DOCS_SECURITY_GROUP = tools.config.get(
    'rest_docs_security_group', False
)
DOCS_CODEGEN_URL = tools.config.get(
    'rest_docs_codegen_url', 
    'https://generator3.swagger.io/api'
)

ACTIVE_BASIC_AUTHENTICATION = tools.config.get(
    'rest_authentication_basic', True
)
ACTIVE_OAUTH1_AUTHENTICATION = tools.config.get(
    'rest_authentication_oauth1', True
)
ACTIVE_OAUTH2_AUTHENTICATION = tools.config.get(
    'rest_authentication_oauth2', True
)

try:
    import oauthlib
except ImportError:
    ACTIVE_OAUTH1_AUTHENTICATION = False
    ACTIVE_OAUTH2_AUTHENTICATION = False

# TODO CONNECT TO VALIDATORS