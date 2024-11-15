import unittest
from unittest.mock import Mock
from unittest.mock import patch

from fastapi.testclient import TestClient
from users.main import app
from users.utils.exceptions import UserNotFoundException

client = TestClient(app)


class TestUsersAPI(unittest.TestCase):
    @patch("users.routes.users_routes.JWTBearer")
    @patch("users.services.dynamo_services.get_user_by_email")
    @patch("users.utils.users.is_authenticated")
    @patch("users.utils.users.decodeJWT")
    def test_get_user_info_success(
        self,
        mock_decodeJWT,
        mock_is_authenticated,
        mock_get_user_by_email,
        mock_jwt_bearer,
    ):

        mock_is_authenticated.return_value = True

        mock_get_user_by_email.return_value = {
            "user_id": "some-uuid",
            "email": "user@example.com",
            "username": "testuser",
            "plan": "free",
        }

        mock_decode_jwt = Mock()

        mock_jwt_bearer = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        mock_decodeJWT.return_value = {"sub": "user@example.com"}

        print(mock_jwt_bearer)
        response = client.get(
            "/users/some-uuid", headers={"Authorization": f"Bearer {mock_jwt_bearer}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "user@example.com")
        self.assertEqual(response.json()["username"], "testuser")

    # @patch("users.api.is_authenticated")
    # def test_get_user_info_unauthorized(self, mock_is_authenticated):
    #     mock_is_authenticated.return_value = False

    #     response = client.get("/users/some-uuid", headers={"Authorization": "Bearer invalid_token"})
    #     self.assertEqual(response.status_code, 401)
    #     self.assertEqual(response.json()["detail"], "Unauthorized")

    # @patch("users.api.get_user_by_email")
    # @patch("users.api.is_authenticated")
    # @patch("users.api.decodeJWT")
    # def test_get_user_info_user_not_found(self, mock_decodeJWT, mock_is_authenticated, mock_get_user_by_email):
    #     mock_is_authenticated.return_value = True
    #     mock_decodeJWT.return_value = {"sub": "nonexistent@example.com"}
    #     mock_get_user_by_email.side_effect = UserNotFoundException()

    #     response = client.get("/users/some-uuid", headers={"Authorization": "Bearer valid_token"})
    #     self.assertEqual(response.status_code, 404)
    #     self.assertEqual(response.json()["detail"], "User not found with id: some-uuid")

    # @patch("users.api.update_user_info")
    # @patch("users.api.is_authenticated")
    # @patch("users.api.decodeJWT")
    # def test_update_user_info_success(self, mock_decodeJWT, mock_is_authenticated, mock_update_user_info):
    #     mock_is_authenticated.return_value = True
    #     mock_decodeJWT.return_value = {"sub": "user@example.com"}
    #     mock_update_user_info.return_value = {
    #         "user_id": "some-uuid",
    #         "email": "user@example.com",
    #         "username": "updateduser",
    #         "plan": "free"
    #     }

    #     response = client.patch("/users/some-uuid", json={"username": "updateduser"}, headers={"Authorization": "Bearer valid_token"})
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json()["username"], "updateduser")

    # @patch("users.api.update_user_info")
    # @patch("users.api.is_authenticated")
    # @patch("users.api.decodeJWT")
    # def test_update_user_info_user_not_found(self, mock_decodeJWT, mock_is_authenticated, mock_update_user_info):
    #     mock_is_authenticated.return_value = True
    #     mock_decodeJWT.return_value = {"sub": "nonexistent@example.com"}
    #     mock_update_user_info.side_effect = UserNotFoundException()

    #     response = client.patch("/users/some-uuid", json={"username": "updateduser"}, headers={"Authorization": "Bearer valid_token"})
    #     self.assertEqual(response.status_code, 404)
    #     self.assertEqual(response.json()["detail"], "User not found with email: nonexistent@example.com")

    # @patch("users.api.get_user_by_email")
    # @patch("users.api.is_authenticated")
    # @patch("users.api.decodeJWT")
    # def test_get_user_plan_success(self, mock_decodeJWT, mock_is_authenticated, mock_get_user_by_email):
    #     mock_is_authenticated.return_value = True
    #     mock_decodeJWT.return_value = {"sub": "user@example.com"}
    #     mock_get_user_by_email.return_value = {
    #         "user_id": "some-uuid",
    #         "email": "user@example.com",
    #         "username": "testuser",
    #         "plan": "premium"
    #     }

    #     response = client.get("/users/plan/some-uuid", headers={"Authorization": "Bearer valid_token"})
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json()["plan"], "premium")

    # @patch("users.api.service_update_plan")
    # @patch("users.api.is_authenticated")
    # @patch("users.api.decodeJWT")
    # def test_update_user_plan_success(self, mock_decodeJWT, mock_is_authenticated, mock_service_update_plan):
    #     mock_is_authenticated.return_value = True
    #     mock_decodeJWT.return_value = {"sub": "user@example.com"}
    #     mock_service_update_plan.return_value = {
    #         "user_id": "some-uuid",
    #         "plan": "premium"
    #     }

    #     response = client.patch("/users/plan/some-uuid", json={"plan": "premium"}, headers={"Authorization": "Bearer valid_token"})
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json()["plan"], "premium")

    # @patch("users.api.service_update_plan")
    # @patch("users.api.is_authenticated")
    # @patch("users.api.decodeJWT")
    # def test_update_user_plan_user_not_found(self, mock_decodeJWT, mock_is_authenticated, mock_service_update_plan):
    #     mock_is_authenticated.return_value = True
    #     mock_decodeJWT.return_value = {"sub": "nonexistent@example.com"}
    #     mock_service_update_plan.side_effect = UserNotFoundException()

    #     response = client.patch("/users/plan/some-uuid", json={"plan": "premium"}, headers={"Authorization": "Bearer valid_token"})
    #     self.assertEqual(response.status_code, 404)
    #     self.assertEqual(response.json()["detail"], "User not with id: some-uuid found")

    # @patch("users.api.is_authenticated")
    # def test_get_user_plan_unauthorized(self, mock_is_authenticated):
    #     mock_is_authenticated.return_value = False

    #     response = client.get("/users/plan/some-uuid", headers={"Authorization": "Bearer invalid_token"})
    #     self.assertEqual(response.status_code, 401)
    #     self.assertEqual(response.json()["detail"], "Unauthorized")


if __name__ == "__main__":
    unittest.main()
