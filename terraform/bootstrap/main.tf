# Bootstrap — run once locally to create the S3 bucket and DynamoDB table
# that the main Terraform config uses as its remote backend.
#
# Usage:
#   cd terraform/bootstrap
#   terraform init
#   terraform apply
#
# After apply, note the outputs and fill them into terraform/backend.tf,
# then run `terraform init` from the terraform/ directory.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.6"
  # Intentionally uses local state — cannot use the backend it is creating.
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"
}

variable "project_name" {
  description = "Short project identifier used in resource names"
  type        = string
  default     = "hk-edtech"
}

resource "aws_s3_bucket" "tfstate" {
  bucket        = "${var.project_name}-tfstate"
  force_destroy = false

  tags = {
    Name    = "${var.project_name}-tfstate"
    Purpose = "Terraform remote state"
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "tflock" {
  name         = "${var.project_name}-tflock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name    = "${var.project_name}-tflock"
    Purpose = "Terraform state locking"
  }
}

output "bucket" {
  description = "Copy this into terraform/backend.tf → bucket"
  value       = aws_s3_bucket.tfstate.bucket
}

output "dynamodb_table" {
  description = "Copy this into terraform/backend.tf → dynamodb_table"
  value       = aws_dynamodb_table.tflock.name
}
