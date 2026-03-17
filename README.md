# BACKEND

## High level run down
1. Ansible - For setting up EC2 box (lifting firewall, setting reverse proxy configs, installing docker, nginx...)
2. Github Action - For on push deployment
3. Supabase Auth - Auth provider, opensource BaaS

## Terrform (IaC) run down

### Part I - Manually setup AWS CLI config + Bootstrap S3
0. Download terraform and set it up locally
    - 
    ```bash
        wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt update && sudo apt install terraform
        terraform --version
    ```
1. Setup AWS CLI first, enter sudo password
    ```bash
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
        unzip /tmp/awscliv2.zip -d /tmp
        sudo /tmp/aws/install
    ```
2. Setup AWS credentials locally first (https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)
    - 
    ```bash
        aws configure
    ```
    - Follow the intructions for providing access key, secret key, region (ap-southeast-2), and output format (json)

3. Run bootstrap manually first: 
    ```bash
        cd terraform/bootstrap
        terraform init
        terraform apply
    ```
4. Copy the 2 outputs bucket and dynamodb_table into terraform/backend.tf

### Part II - Manually setup EC2  against S3 backend
1. initial the main tf config
```bash
    cd terraform/
    terraform init
```

2. Create local tfvars `cp terraform.tfvars.example terraform.tfvars` and update the path
3. Edit the terraform.tfvars with the correct private key path by updating to `ssh_private_key_path = "/home/miltonycchow/dev01.pem"`
4. Add the 2 credentials to GitHub secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

5. If you want to do it manually... you can do `terraform apply -var="ttl_hours=2"` if you wish to deviate from the default 6 hours, if you want to test the GitHub Action, just do a push to main and it will trigger the workflow to apply the terraform config

## Setting up EC2 dev server
dev local box run: `python3 -m pip install --user ansible`
run: `ansible-playbook -i inventory/hosts.ini bootstrap_setup_ec2.yaml`

## Seeing docker logs on dev EC2 instance:
`ssh -i ../dev01.pem ubuntu@x.xx.xx.xx "docker logs -f fastapi"`

## TODO List:
Add a real domain + free HTTPS (one command):Bashsudo certbot --nginx -d yourdomain.com
Add health checks + auto-rollback in GitHub Actions (I’ll give you the 5-line addition)
Add Prometheus metrics endpoint to your FastAPI (takes 10 lines)


~~JWT secret implementation~~ - Finished
