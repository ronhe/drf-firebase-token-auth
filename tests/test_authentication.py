"""Test the authentication module"""

from unittest import mock
from django import test
import firebase_admin
from firebase_admin import auth as firebase_auth
from django.contrib import auth

from drf_firebase_token_auth import models
from drf_firebase_token_auth.authentication import FirebaseTokenAuthentication


class FirebaseTokenAuthTestCase(test.TestCase):
    """Test the FirebaseTokenAuth class"""
    def setUp(self):
        with mock.patch('drf_firebase_token_auth.authentication.firebase_admin',
                        spec=True) as mock_firebase_admin:
            self.fb_token_auth = FirebaseTokenAuthentication()

        self.User = auth.get_user_model()

    def test_extract_email_from_firebase_user_no_email(self):
        mock_fb_user = mock.MagicMock(spec=firebase_admin.auth.UserRecord)
        mock_fb_user.email = None
        self.assertEqual(
            None,
            FirebaseTokenAuthentication._extract_email_from_firebase_user(
                mock_fb_user
            )
        )

    def test_extract_email_from_firebase_user_verified_email(self):
        mock_fb_user = mock.MagicMock(spec=firebase_admin.auth.UserRecord)
        email = "a@b.com"
        mock_fb_user.email = email
        mock_fb_user.email_verified = True
        self.assertEqual(
            email,
            FirebaseTokenAuthentication._extract_email_from_firebase_user(
                mock_fb_user
            )
        )

    @mock.patch('drf_firebase_token_auth.authentication.firebase_auth',
                spec=firebase_auth)
    def test_authenticate_firebase_user(self, mock_firebase_auth):
        uid = '1234'
        token ='abcd'
        mock_firebase_auth.verify_id_token.return_value = {'uid': uid}
        self.assertEqual(
            mock_firebase_auth.get_user(
                token,
                app=self.fb_token_auth._firebase_app,
                check_revoked=True
            ),
            self.fb_token_auth.authenticate_firebase_user(token)
        )

    def test_get_local_user(self):
        uid = '1234'
        username = 'user'
        user = self.User.objects.create(username=username)
        models.FirebaseUser.objects.create(uid=uid, user=user)
        mock_fb_user = mock.MagicMock(spec=firebase_auth.UserRecord)
        mock_fb_user.uid = uid

        self.assertEqual(
            user,
            self.fb_token_auth.get_local_user(mock_fb_user)
        )

    def test_get_local_user_email_match(self):
        uid = '1234'
        username = 'user'
        email = "a@b.com"
        user = self.User.objects.create(username=username, email=email)

        mock_fb_user = mock.MagicMock(spec=firebase_auth.UserRecord)
        mock_fb_user.uid = uid
        mock_fb_user.email = email

        self.assertEqual(
            user,
            self.fb_token_auth.get_local_user(mock_fb_user)
        )

    def test_create_local_user(self):
        mock_fb_user = mock.MagicMock(spec=firebase_auth.UserRecord)
        mock_fb_user.uid = '1234'
        mock_fb_user.email = 'a@b.com'
        mock_fb_user.email_verified = True
        mock_fb_user.display_name = 'John Doe'

        user = self.fb_token_auth.create_local_user(mock_fb_user)
        self.assertEqual(user.email, mock_fb_user.email)
        self.assertEqual(user.username, mock_fb_user.email)
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')

    def test_get_or_create_local_firebase_user_create(self):
        mock_fb_user = mock.MagicMock(spec=firebase_auth.UserRecord)
        mock_fb_user.uid = '1234'
        user = self.User.objects.create(username='username')

        fb_user = self.fb_token_auth.get_or_create_local_firebase_user(
            mock_fb_user,
            user
        )

        self.assertEqual(fb_user.uid, mock_fb_user.uid)
        self.assertEqual(fb_user.user, user)

    def test_get_or_create_local_firebase_user_get(self):
        user = self.User.objects.create(username='username')
        fb_user = models.FirebaseUser.objects.create(uid="1234", user=user)

        self.assertEqual(
            self.fb_token_auth.get_or_create_local_firebase_user(
                fb_user,
                user
            ),
            fb_user
        )

    def test_authenticate_credentials_local_user_exists(self):
        token = '1234'
        mock_local_user = mock.MagicMock(spec=self.User)
        mock_fb_user = mock.MagicMock(spec=firebase_auth.UserRecord)
        mock_local_fb_user = mock.MagicMock(spec=models.FirebaseUser)

        with mock.patch.object(
                self.fb_token_auth,
                'authenticate_firebase_user',
                spec=self.fb_token_auth.authenticate_firebase_user,
                return_value=mock_fb_user,
        ) as mock_authenticate_firebase_user, \
                mock.patch.object(
                    self.fb_token_auth,
                    'get_local_user',
                    spec=self.fb_token_auth.get_local_user,
                    return_value=mock_local_user,
                ) as mock_get_local_user, \
                mock.patch.object(
                    self.fb_token_auth,
                    'get_or_create_local_firebase_user',
                    spec=self.fb_token_auth.get_or_create_local_firebase_user,
                    return_value=mock_local_fb_user,
                ) as mock_get_or_create_local_firebase_user:
            
            self.assertEqual(
                self.fb_token_auth.authenticate_credentials(token)[0],
                mock_local_user
            )

            mock_get_local_user.assert_called_with(mock_fb_user)

            mock_get_or_create_local_firebase_user.assert_called_with(
                firebase_user=mock_fb_user,
                local_user=mock_local_user,
            )

    def test_authenticate_credentials_local_user_does_not_exist(self):
        token = '1234'
        mock_local_user = mock.MagicMock(spec=self.User)
        mock_fb_user = mock.MagicMock(spec=firebase_auth.UserRecord)
        mock_local_fb_user = mock.MagicMock(spec=models.FirebaseUser)

        with mock.patch.object(
                self.fb_token_auth,
                'authenticate_firebase_user',
                spec=self.fb_token_auth.authenticate_firebase_user,
                return_value=mock_fb_user,
        ) as mock_authenticate_firebase_user, \
                mock.patch.object(
                    self.fb_token_auth,
                    'get_local_user',
                    spec=self.fb_token_auth.get_local_user,
                    side_effect=self.User.DoesNotExist(),
                ) as mock_get_local_user, \
                mock.patch.object(
                    self.fb_token_auth,
                    'create_local_user',
                    spec=self.fb_token_auth.create_local_user,
                    return_value=mock_local_user
                ) as mock_create_local_user, \
                mock.patch.object(
                    self.fb_token_auth,
                    'get_or_create_local_firebase_user',
                    spec=self.fb_token_auth.get_or_create_local_firebase_user,
                    return_value=mock_local_fb_user,
                ) as mock_get_or_create_local_firebase_user:
            self.assertEqual(
                self.fb_token_auth.authenticate_credentials(token)[0],
                mock_local_user
            )

            mock_get_local_user.assert_called_with(mock_fb_user)
            mock_create_local_user.assert_called_with(mock_fb_user)

            mock_get_or_create_local_firebase_user.assert_called_with(
                firebase_user=mock_fb_user,
                local_user=mock_local_user,
            )