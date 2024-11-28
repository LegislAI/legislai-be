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
        user_quota = user["weekly_queries"]["S"]
        updated_quota = 0
        boto3_client.update_item(
            TableName="users",
            Key={"user_id": {"S": user_id}, "email": {"S": user["email"]["S"]}},
            UpdateExpression="SET weekly_queries = :weekly_queries",
            ExpressionAttributeValues={":weekly_queries": {"S": str(updated_quota)}},
        )
    except KeyError:
        raise Exception(f"User {user['user_id']['S']} does not have a quota set")
    except Exception as e:
        raise Exception(f"Failed to update user quota: {str(e)}")


for user in get_all_users():
    update_user_quota(user)
