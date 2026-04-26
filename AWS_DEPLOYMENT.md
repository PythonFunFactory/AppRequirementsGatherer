# AWS Deployment Guide

## Architecture Overview

```
Internet
   │  HTTPS (443)
   ▼
Application Load Balancer  ◄─── ACM TLS Certificate
   │  HTTP (80)
   ▼
EC2 Instance (t3.small)
   ├── Docker: frontend (nginx, port 80)
   │     └── proxies /auth /sessions /admin → backend
   └── Docker: backend (FastAPI, port 8000)
         ├── SQLite DB  → EBS volume (persists with EC2)
         └── PDFs       → S3 bucket
```

Container images are stored in **ECR** and pulled to EC2 on each deploy. The ALB handles TLS termination via **ACM**, so your app never deals with certificates directly.

---

## Prerequisites

On your local machine:
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) installed and configured (`aws configure`)
- Docker Desktop running
- Your domain name with access to its DNS settings

In your AWS account:
- A Route 53 hosted zone for your domain (or you'll update DNS manually at your registrar)

---

## Step 1 — IAM Setup

### 1a. Create an EC2 instance role

This lets the EC2 instance access S3 and ECR without storing AWS credentials in `.env`.

```bash
# Create the role
aws iam create-role \
  --role-name RequirementsGathererEC2Role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach S3 full access to your PDF bucket
aws iam put-role-policy \
  --role-name RequirementsGathererEC2Role \
  --policy-name S3PDFAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }]
  }'

# Attach ECR read access (to pull images)
aws iam attach-role-policy \
  --role-name RequirementsGathererEC2Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

# Create the instance profile
aws iam create-instance-profile \
  --instance-profile-name RequirementsGathererEC2Profile

aws iam add-role-to-instance-profile \
  --instance-profile-name RequirementsGathererEC2Profile \
  --role-name RequirementsGathererEC2Role
```

---

## Step 2 — S3 Bucket for PDFs

```bash
aws s3api create-bucket \
  --bucket YOUR-BUCKET-NAME \
  --region us-east-1

# Block all public access (PDFs are served via presigned URLs)
aws s3api put-public-access-block \
  --bucket YOUR-BUCKET-NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

---

## Step 3 — ECR Repositories

Create two repositories — one for each Docker image.

```bash
aws ecr create-repository --repository-name requirements-gatherer-backend --region us-east-1
aws ecr create-repository --repository-name requirements-gatherer-frontend --region us-east-1
```

Note the registry URI from the output: `123456789012.dkr.ecr.us-east-1.amazonaws.com`

### Build and push images

Run this from the project root whenever you want to deploy a new version.

```bash
# Set your values
ECR_REGISTRY=123456789012.dkr.ecr.us-east-1.amazonaws.com
AWS_REGION=us-east-1

# Log in to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and push backend
docker build -t $ECR_REGISTRY/requirements-gatherer-backend:latest ./backend
docker push $ECR_REGISTRY/requirements-gatherer-backend:latest

# Build and push frontend
docker build -t $ECR_REGISTRY/requirements-gatherer-frontend:latest ./frontend
docker push $ECR_REGISTRY/requirements-gatherer-frontend:latest
```

---

## Step 4 — EC2 Instance

### 4a. Create a security group

```bash
# Get your default VPC ID
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" \
  --query "Vpcs[0].VpcId" --output text)

aws ec2 create-security-group \
  --group-name requirements-gatherer-sg \
  --description "Requirements Gatherer app" \
  --vpc-id $VPC_ID

# Note the GroupId from output, then add rules:
SG_ID=sg-xxxxxxxxxxxxxxxxx  # replace with your GroupId

# SSH (restrict to your IP in production)
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 22 --cidr 0.0.0.0/0

# HTTP from ALB
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 80 --cidr 0.0.0.0/0
```

### 4b. Launch the instance

```bash
# Get the latest Amazon Linux 2023 AMI
AMI_ID=$(aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=al2023-ami-*-x86_64" \
            "Name=state,Values=available" \
  --query "sort_by(Images, &CreationDate)[-1].ImageId" \
  --output text)

aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.small \
  --key-name YOUR-KEY-PAIR-NAME \
  --security-group-ids $SG_ID \
  --iam-instance-profile Name=RequirementsGathererEC2Profile \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=requirements-gatherer}]' \
  --count 1
```

Note the `InstanceId` and `PublicIpAddress` from the output.

### 4c. Install Docker on the instance

SSH in and run:

```bash
ssh -i your-key.pem ec2-user@YOUR-EC2-IP

# Install Docker
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

