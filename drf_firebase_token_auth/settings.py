"""Settings for the drf_firebase_token_auth application"""

from django.conf import settings
from rest_framework.settings import APISettings


USER_SETTINGS = getattr(settings, 'DRF_FIREBASE_TOKEN_AUTH', None)

DEFAULTS = {
    # Path to JSON file with firebase secrets
    'FIREBASE_SERVICE_ACCOUNT_KEY_FILE_PATH': '',

    # Create new matching local user in db, if no match found.
    # Otherwise, Firebase user not matching a local user will not
    # be authenticated.
    'SHOULD_CREATE_LOCAL_USER': True,

    # Authentication header token keyword (usually 'Token', 'JWT' or 'Bearer')
    'AUTH_HEADER_TOKEN_KEYWORD': 'Token',

    # Verify that Firebase token has not been revoked.
    'VERIFY_FIREBASE_TOKEN_NOT_REVOKED': True,

    # Require that Firebase user email_verified is True.
    # If set to True, non verified email addresses from Firebase are ignored.
    'IGNORE_FIREBASE_UNVERIFIED_EMAIL': True,
}

# List of settings that may be in string import notation.
IMPORT_STRINGS = ()

api_settings = APISettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)
