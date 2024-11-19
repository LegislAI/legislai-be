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

# # Create a VPC
# resource "aws_vpc" "authorization_vpc" {
#   cidr_block = "10.0.0.0/16"

#   tags = {
#     Name = "authorization-vpc"
#   }
# }

# # Create an Internet Gateway
# resource "aws_internet_gateway" "igw" {
#   vpc_id = aws_vpc.authorization_vpc.id

#   tags = {
#     Name = "authorization-igw"
#   }
# }

# # Create public subnets with valid availability zones for eu-west-1
# resource "aws_subnet" "public_subnet_1" {
#   vpc_id            = aws_vpc.authorization_vpc.id
#   cidr_block        = "10.0.1.0/24"
#   availability_zone = "eu-west-1a"

#   tags = {
#     Name = "public-subnet-1"
#   }
# }

# resource "aws_subnet" "public_subnet_2" {
#   vpc_id            = aws_vpc.authorization_vpc.id
#   cidr_block        = "10.0.2.0/24"
#   availability_zone = "eu-west-1b"

#   tags = {
#     Name = "public-subnet-2"
#   }
# }

# # Create a route table for public subnets
# resource "aws_route_table" "public" {
#   vpc_id = aws_vpc.authorization_vpc.id

#   route {
#     cidr_block = "0.0.0.0/0"
#     gateway_id = aws_internet_gateway.igw.id
#   }

#   tags = {
#     Name = "public-route-table"
#   }
# }

# # Associate the route table with the public subnets
# resource "aws_route_table_association" "public_subnet_1" {
#   subnet_id      = aws_subnet.public_subnet_1.id
#   route_table_id = aws_route_table.public.id
# }

# resource "aws_route_table_association" "public_subnet_2" {
#   subnet_id      = aws_subnet.public_subnet_2.id
#   route_table_id = aws_route_table.public.id
# }

# # Create a security group
# resource "aws_security_group" "authorization_sg" {
#   vpc_id = aws_vpc.authorization_vpc.id

#   ingress {
#     from_port   = 80
#     to_port     = 80
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"] # Allow all incoming traffic on port 80 (for ALB)
#   }

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1" # Allow all outgoing traffic
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   tags = {
#     Name = "authorization-sg"
#   }
# }

resource "aws_dynamodb_table" "users_table" {
  name           = "users"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "user_id"
  range_key      = "email"

  attribute {
    name = "user_id"
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
    projection_type    = "ALL"
  }

  tags = {
    Name = "users_table"
  }
}

resource "aws_dynamodb_table" "token_blacklist_table" {
  name           = "token_blacklist"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "user_id"
  range_key      = "auth_token"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "auth_token"
    type = "S"
  }

  ttl {
    attribute_name = "TimeToExist"
    enabled        = true
  }

  tags = {
    Name = "token_blacklist_table"
  }
}
resource "aws_dynamodb_table" "conversations_table" {
  name           = "conversations"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "conversation_id"
  range_key      = "user_id"

  attribute {
    name = "conversation_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "conversation_name"
    type = "S"
  }

  attribute {
    name = "conversation_field"
    type = "S"
  }

  attribute {
    name = "updated_at"
    type = "S"
  }
  
    # GSI for querying by user_id
  global_secondary_index {
    name               = "UserIdAtIndex"
    hash_key           = "user_id"
    projection_type    = "ALL"
    write_capacity     = 10
    read_capacity      = 10
  }

  # GSI for querying by updated_at
  global_secondary_index {
    name               = "UpdatedAtIndex"
    hash_key           = "updated_at"
    projection_type    = "ALL"
    write_capacity     = 10
    read_capacity      = 10
  }

  # GSI for querying by name (if needed)
  global_secondary_index {
    name               = "NameIndex"
    hash_key           = "conversation_name"
    projection_type    = "ALL"
    write_capacity     = 10
    read_capacity      = 10
  }

  # GSI for querying by field (if needed)
  global_secondary_index {
    name               = "FieldIndex"
    hash_key           = "conversation_field"
    projection_type    = "ALL"
    write_capacity     = 10
    read_capacity      = 10
  }

  tags = {
    Name = "conversations_table"
  }
}

resource "aws_dynamodb_table" "messages_table" {
  name           = "messages"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "message_index"
  range_key      = "conversation_id"

  attribute {
    name = "message_index"
    type = "S"
  }

  attribute {
    name = "conversation_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "message"
    type = "S"
  }

  attribute {
    name = "sender"
    type = "S"
  }

  # attribute {
  #   name = "attachments"
  #   type = "L"
  # }

  # GSI for querying by created_at
  global_secondary_index {
    name               = "TimeStampIndex"
    hash_key           = "timestamp"
    projection_type    = "ALL"
    write_capacity     = 10
    read_capacity      = 10
  }

  # GSI for querying by sender (if needed)
  global_secondary_index {
    name               = "SenderIndex"
    hash_key           = "sender"
    projection_type    = "ALL"
    write_capacity     = 10
    read_capacity      = 10
  }

  global_secondary_index {
    name               = "MessageIndex"
    hash_key           = "message"
    projection_type    = "ALL"
    write_capacity     = 10
    read_capacity      = 10
  }

  tags = {
    Name = "messages_table"
  }
}