# Install Docker Compose plugin
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Log out and back in for the docker group to take effect
exit
ssh -i your-key.pem ec2-user@YOUR-EC2-IP
```

---

## Step 5 — Deploy the Application

### 5a. Set up the app on EC2

```bash
# Clone the repo
git clone https://github.com/PythonFunFactory/AppRequirementsGatherer.git
cd AppRequirementsGatherer
git checkout AWS_Deploy

# Copy and edit the env file
cp .env.aws.example .env
nano .env   # fill in all values
```

**Required `.env` values to set:**
| Variable | Where to get it |
|---|---|
| `AZURE_TENANT_ID/CLIENT_ID/SECRET` | Azure Portal → App Registrations |
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `SECRET_KEY` | Run: `openssl rand -hex 32` |
| `FRONTEND_URL` | Your domain, e.g. `https://app.yourorg.com` |
| `AWS_S3_BUCKET` | The bucket name from Step 2 |
| `ECR_REGISTRY` | Your ECR registry URI from Step 3 |

### 5b. Log ECR in on EC2 and start the app

```bash
# Log in to ECR (the instance role handles auth automatically)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

# Pull images and start
docker compose -f docker-compose.prod.yml up -d

# Verify both containers are running
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

The app is now running on port 80 of your EC2 instance.

---

## Step 6 — Application Load Balancer + HTTPS

### 6a. Request a TLS certificate (ACM)

```bash
aws acm request-certificate \
  --domain-name app.yourorg.com \
  --validation-method DNS \
  --region us-east-1
```

Follow the DNS validation instructions in the ACM console (add a CNAME record to your domain). Wait for status to become `ISSUED` before proceeding.

### 6b. Create the ALB

In the **AWS Console** → EC2 → Load Balancers → Create:

1. **Type**: Application Load Balancer
2. **Name**: `requirements-gatherer-alb`
3. **Scheme**: Internet-facing
4. **Listeners**: HTTP (80) and HTTPS (443)
5. **Availability Zones**: Select at least 2 subnets in your VPC
6. **Security Group**: Create a new one allowing inbound 80 and 443 from `0.0.0.0/0`
7. **Target Group**:
   - Type: Instances
   - Protocol: HTTP, Port: 80
   - Health check path: `/health`
   - Register your EC2 instance as a target
8. **HTTPS Listener**: Select the ACM certificate from Step 6a
9. **HTTP → HTTPS redirect**: Add a rule on the HTTP listener to redirect to HTTPS

Note the ALB DNS name (e.g. `requirements-gatherer-alb-123456789.us-east-1.elb.amazonaws.com`).

### 6c. Point your domain at the ALB

In Route 53 (or your DNS provider), create an **A record** (alias) for `app.yourorg.com` pointing to the ALB DNS name.

---

## Step 7 — Update Entra ID Redirect URI

In the **Azure Portal** → App Registrations → your app → Authentication:

Add redirect URI: `https://app.yourorg.com/auth/callback`

Remove or keep the localhost URI for dev use.

---

## Deploying Updates

Each time you push changes:

```bash
# On your local machine — rebuild and push new images
ECR_REGISTRY=123456789012.dkr.ecr.us-east-1.amazonaws.com
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

docker build -t $ECR_REGISTRY/requirements-gatherer-backend:latest ./backend && \
  docker push $ECR_REGISTRY/requirements-gatherer-backend:latest

docker build -t $ECR_REGISTRY/requirements-gatherer-frontend:latest ./frontend && \
  docker push $ECR_REGISTRY/requirements-gatherer-frontend:latest

# On EC2 — pull and restart
ssh -i your-key.pem ec2-user@YOUR-EC2-IP \
  "cd AppRequirementsGatherer && \
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY && \
   docker compose -f docker-compose.prod.yml pull && \
   docker compose -f docker-compose.prod.yml up -d"
```

---

## Backups

The SQLite database lives in the `db_data` Docker volume on the EC2 EBS volume. Back it up by snapshotting the EBS volume from the AWS console, or by copying the file out periodically:

```bash
# On EC2 — copy DB out of the volume
docker cp $(docker compose -f docker-compose.prod.yml ps -q backend):/app/app.db ./app.db.backup
aws s3 cp app.db.backup s3://YOUR-BUCKET-NAME/backups/app.db.$(date +%Y%m%d)
```

Consider adding this as a cron job on the EC2 instance.

---

## Estimated AWS Costs

| Service | Size | Est. Monthly |
|---|---|---|
| EC2 t3.small | 730 hrs | ~$15 |
| EBS gp3 20 GB | — | ~$1.60 |
| ALB | low traffic | ~$16 |
| S3 | < 1 GB PDFs | < $0.25 |
| ACM | — | Free |
| ECR | < 1 GB images | < $0.10 |
| **Total** | | **~$33/month** |

> To cut costs during development, stop the EC2 instance when not in use (`aws ec2 stop-instances --instance-ids i-xxx`). The EBS volume and its data persist while stopped.
