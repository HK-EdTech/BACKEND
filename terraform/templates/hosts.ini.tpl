[ec2]
${ec2_ip} ansible_user=ubuntu ansible_ssh_private_key_file=${ssh_key_path}

[ec2:vars]
ansible_python_interpreter=/usr/bin/python3
