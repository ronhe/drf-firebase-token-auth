"""Firebase token authentication classes"""

from typing import *
from django.contrib import auth
from django.utils import timezone
from rest_framework import authentication, exceptions
import firebase_admin
from firebase_admin import auth as firebase_auth

from .settings import api_settings
from . import models


FIREBASE_APP_NAME = 'drf_firebase_token_auth'

_User = auth.get_user_model()


class FirebaseTokenAuthentication(authentication.TokenAuthentication):
    """Firebase token authentication class"""
    keyword = api_settings.AUTH_HEADER_TOKEN_KEYWORD

    def __init__(self) -> None:
        try:
            self._firebase_app = firebase_admin.get_app(FIREBASE_APP_NAME)
        except ValueError:
            firebase_credentials = firebase_admin.credentials.Certificate(
                api_settings.FIREBASE_SERVICE_ACCOUNT_KEY_FILE_PATH
            )
            self._firebase_app = firebase_admin.initialize_app(
                firebase_credentials,
                name=FIREBASE_APP_NAME
            )

    @staticmethod
    def _extract_email_from_firebase_user(
            firebase_user: firebase_auth.UserRecord,
            ignore_unverified_email=api_settings.IGNORE_FIREBASE_UNVERIFIED_EMAIL,
    ) -> Union[str, None]:
        """Extract user email from a Firebase user.

        Args:
            firebase_user: A Firebase user.
            ignore_unverified_email: Is a verified email required.

        Returns:
            User's email address or None if not found.
        """
        if ignore_unverified_email:
            if firebase_user.email_verified and firebase_user.email:
                return firebase_user.email
            else:
                return None

        # Make best effort to extract an email address.
        emails = [firebase_user.email] if firebase_user else []
        emails += [data.email for data in firebase_user.provider_data if data.email]

        return emails[0] if emails else None

    def authenticate_firebase_user(self,
                                   token: str) -> firebase_auth.UserRecord:
        """Authenticate a Firebase user using a given token

        Args:
            token: A Firebase token.

        Returns:
            A firebase user
        """
        try:
            decoded_token = firebase_auth.verify_id_token(
                token,
                app=self._firebase_app,
                check_revoked=api_settings.VERIFY_FIREBASE_TOKEN_NOT_REVOKED
            )
        except ValueError:
            raise exceptions.AuthenticationFailed(
                'JWT was found to be invalid, or the App’s project ID cannot '
                'be determined.'
            )
        except (firebase_auth.InvalidIdTokenError,
                firebase_auth.ExpiredIdTokenError,
                firebase_auth.RevokedIdTokenError,
                firebase_auth.CertificateFetchError) as exc:
            if exc.code == 'ID_TOKEN_REVOKED':
                raise exceptions.AuthenticationFailed(
                    'Token revoked, inform the user to reauthenticate or '
                    'signOut().'
                )
            else:
                raise exceptions.AuthenticationFailed(
                    'Token is invalid.'
                )

        return firebase_auth.get_user(decoded_token['uid'],
                                      app=self._firebase_app)

    def get_local_user(self, firebase_user: firebase_auth.UserRecord) -> _User:
        """Get a local user from a Firebase user.

        Args:
            firebase_user: A Firebase user.

        Returns:
            A local user model object.

        Raises:
            User.DoesNotExist: Could not find a local user matching to the
                given Firebase user.
        """
        # Try getting from a local firebase user.
        try:
            return models.FirebaseUser.objects.select_related('user').\
                get(uid=firebase_user.uid).user
        except models.FirebaseUser.DoesNotExist:
            pass

        # Try getting user by email.
        email = self._extract_email_from_firebase_user(firebase_user)
        if email:
            try:
                return _User.objects.get(**{_User.EMAIL_FIELD: email})
            except _User.DoesNotExist:
                pass

        # Try getting user by uid, and let User.DoesNotExist raise if not found.
        return _User.objects.get(**{_User.USERNAME_FIELD: firebase_user.uid})

    def create_local_user(self,
                          firebase_user: firebase_auth.UserRecord) -> _User:
        """Create a local user for a given Firebase user

        Args:
            firebase_user: A Firebase user.

        Returns:
            The created local user model object.
        """
        email = self._extract_email_from_firebase_user(firebase_user)
        username = email if email else firebase_user.uid

        user = _User.objects.create_user(**{_User.USERNAME_FIELD: username})

        if email:
            user.email = email

        if firebase_user.display_name:
            words = firebase_user.display_name.split(' ')
            user.first_name = ' '.join(words[:-1])
            user.last_name = words[-1]

        user.save()
        return user

    @staticmethod
    def get_or_create_local_firebase_user(
            firebase_user: firebase_auth.UserRecord,
            local_user
    ) -> models.FirebaseUser:
        """Get or create a local firebase user.

        Args:
            firebase_user: A Firebase user.
            local_user: User model object.

        Returns:
            The created local Firebase user.
        """
        local_firebase_user, created = \
            models.FirebaseUser.objects.get_or_create(
                uid=firebase_user.uid,
                defaults={'user': local_user}
            )
        return local_firebase_user

    def authenticate_credentials(self, token: str) -> Tuple[_User, None]:
        """Authenticate the token against Firebase

        Args:
            token: Firebase authentication token.

        Returns:
            The local user matching the Firebase authenticated user.
        """
        # Authenticate the Firebase token.
        firebase_user = self.authenticate_firebase_user(token)

        # Get or create local user that matches the Firebase user.
        try:
            local_user = self.get_local_user(firebase_user)
        except _User.DoesNotExist:
            if api_settings.SHOULD_CREATE_LOCAL_USER:
                local_user = self.create_local_user(firebase_user)
            else:
                raise exceptions.AuthenticationFailed(
                    'User is not registered to the application.'
                )

        # Update user last login.
        local_user.last_login = timezone.now()
        local_user.save()

        # Get or create a local Firebase user.
        self.get_or_create_local_firebase_user(firebase_user=firebase_user,
                                               local_user=local_user)

        return local_user, None
