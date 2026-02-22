terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.6"
}

provider "aws" {
  region = var.aws_region
}

# Dynamically resolve the latest Ubuntu 22.04 LTS AMI so the config never
# goes stale when Canonical publishes new images.
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "app" {
  name        = "${var.environment}-app-sg"
  description = "Allow SSH, HTTP, HTTPS inbound; all outbound"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-app-sg"
    Environment = var.environment
  }
}

resource "aws_instance" "app" {
  ami                                  = data.aws_ami.ubuntu.id
  instance_type                        = var.instance_type
  key_name                             = var.key_pair_name
  vpc_security_group_ids               = [aws_security_group.app.id]
  instance_initiated_shutdown_behavior = "terminate"

  # Schedule the instance to shut itself down (and terminate) after ttl_hours.
  user_data = <<-EOF
    #!/bin/bash
    shutdown -h +${var.ttl_hours * 60}
  EOF

  root_block_device {
    volume_size = var.root_volume_size
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name        = "${var.environment}-app-server"
    Environment = var.environment
  }
}

# Regenerate the Ansible inventory every time the EC2 public IP changes.
resource "local_file" "ansible_inventory" {
  content = templatefile("${path.module}/templates/hosts.ini.tpl", {
    ec2_ip       = aws_instance.app.public_ip
    ssh_key_path = var.ssh_private_key_path
  })
  filename        = "${path.module}/../ansible/inventory/hosts.ini"
  file_permission = "0644"
}
