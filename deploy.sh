#!/bin/bash

set -e  # Exit immediately if any command fails

# === CONFIG ===
CLUSTER_NAME="fastapi-users-cluster"
TEMPLATE_FILE="./task-definition.template.json"
TASK_DEF_FILE="./task-definition.json"
TASK_DEF_FAMILY="fastapi-users-task"
AWS_REGION="us-east-1"

# === ECR CONFIG ===
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
REPO_NAME="fastapi-users"
IMAGE_TAG="latest"  # or use `latest`, or inject via CI/CD

IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"

echo "🧱 Building Docker image: $IMAGE_URI"
docker build -t "$IMAGE_URI" .

echo "🔐 Logging into Amazon ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# === Create ECR repo if it doesn't exist ===
if ! aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
  echo "📦 Creating ECR repository: $REPO_NAME"
  aws ecr create-repository --repository-name "$REPO_NAME" --region "$AWS_REGION"
else
  echo "✅ ECR repository '$REPO_NAME' already exists."
fi

echo "📤 Pushing Docker image to ECR..."
docker push "$IMAGE_URI"

# === Generate ECS task definition ===
echo "🛠️ Generating ECS task definition from template..."
sed \
  -e "s|{{AWS_ACCOUNT_ID}}|$AWS_ACCOUNT_ID|g" \
  -e "s|{{IMAGE_NAME}}|$REPO_NAME:$IMAGE_TAG|g" \
  -e "s|{{TASK_DEF_FAMILY}}|$TASK_DEF_FAMILY|g" \
  "$TEMPLATE_FILE" > "$TASK_DEF_FILE"

# === Ensure ECS Cluster Exists ===
echo "🔍 Checking if ECS cluster '$CLUSTER_NAME' exists..."
CLUSTER_EXISTS=$(aws ecs describe-clusters --clusters "$CLUSTER_NAME" --query "clusters[0].status" --output text 2>/dev/null)

if [ "$CLUSTER_EXISTS" == "ACTIVE" ]; then
  echo "✅ ECS cluster '$CLUSTER_NAME' already exists."
else
  echo "🚀 Creating ECS cluster: $CLUSTER_NAME"
  aws ecs create-cluster --cluster-name "$CLUSTER_NAME"
fi

# === Register ECS Task Definition ===
echo "📦 Registering ECS task definition..."
aws ecs register-task-definition --cli-input-json file://"$TASK_DEF_FILE"

# === Get Subnets from Default VPC ===
echo "🌐 Retrieving default VPC subnets..."
SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters "Name=default-for-az,Values=true" \
  --query "Subnets[*].SubnetId" \
  --output text | tr '\t' ',')

if [ -z "$SUBNET_IDS" ]; then
  echo "❌ Error: No default subnets found."
  exit 1
fi
echo "✅ Subnets: $SUBNET_IDS"

# === Get Default Security Group ===
echo "🔐 Getting default security group..."
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=default" \
  --query "SecurityGroups[0].GroupId" \
  --output text)

if [ -z "$SG_ID" ]; then
  echo "❌ Error: Default security group not found."
  exit 1
fi
echo "✅ Security Group: $SG_ID"

# === Run ECS Task ===
echo "🚀 Running ECS Fargate task..."
aws ecs run-task \
  --cluster "$CLUSTER_NAME" \
  --launch-type FARGATE \
  --task-definition "$TASK_DEF_FAMILY" \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --count 1

echo "🎉 Deployment complete. ECS Task launched!"
