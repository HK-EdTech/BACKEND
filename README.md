# BACKEND

## Setting up EC2 dev server
dev local box run: `python3 -m pip install --user ansible`
run: `ansible-playbook -i inventory/hosts.ini bootstrap_setup_ec2.yaml`

## TODO List:
Add a real domain + free HTTPS (one command):Bashsudo certbot --nginx -d yourdomain.com
Add health checks + auto-rollback in GitHub Actions (I’ll give you the 5-line addition)
Add Prometheus metrics endpoint to your FastAPI (takes 10 lines)