# import pytest
# from moto import mock_dynamodb
# import boto3
# from datetime import datetime, timezone
# from fastapi.testclient import TestClient
# from fastapi import FastAPI
# from unittest.mock import patch, MagicMock
# import jwt
# from authentication.main import app




# # Test data
# TEST_USER = {
#     "email": "test@example.com",
#     "username": "testuser",
#     "password": "Test123!",
#     "userid": "123e4567-e89b-12d3-a456-426614174000",
#     "hashed_password": "hashed_password_string",
# }

# @pytest.fixture
# def mock_boto3_client():
#     """Create a mock boto3 client"""
#     with patch('boto3.client') as mock_client:
#         yield mock_client


# @pytest.fixture
# def mock_db():
#     """Create a mock database client"""
#     mock = MagicMock()
    
#     # Mock successful query response
#     mock.query.return_value = {
#         "Items": [{
#             "userid": {"S": TEST_USER["userid"]},
#             "email": {"S": TEST_USER["email"]},
#             "username": {"S": TEST_USER["username"]},
#             "password": {"S": TEST_USER["hashed_password"]}
#         }],
#         "Count": 1
#     }
    
#     # Mock successful put_item response
#     mock.put_item.return_value = {}
    
#     return mock

# @pytest.fixture
# def mock_security():
#     """Create a mock security utils"""
#     mock = MagicMock()
#     mock.hash_password.return_value = TEST_USER["hashed_password"]
#     mock.verify_password.return_value = True
#     return mock