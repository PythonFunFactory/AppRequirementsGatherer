# Demo Deployment

Get the app on the internet in about 10 minutes. No domain, no HTTPS, no frills.

## Step 1 — Launch an EC2 instance

In the [AWS Console](https://console.aws.amazon.com/ec2) → **Launch Instance**:

| Setting | Value |
|---|---|
| AMI | Amazon Linux 2023 |
| Instance type | t3.small |
| Key pair | Create or select one — you'll need the `.pem` file |
| Security group | Allow **SSH (22)** and **HTTP (80)** from `0.0.0.0/0` |

Launch it, then wait ~60 seconds for it to start. Grab the **Public IPv4 address** from the instance details.

## Step 2 — Run the setup script

SSH in and run one command:

```bash
ssh -i your-key.pem ec2-user@YOUR-EC2-IP

bash <(curl -sSL https://raw.githubusercontent.com/PythonFunFactory/AppRequirementsGatherer/Demo/demo-setup.sh)
```

When prompted, paste your Anthropic API key. The script installs Docker, clones the repo, and starts the app. It takes 3–5 minutes (most of that is Docker building the images).

## Step 3 — Open the app

Navigate to `http://YOUR-EC2-IP` in a browser.

Users sign in by typing any name and email address — no passwords, no accounts to create.

## Tearing it down

When the demo is done, just **terminate the EC2 instance** from the AWS console. Everything is gone with it.

Or to just stop the app without terminating:
```bash
cd AppRequirementsGatherer && sudo docker compose down
```
