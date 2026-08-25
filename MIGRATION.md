# AWS Migration

Reason: AWS Free accounts are good for about 180 days...

~~ ## Step 1A: Setup Google Workspace ~~

Reference: [here](https://www.cyberangles.org/blog/can-i-create-a-google-account-programmatically/)

1. Setup google workspace account [here](https://workspace.google.com/)
2. Click: `開始免費試用`
3. Then click: `建立新帳戶`
4. 開始使用 options:
    - Location: HK
    - Company name (optional): Markflow.ai
    - Company size: 2-9
5. 請提供您的聯絡資訊
    - Surname: Me
    - Given name: Me
    - Email address: ycchow@gmail
6. 選擇帳戶設定方式: 
    - 使用現有網域完成設定 and click: `使用這個方法繼續`
7. 貴公司的網域名稱為何？
    - 網域名稱: markflow.ai
8. 要使用這個網域設定 Google Workspace 嗎？
    - it shows: `markflow.ai`
    - Yes, click: `下一步`
9. 建立使用者名稱
    - Username: milton
    - Password: (choose a password)
    - Confirm password: (confirm the password)
    - I unchecked everything (which is the default)
    - click `同意並繼續`
    - Takes a while to load
10. Google login page:
    - login with: milton@markflow.ai
    - Password: (the password you set)
11. 驗證您的身分:
    - Telphone number: HK +852 (your phone number)
    - Fill in `G-xxxxxx`
    - click: `下一步`
    - click `我瞭解了`
12. Price...
    - 65.8 HKD per user - 30GB
    - 98.7 HKD per user - 2TB
    - 206.8 HKD per user - 5TB 

## Step 1B: Setup Cloudflare

Assume we already bought a domain from GoDaddy

1. Login from [dash.cloudflare.com](https://dash.cloudflare.com/login)
2. I used my personal Github account to login
    - `Authorized Cloudflare`
3. Add a domain (register a new domain or bring your own). Type in your domain
    - `marflow.hk`
    - Prompted you to "Transfer your domain" page with your pre-typed Domain name
    - Free - `Select Plan` 
    - Select nothing, leave it as it is, `Continue to activation`
4. Update your nameservers to activate Cloudflare. 
    - Log into your DNS provider/ registrar: GoDaddy
    - In GoDaddy, update your nameservers:
        - [control panel](https://dcc.godaddy.com/control/portfolio)
        - Select `markflowhk.com` amd click `More`
        - `編輯名稱伺服器`
        - Remove: GoDaddy 名稱伺服器 (推薦使用) NS24.DOMAINCONTROL.COM & NS23.DOMAINCONTROL.COM
        - Add: Cloudflare nameservers
            - `kipp.ns.cloudflare.com`
            - `melany.ns.cloudflare.com`
        - Save
        - `Continue`
5. Back to cloudflare: click `I've updated my nameservers`
    - Press `check nameservers now`
    - Or refresh: and you're done: `Your domain is now protected by Cloudflare`

TLDR:
    - GoDaddy: Renewals happen here
    - Cloudflare: DNS lives here
6. Enable email routing:
    - `Email` -> `Email Routing` -> `Onboard Domain`
    - Zone, select `markflowhk.com` -> `Done`
    - Click `Email Routing` -> `Destination Address` -> `Add Destination Address` (my own email) (Auto veriried, nice)

~~ 7A. Create (Account level) API Token: ~~ 
    - Bottom left: Manage Account -> `Account API Tokens` -> `Create a Token`
    - `Specified Domains`: `markflowhk.com` 
        - `DNS & Zones`:
            - Read and edit for all 6 !
    - `No Expiration` 
    - Click `Review Token`
        - 
        ```
            DNS Write
            DNS Read
            Zone Read
            Zone Write
            Zone Custom Asset Write
            Zone Custom Asset Read
            Zone DNS Settings Read
            Zone Settings Read
            Zone Versioning Read
            Zone DNS Settings Write
            Zone Settings Write
            Zone Versioning Write
        ```
    - Click `Create Token`

7. Create (User level) API Token:
    - Top right: `Profile`
    - Left side bar: `API Tokens`
    - Click `Create Token`
    - Create Custom Token `Get Started`
        - Token name: `markflowhk`
        - Under `Permissions`
            - `Zone`
            - search `Email Routing Rules`
            - `Edit`
        - Under `Zone Resources`
            - `Include` -> `Specific Zone` -> `markflowhk.com`
        - Continue to summary → Create Token
        ```
        markflowhk API token summary
        This API token will affect the below accounts and zones, along with their respective permissions


        xxxxxx@gmail.com's Account
        markflowhk.com - Email Routing Rules:Edit
        ```
    - Save your markflowhk api token


## Step 1C: Setup Cloudfare with Github Actions
1. Create new custom token on Cloudflare with the following     
    - Permissions:
        - Zone: Email Routing Rules: Edit
        - Zone: Zone: Read
        - Account: Email Routing Address: Edit
    - Zone Resources: 
        - Include: Specific Zone: markflowhk.com

Continue to summary, copy the token

2. 

## Step 2: Setup AWS Free tier account
1. Go to [AWS Free Tier](https://aws.amazon.com/free/)
2. Click `Create a Free Account`, `New to AWS? Create a new AWS account`
3. `Verify your email address`
4. `Root user password` 
5. `Choose Free plan`

6. These are temp credentials:

```
~ $ aws configure list
NAME       : VALUE                    : TYPE             : LOCATION
profile    : <not set>                : None             : None
access_key : ****************224B     : container-role   : 
secret_key : ****************JzhG     : container-role   : 
region     : ap-southeast-2           : env              : ['AWS_REGION', 'AWS_DEFAULT_REGION']
~ $ aws configure get aws_access_key_id
~ $ aws sts get-caller-identity
{
    "UserId": "707938860146",
    "Account": "707938860146",
    "Arn": "arn:aws:iam::707938860146:root"
}
~ $ 
```

7. [security credentials](https://us-east-1.console.aws.amazon.com/iam/home?region=ap-southeast-2#/security_credentials)

8. `Create access key` --> `Retrive access key` --> `Download .csv file` (save it somewhere safe)

9. Update the following on Github Action
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY

10. Update terraform:
    - terraform/backend.tf
        ```
        bucket         = "hk-edtech-707938860146-tfstate"
        ```
    - terraform/bootstrap/main.tf 
        ```
        default     = "hk-edtech-707938860146"
        ```