# ⚙️ Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) installed and configured
- *[Terraform](https://developer.hashicorp.com/terraform/install) installed (only if deploying via Terraform)
- [Docker](https://www.docker.com/get-started) for building containers/images
- [Git](https://git-scm.com/)

---

## 🖥️ How to Run Locally

### 1. Clone the Repository to local machine

```bash
git clone https://github.com/sally-orig/FinalProject-Users.git UserManagementProject

cd UserManagementProject
```

### 2. Run Alembic migration files

```bash
alembic upgrade head
```

### 3. Run Fastapi application

```bash
uvicorn user.main:app --host 0.0.0.0 --port 8085 --reload
```

---

## 🐳 How to Run Using Docker

### 1. Clone the Repository

```bash
git clone https://github.com/sally-orig/FinalProject-Users.git UserManagementProject

cd UserManagementProject
```

### 2. Build Docker Image

```bash
docker build -t fastapi_users_image .
```

### 3. Run container

```bash
docker run -p 8085:8085 fastapi_users_image
```

---

## ☁️📜 How to deploy to AWS Fargate using a script

### 1. Clone the Repository to your local machine

```bash
git clone https://github.com/sally-orig/FinalProject-Users.git UserManagementProject
```

### 2. Configure AWS credentials then enter your Access Key, Secret Key, and default region (e.g., us-east-1)

```bash
aws configure
```

### 3. Make deploy.sh executable

```bash
chmod +x deploy.sh
```

### 4. Execute deploy.sh script

```bash
./deploy.sh
```

## ☁️📦🧩 How to deploy to AWS Fargate using Terraform and GitHub actions

### 1. Clone the Repository to local

```bash
git clone https://github.com/sally-orig/FinalProject-Users.git UserManagementProject
```

### 2. Configure AWS credentials. Enter your Access Key, Secret Key, and default region (e.g., us-east-1)

```bash
aws configure
```

### 3. Initialize Terraform

```bash
cd UserManagementProject/terraform
terraform init
```

### 3. Apply terraform (Create ECR repo, ECS cluster, ECS service, etc.) and confirm by typing yes

```bash
terraform apply
```

### 4. Create own repository in github. Get secret key and access key from step #2 and add to your github repository secrets

### 5. Push files to your own repository

```bash
cd ..
git add .
git commit -m 'initial commit, deploy to ecs fargate using terraform and github actions'
git push
```

### 6. Go to actions and deploy/run workflow
