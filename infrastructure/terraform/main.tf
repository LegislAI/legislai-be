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

# Create a VPC
resource "aws_vpc" "authorization_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "authorization-vpc"
  }
}

# Create public subnets with valid availability zones for eu-west-1
resource "aws_subnet" "public_subnet_1" {
  vpc_id            = aws_vpc.authorization_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "eu-west-1a"

  tags = {
    Name = "public-subnet-1"
  }
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id            = aws_vpc.authorization_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "eu-west-1b"

  tags = {
    Name = "public-subnet-2"
  }
}

# Create a security group
resource "aws_security_group" "authorization_sg" {
  vpc_id = aws_vpc.authorization_vpc.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow all incoming traffic on port 8000
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # Allow all outgoing traffic
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "authorization-sg"
  }
}

# Create IAM role for ECS task execution
resource "aws_iam_role" "ecs_execution_role" {
  name = "ecs_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy_attachment" "ecs_execution_policy" {
  name       = "ecs_execution_policy_attachment"
  roles      = [aws_iam_role.ecs_execution_role.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
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
    Name = "users_table"
  }
}

resource "aws_ecr_repository" "authorization" {
  name = "authorization"
}

resource "aws_ecs_cluster" "authorization" {
  name = "authorization-cluster"
}

resource "aws_ecs_task_definition" "authorization" {
  family                   = "authorization-task"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = "256"
  memory                  = "512"

  execution_role_arn = aws_iam_role.ecs_execution_role.arn # Add execution role

  container_definitions = jsonencode([
    {
      name      = "authorization"
      image     = "${aws_ecr_repository.authorization.repository_url}:latest"
      memory    = 512
      cpu       = 256
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "AWS_ACCESS_KEY_ID"
          value = var.AWS_ACCESS_KEY_ID
        },
        {
          name  = "AWS_SECRET_ACCESS_KEY"
          value = var.AWS_SECRET_ACCESS_KEY
        }
      ]
    }
  ])
}

resource "aws_ecs_service" "authorization" {
  name            = "authorization-service"
  cluster         = aws_ecs_cluster.authorization.id
  task_definition = aws_ecs_task_definition.authorization.id
  desired_count   = 1

  network_configuration {
    subnets          = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
    security_groups  = [aws_security_group.authorization_sg.id]
  }
}
