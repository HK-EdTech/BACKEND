variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-southeast-2"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ssh_public_key" {
  description = "SSH public key content to register as an AWS key pair at deploy time"
  type        = string
}

variable "ssh_private_key_path" {
  description = "Local path to the private key (.pem). Written into the Ansible inventory."
  type        = string
  # No default — must be supplied via tfvars or TF_VAR_ssh_private_key_path.
  # Local dev: absolute path to dev01.pem
  # CI: ~/.ssh/deploy_key  (where GitHub Actions writes DEPLOY_KEY_DEV)
}

variable "root_volume_size" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 20
}

variable "ttl_hours" {
  description = "Hours until the instance automatically terminates"
  type        = number
  default     = 6
}
