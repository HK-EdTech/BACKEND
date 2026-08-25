output "public_ip" {
  description = "Elastic IP (stable across deploys)"
  value       = aws_eip.app.public_ip
}

output "public_dns" {
  description = "Public DNS hostname of the EC2 instance"
  value       = aws_instance.app.public_dns
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "ami_id" {
  description = "AMI ID that was resolved and used"
  value       = data.aws_ami.ubuntu.id
}

output "ttl_hours" {
  description = "Hours until the instance auto-terminates"
  value       = var.ttl_hours
}
