# BACKEND

## Setting up EC2 dev server
dev local box run: `python3 -m pip install --user ansible`
run: `ansible-playbook -i inventory/hosts.ini bootstrap_setup_ec2.yaml`