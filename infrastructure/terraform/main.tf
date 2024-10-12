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
  default = "us-east-1"
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

resource "aws_dynamodb_table" "users-table" {
  name           = "users"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "userid"
  range_key      = "email"

  attribute {
    name = "userid"
    type = "S"
  }

  attribute {
    name = "username"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  ttl {
    attribute_name = "TimeToExist"
    enabled        = true
  }

  global_secondary_index {
    name               = "EmailIndex"
    hash_key           = "email"
    range_key          = "username"
    write_capacity     = 10
    read_capacity      = 10
    projection_type    = "INCLUDE"
    non_key_attributes = ["userid", "username", "password", "usercreated", "lastlogin"]
  }

  tags = {
    Name        = "users_table"
  }
}
