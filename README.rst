Firebase Token Authentication for Django Rest Framework
=======================================================

Inspired by `garyburgmann/drf-firebase-auth <https://github.com/garyburgmann/drf-firebase-auth>`_
and based on `Rest Framework's TokenAuthentication <https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication>`_,
``drf-firebase-token-auth`` should be just what you need to enable client
authentication using `Firebase Authentication <https://firebase.google.com/docs/auth>`_.

Installation
------------
#. Install the pip package:

   .. code-block:: bash

    $ pip install drf-firebase-token-auth

#. Add the application to your project's ``INSTALLED_APPS``:

   .. code-block:: python

    # settings.py
    INSTALLED_APS = [
        ...
        'drf-firebase-token-auth',
    ]

#. Add ``FirebaseTokenAuthentication`` to Rest Framework's list of default
   authentication classes:

   .. code-block:: python

    # settings.py
    REST_FRAMEWORK = {
        ...
        'DEFAULT_AUTHENTICATION_CLASSES': [
            ...
            'drf_firebase_token_auth.authentication.FirebaseTokenAuthentication',
        ]
    }


   *Note*: It's perfectly fine to keep other authentication classes as well.
   For example, you may want to keep ``rest_framework.authentication.SessionAuthentication``
   to allow access to the browsable API for local users with password.

#. Configure the application:

   .. code-block:: python

    # settings.py
    DRF_FIREBASE_TOKEN_AUTH = {
        # REQUIRED SETTINGS:

        # Path to JSON file with firebase secrets
        'FIREBASE_SERVICE_ACCOUNT_KEY_FILE_PATH': r'/mnt/c/Users/ronhe/Google Drive/ProgramsData/WizWot/paywiz-c4b4f-firebase-adminsdk-ekbjf-9b7776879a.json',


        # OPTIONAL SETTINGS:

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

#. Migrate:

   .. code-block:: bash

    $ python manage.py migrate drf-firebase-token-auth

