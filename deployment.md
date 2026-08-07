# Deployment Guide — NovaMind AI Multimodal Chatbot

This guide covers two deployment targets:
- **Local** — run on your Windows machine for development and demo
- **AWS EC2** — deploy for public internet access

Commands are labelled clearly: `[PowerShell]`, `[EC2 — Ubuntu]`, `[AWS Console]`.

---

## Part 1 — Local Deployment (Windows)

### Step 1: Navigate to the project folder

```powershell
# [PowerShell]
cd "E:\GenAi-Project-Udemy\Code_15042025\Chatbot_text_image"
```

### Step 2: Activate the virtual environment

```powershell
# [PowerShell]
.\.venv\Scripts\Activate.ps1
```

If you see a permissions error, run this first:
```powershell
# [PowerShell] — one-time fix
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install the new requirements

```powershell
# [PowerShell]
pip install -r requirements_new.txt
```

### Step 4: Verify AWS credentials

```powershell
# [PowerShell]
aws sts get-caller-identity
```

Expected output: your AWS Account ID, User ID, and ARN.
If this fails, run `aws configure` and provide your credentials.

### Step 5: Enable Nova Pro in Bedrock Console

```
# [AWS Console]
1. Open: https://console.aws.amazon.com/bedrock/
2. Left menu → Model access
3. Find "Amazon Nova Pro" → Request access (or Enable)
4. Wait for status to become "Access granted" (usually instant)
```

### Step 6: Run the diagnostic check

```powershell
# [PowerShell]
python scripts/bedrock_model_access_check.py
```

All 10 checks must pass before running the app.

### Step 7: Run the multimodal chatbot

```powershell
# [PowerShell]
streamlit run mod_chatbot_frontend.py
```

Open your browser at: **http://localhost:8501**

### Step 8 (optional): Run the original chatbot

The original chatbot is preserved and still works:

```powershell
# [PowerShell]
streamlit run chatbot_frontend2.py
```

---

###################################
## Part 2 — AWS EC2 Deployment
###################################
### Prerequisites

- AWS account with EC2 and Bedrock access
- A key pair (.pem file) for SSH
- The project pushed to GitHub, or files ready to upload via SCP

---

### Step 1: Launch EC2 Instance

```
# [AWS Console]
1. Go to EC2 → Launch Instance
2. Name: novabot-server
3. AMI: Ubuntu 24.04 LTS (free tier eligible)
4. Instance type: t3.micro  (or t2.micro for free tier)
5. Key pair: select or create one (save the .pem file)
6. Security Group — Inbound Rules:
   Type        Port   Source
   SSH         22     My IP
   Custom TCP  8501   0.0.0.0/0   (Streamlit)
7. Click Launch Instance
```

### Step 2: Attach an IAM Role (Recommended — no credentials needed)

```
# [AWS Console]
1. Go to EC2 → Instances → select your instance
2. Actions → Security → Modify IAM Role
3. Create new role:
   - Trusted entity: EC2
   - Policy: AmazonBedrockFullAccess
   - Role name: novabot-ec2-role
4. Attach the role to the instance
```

With an IAM role, no `aws configure` is needed on the EC2 instance.

### Step 3: Connect to the EC2 instance

```powershell
# [PowerShell — run from folder where .pem file is located]
ssh -i "mlops-key.pem" ubuntu@<your-ec2-public-ip>
```

### Step 4: Set up the server

```bash
# [EC2 — Ubuntu]
sudo apt update && sudo apt upgrade -y
sudo apt install python3-venv python3-pip git -y
```

### Step 5: Clone the repository

```bash
# [EC2 — Ubuntu]
cd ~
git clone https://github.com/aamir490/use-case-3--multimodal-ai-chatbot-aws-bedrock.git
cd use-case-3--multimodal-ai-chatbot-aws-bedrock
```

### Step 6: Create virtual environment and install packages

```bash
# [EC2 — Ubuntu]
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements_new.txt
```

### Step 7: Verify the setup

```bash
# [EC2 — Ubuntu]
python scripts/bedrock_model_access_check.py
```

### Step 8: Run the app in the background

```bash
# [EC2 — Ubuntu]
nohup streamlit run mod_chatbot_frontend.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  > nohup.out 2>&1 &
```

### Step 9: Access the app

```
http://<your-ec2-public-ip>:8501
```

Find your EC2 public IP in the AWS Console → EC2 → Instances.

---

## Part 3 — EC2 Maintenance Commands

### Check if the app is running

```bash
# [EC2 — Ubuntu]
ps aux | grep streamlit
```

### View logs

```bash
# [EC2 — Ubuntu]
tail -f nohup.out
```

### Stop the app

```bash
# [EC2 — Ubuntu]
pkill -f streamlit
```

### Restart with latest code from GitHub

```bash
# [EC2 — Ubuntu]
cd ~/use-case-3--multimodal-ai-chatbot-aws-bedrock
git pull
pkill -f streamlit
source .venv/bin/activate
nohup streamlit run mod_chatbot_frontend.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  > nohup.out 2>&1 &
```

### Check port 8501 is listening

```bash
# [EC2 — Ubuntu]
sudo ss -tulnp | grep 8501
```

### Update files directly (without Git)

```powershell
# [PowerShell — from your local machine]
scp -i "mlops-key.pem" mod_chatbot_frontend.py ubuntu@<ip>:~/chatbot/
scp -i "mlops-key.pem" -r services/ ubuntu@<ip>:~/chatbot/
scp -i "mlops-key.pem" -r utils/ ubuntu@<ip>:~/chatbot/
```

---

## Part 4 — Environment Variables (Optional)

If you want to customise the app without editing code:

```powershell
# [PowerShell — local]
Copy-Item .env.example .env
notepad .env
```

```bash
# [EC2 — Ubuntu]
cp .env.example .env
nano .env
```

Then load the `.env` before running:

```bash
# [EC2 — Ubuntu]
export $(cat .env | grep -v '^#' | xargs)
streamlit run mod_chatbot_frontend.py --server.port 8501 --server.address 0.0.0.0
```

---

## Part 5 — Security Hardening for EC2

For a more secure production setup:

```
# [AWS Console]
1. Restrict SSH (port 22) to your specific IP only
2. Consider using AWS Systems Manager Session Manager instead of SSH
   (eliminates the need for an open port 22 entirely)
3. Use HTTPS:
   - Request a free certificate from AWS ACM
   - Set up an Application Load Balancer with HTTPS → EC2
   - Or install nginx + certbot on the EC2 instance
4. Restrict port 8501 to your IP during development
   (open to 0.0.0.0/0 only for demos)
```
