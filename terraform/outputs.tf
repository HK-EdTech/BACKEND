output "public_ip" {
  description = "Public IP of the EC2 instance (used by GitHub Actions and SSH)"
  value       = aws_instance.app.public_ip
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
