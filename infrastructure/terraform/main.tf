terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "AWS_REGION" {
  type    = string
  default = "eu-west-1"  # Updated to match your region
}

variable "AWS_ACCESS_KEY_ID" {
  type      = string
  sensitive = true
}

variable "AWS_SECRET_ACCESS_KEY" {
  type      = string
  sensitive = true
}

provider "aws" {
  region                      = var.AWS_REGION
  access_key                  = var.AWS_ACCESS_KEY_ID
  secret_key                  = var.AWS_SECRET_ACCESS_KEY
  skip_metadata_api_check     = true
}

# resource "aws_dynamodb_table" "users_table" {
#   name           = "users"
#   billing_mode   = "PROVISIONED"
#   read_capacity  = 20
#   write_capacity = 20
#   hash_key       = "user_id"
#   range_key      = "email"

#   attribute {
#     name = "user_id"
#     type = "S"
#   }

#   attribute {
#     name = "username"
#     type = "S"
#   }

#   attribute {
#     name = "email"
#     type = "S"
#   }

#   ttl {
#     attribute_name = "TimeToExist"
#     enabled        = true
#   }

#   global_secondary_index {
#     name               = "EmailIndex"
#     hash_key           = "email"
#     range_key          = "username"
#     write_capacity     = 10
#     read_capacity      = 10
#     projection_type    = "ALL"
#   }

#   tags = {
#     Name = "users_table"
#   }
# }

# resource "aws_dynamodb_table" "token_blacklist_table" {
#   name           = "token_blacklist"
#   billing_mode   = "PROVISIONED"
#   read_capacity  = 20
#   write_capacity = 20
#   hash_key       = "user_id"
#   range_key      = "auth_token"

#   attribute {
#     name = "user_id"
#     type = "S"
#   }

#   attribute {
#     name = "auth_token"
#     type = "S"
#   }

#   ttl {
#     attribute_name = "TimeToExist"
#     enabled        = true
#   }

#   tags = {
#     Name = "token_blacklist_table"
#   }
# }
# resource "aws_dynamodb_table" "conversations_table" {
#   name           = "conversations"
#   billing_mode   = "PROVISIONED"
#   read_capacity  = 20
#   write_capacity = 20
#   hash_key       = "conversation_id"
#   range_key      = "user_id"

#   attribute {
#     name = "conversation_id"
#     type = "S"
#   }

#   attribute {
#     name = "user_id"
#     type = "S"
#   }

#   attribute {
#     name = "conversation_name"
#     type = "S"
#   }

#   attribute {
#     name = "conversation_field"
#     type = "S"
#   }

#   attribute {
#     name = "updated_at"
#     type = "S"
#   }

#   # GSI for querying by user_id
#   global_secondary_index {
#     name               = "UserIdAtIndex"
#     hash_key           = "user_id"
#     projection_type    = "ALL"
#     write_capacity     = 10
#     read_capacity      = 10
#   }

#   # GSI for querying by updated_at
#   global_secondary_index {
#     name               = "UpdatedAtIndex"
#     hash_key           = "updated_at"
#     projection_type    = "ALL"
#     write_capacity     = 10
#     read_capacity      = 10
#   }

#   # GSI for querying by name (if needed)
#   global_secondary_index {
#     name               = "NameIndex"
#     hash_key           = "conversation_name"
#     projection_type    = "ALL"
#     write_capacity     = 10
#     read_capacity      = 10
#   }

#   # GSI for querying by field (if needed)
#   global_secondary_index {
#     name               = "FieldIndex"
#     hash_key           = "conversation_field"
#     projection_type    = "ALL"
#     write_capacity     = 10
#     read_capacity      = 10
#   }

#   tags = {
#     Name = "conversations_table"
#   }
# }

# resource "aws_dynamodb_table" "messages_table" {
#   name           = "messages"
#   billing_mode   = "PROVISIONED"
#   read_capacity  = 20
#   write_capacity = 20
#   hash_key       = "message_index"
#   range_key      = "conversation_id"

#   attribute {
#     name = "message_index"
#     type = "S"
#   }

#   attribute {
#     name = "conversation_id"
#     type = "S"
#   }

#   attribute {
#     name = "timestamp"
#     type = "S"
#   }

#   attribute {
#     name = "message"
#     type = "S"
#   }

#   attribute {
#     name = "sender"
#     type = "S"
#   }

#   # attribute {
#   #   name = "attachments"
#   #   type = "L"
#   # }

#   # GSI for querying by created_at
#   global_secondary_index {
#     name               = "TimeStampIndex"
#     hash_key           = "timestamp"
#     projection_type    = "ALL"
#     write_capacity     = 10
#     read_capacity      = 10
#   }

#   # GSI for querying by sender (if needed)
#   global_secondary_index {
#     name               = "SenderIndex"
#     hash_key           = "sender"
#     projection_type    = "ALL"
#     write_capacity     = 10
#     read_capacity      = 10
#   }

#   global_secondary_index {
#     name               = "MessageIndex"
#     hash_key           = "message"
#     projection_type    = "ALL"
#     write_capacity     = 10
#     read_capacity      = 10
#   }

#   tags = {
#     Name = "messages_table"
#   }
# }


resource "aws_s3_bucket" "dependencies" {
  bucket = "lambda-dependencies-123"
}

resource "aws_s3_bucket" "lambdas" {
  bucket = "lambda-functions-123"
  force_destroy = true
}

resource "aws_iam_role" "lambda_deployer_role" {
  name = "lambda-role"
  assume_role_policy = jsonencode(
    { Version = "2012-10-17"
    Statement = [
      { Action = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
      Effect = "Allow"
      Sid = ""
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name = "lambda-policy"
  description = "Policy for Lambda to access S3 and CloudWatch"
  policy = jsonencode(
    {
      Version = "2012-10-17"
      Statement = [ {
        Action = [ "s3:GetObject", "s3:PutObject" ]
        Effect = "Allow"
        Resource = "arn:aws:s3:::*/*"
    },
    {
        Action = [ "logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents" ]
        Effect = "Allow"
        Resource = "arn:aws:logs:*:*:*" } ]
    }
  )
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attach" {
  role = aws_iam_role.lambda_deployer_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}
