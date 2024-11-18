import os

import boto3
from dotenv import load_dotenv

load_dotenv()

aws_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")

boto3_client = boto3.client(
    "dynamodb",
    aws_access_key_id=f"{aws_key_id}",
    aws_secret_access_key=f"{aws_secret_key}",
    region_name=f"{aws_region}",
)


def get_all_users():
    response = boto3_client.scan(TableName="users")
    return response["Items"]


def update_user_quota(user):
    try:
        user_id = user["user_id"]["S"]
        user_quota = user["daily_queries"]["S"]
        print(f"Updating user {user_id} quota from {user_quota} to 0")
        updated_quota = 0
        boto3_client.update_item(
            TableName="users",
            Key={"user_id": {"S": user_id}, "email": {"S": user["email"]["S"]}},
            UpdateExpression="SET daily_queries = :daily_queries",
            ExpressionAttributeValues={":daily_queries": {"S": str(updated_quota)}},
        )
        print(f"User {user_id} quota updated to {updated_quota}")
    except KeyError:
        print(f"User {user['user_id']['S']} does not have a quota set")
    except Exception as e:
        print(f"Failed to update user quota: {str(e)}")


for user in get_all_users():
    update_user_quota(user)
