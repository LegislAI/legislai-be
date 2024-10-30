import unittest
from unittest.mock import patch

from api import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestAuthentication(unittest.TestCase):
    @patch("api._get_user")
    def test_register_existing_user(self, mock_get_user):
        """Test registering a user that already exists"""
        mock_get_user.return_value = {
            "email": "existingemail@example.com",
            "username": "existinguser",
            "password": "password123",
        }

        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "existingemail@example.com",
                "password": "password123",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"],
            "User with email existingemail@example.com already exists",
        )

    @patch("api._create_user")
    @patch("api._get_user")
    def test_register_new_user(self, mock_get_user, mock_create_user):
        """Test registering a new user"""
        mock_get_user.return_value = None
        mock_create_user.return_value = {
            "password": "password123",
            "email": "newemail@example.com",
            "username": "newuser",
        }

        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newemail@example.com",
                "password": "password123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.json())
        self.assertEqual(response.json()["email"], "newemail@example.com")

    @patch("api._get_user")
    def test_login_non_existent_email(self, mock_get_user):
        """Test logging in with a non-existent email"""
        mock_get_user.return_value = None

        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Incorrect credentials")

    @patch("api._get_user")
    def test_login_wrong_password(self, mock_get_user):
        """Test logging in with a wrong password"""
        mock_get_user.return_value = {
            "email": "existingemail@example.com",
            "password": "correctpassword",
        }

        response = client.post(
            "/auth/login",
            json={"email": "existingemail@example.com", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Incorrect credentials")

    @patch("api._update_user_fields")
    @patch("api._get_user")
    def test_login_success(self, mock_get_user, mock_update_user_fields):
        """Test logging in with correct credentials"""
        mock_get_user.return_value = {
            "userid": "some-uuid",
            "email": "existingemail@example.com",
            "password": "password123",
            "username": "existinguser",
        }

        response = client.post(
            "/auth/login",
            json={"email": "existingemail@example.com", "password": "password123"},
        )
        self.assertEqual(response.status_code, 200)
        # self.assertIn("access_token", response.json())
        mock_update_user_fields.assert_called_once()


if __name__ == "__main__":
    unittest.main()
