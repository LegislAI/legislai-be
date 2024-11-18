import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from authentication.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestAuthentication(unittest.TestCase):
    @patch("api.oauth.google.authorize_redirect")
    def test_google_login_route(self, mock_authorize_redirect):
        """Test Google login route"""
        # Mock the authorize_redirect method
        mock_authorize_redirect.return_value = {"status": "redirect"}

        response = client.get("/auth/google/login")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "redirect"})

    @patch("api.oauth.google.authorize_access_token")
    @patch("api.oauth.google.get")
    @patch("api._get_user")
    @patch("api._create_user")
    @patch("api.create_access_token")
    @patch("api.create_refresh_token")
    async def test_google_callback_existing_user(
        self,
        mock_create_refresh_token,
        mock_create_access_token,
        mock_create_user,
        mock_get_user,
        mock_get,
        mock_authorize_access_token,
    ):
        """Test Google callback with existing user"""
        # Mock the OAuth token and user info responses
        mock_authorize_access_token.return_value = {"token": "test_token"}
        mock_get.return_value = MagicMock(
            json=lambda: {"name": "Test User", "email": "testuser@example.com"}
        )

        # Simulate an existing user
        mock_get_user.return_value = {
            "email": "testuser@example.com",
            "username": "Test User",
        }

        # Mock token creation
        mock_create_access_token.return_value = "access_token"
        mock_create_refresh_token.return_value = "refresh_token"

        response = client.get("/google/callback?state=some_state")

        self.assertEqual(response.status_code, 200)
        json_response = await response.json()
        self.assertEqual(json_response["access_token"], "access_token")
        self.assertEqual(json_response["refresh_token"], "refresh_token")
        self.assertEqual(json_response["email"], "testuser@example.com")

    @patch("api.oauth.google.authorize_access_token")
    @patch("api.oauth.google.get")
    @patch("api._get_user")
    @patch("api._create_user")
    @patch("api.create_access_token")
    @patch("api.create_refresh_token")
    async def test_google_callback_new_user(
        self,
        mock_create_refresh_token,
        mock_create_access_token,
        mock_create_user,
        mock_get_user,
        mock_get,
        mock_authorize_access_token,
    ):
        """Test Google callback with new user"""
        # Mock the OAuth token and user info responses
        mock_authorize_access_token.return_value = {"token": "test_token"}
        mock_get.return_value = MagicMock(
            json=lambda: {"name": "New User", "email": "newuser@example.com"}
        )

        # Simulate that the user does not exist
        mock_get_user.return_value = None

        # Mock token creation
        mock_create_access_token.return_value = "access_token"
        mock_create_refresh_token.return_value = "refresh_token"

        response = client.get("/auth/google/callback?state=some_state")

        self.assertEqual(response.status_code, 200)
        json_response = await response.json()
        self.assertEqual(json_response["access_token"], "access_token")
        self.assertEqual(json_response["refresh_token"], "refresh_token")
        self.assertEqual(json_response["email"], "newuser@example.com")


if __name__ == "__main__":
    unittest.main()