# resource "aws_ecr_repository" "authorization" {
#   name = "authorization"
# }

# resource "aws_route53_zone" "legislai_org" {
#   name = "legislai.org"
# }

# # Create a CloudWatch Log Group
# resource "aws_cloudwatch_log_group" "ecs_log_group" {
#   name              = "/ecs/authorization" # Change this name as needed
#   retention_in_days = 14 # Optional: set retention policy
# }

# # Create an ECS cluster
# resource "aws_ecs_cluster" "authorization" {
#   name = "authorization-cluster"
# }

# # IAM Role for ECS Task Execution
# resource "aws_iam_role" "ecs_task_execution_role" {
#   name = "ecsTaskExecutionRole"

#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "ecs-tasks.amazonaws.com"
#         }
#       }
#     ]
#   })


# }

# # ECS Task Definition for Authorization API
# resource "aws_ecs_task_definition" "authorization" {
#   family                   = "authorization-task"
#   requires_compatibilities = ["FARGATE"]
#   network_mode            = "awsvpc"
#   cpu                     = "256"
#   memory                  = "512"

#   execution_role_arn = aws_iam_role.ecs_task_execution_role.arn

#   container_definitions = jsonencode([
#     {
#       name      = "authorization"
#       image     = "${aws_ecr_repository.authorization.repository_url}:latest"
#       memory    = 512
#       cpu       = 256
#       essential = true
#       portMappings = [
#         {
#           containerPort = 8000
#           hostPort      = 8000
#           protocol      = "tcp"
#         }
#       ]
#       environment = [
#         {
#           name  = "AWS_ACCESS_KEY_ID"
#           value = var.AWS_ACCESS_KEY_ID
#         },
#         {
#           name  = "AWS_SECRET_ACCESS_KEY"
#           value = var.AWS_SECRET_ACCESS_KEY
#         }
#       ]
#       logConfiguration = {
#         logDriver = "awslogs"
#         options = {
#           "awslogs-group"         = aws_cloudwatch_log_group.ecs_log_group.name
#           "awslogs-region"       = var.AWS_REGION
#           "awslogs-stream-prefix" = "ecs"
#         }
#       }
#     }
#   ])
# }

# # Create an Application Load Balancer
# resource "aws_lb" "app_lb" {
#   name               = "authorization-lb"
#   internal           = false
#   load_balancer_type = "application"
#   security_groups    = [aws_security_group.authorization_sg.id]
#   subnets            = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]

#   enable_deletion_protection = false

#   tags = {
#     Name = "authorization-lb"
#   }
# }

# # Create a Target Group for the Authorization API (IP type)
# resource "aws_lb_target_group" "authorization" {
#   name     = "authorization-tg"
#   port     = 8000
#   protocol = "HTTP"
#   vpc_id   = aws_vpc.authorization_vpc.id
#   target_type = "ip"  # Set target type to 'ip'

#   health_check {
#     path                = "/"
#     port                = "8000"
#     protocol            = "HTTP"
#     interval            = 30
#     timeout             = 5
#     healthy_threshold   = 2
#     unhealthy_threshold = 2
#   }

#   tags = {
#     Name = "authorization-target-group"
#   }
# }

# # Create a Listener for the Load Balancer
# resource "aws_lb_listener" "http" {
#   load_balancer_arn = aws_lb.app_lb.arn
#   port              = 80
#   protocol          = "HTTP"

#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.authorization.arn
#   }
# }

# # Create ECS Service for the Authorization API
# resource "aws_ecs_service" "authorization" {
#   name            = "authorization-service"
#   cluster         = aws_ecs_cluster.authorization.id
#   task_definition = aws_ecs_task_definition.authorization.id
#   desired_count   = 1

#   launch_type = "FARGATE"

#   network_configuration {
#     subnets          = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
#     security_groups  = [aws_security_group.authorization_sg.id]
#     assign_public_ip = true
#   }

#   load_balancer {
#     target_group_arn = aws_lb_target_group.authorization.arn
#     container_name   = "authorization"
#     container_port   = 8000
#   }

#   lifecycle {
#     ignore_changes = [task_definition]  # Ignore changes to task definition
#   }

#   tags = {
#     Name = "authorization-service"
#   }
# }
