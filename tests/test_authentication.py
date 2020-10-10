"""Test the authentication module"""

from unittest import mock
from django import test
import firebase_admin

from drf_firebase_token_auth.authentication import FirebaseTokenAuthentication


class FirebaseTokenAuthTestCase(test.TestCase):
    """Test the FirebaseTokenAuth class"""
    def setUp(self):
        with mock.patch('drf_firebase_token_auth.authentication.firebase_admin',
                        spec=True) as mock_firebase_admin:
            self.firebase_token_auth = FirebaseTokenAuthentication()

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
