#!/usr/bin/env bash
#
# Deploy Dr. Cloud to AWS App Runner.
# Run it step by step the first time so you can see what each part does:
#   bash deploy.sh
#
# Requirements on your machine: aws cli (logged in), docker running.
set -euo pipefail

# ----- Settings you can tweak -----
AWS_REGION="${AWS_REGION:-us-east-1}"
APP_NAME="dr-cloud"
ECR_REPO="dr-cloud"
IMAGE_TAG="latest"
INSTANCE_ROLE="DrCloudAppRunnerInstanceRole"
ACCESS_ROLE="DrCloudAppRunnerAccessRole"
MODEL_ID="${DRCLOUD_MODEL_ID:-us.amazon.nova-pro-v1:0}"
# ----------------------------------

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

echo "==> Account: ${ACCOUNT_ID}  Region: ${AWS_REGION}"

# 1. Create the ECR repository (ignore error if it already exists).
echo "==> [1/6] Ensuring ECR repository exists"
aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${AWS_REGION}" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "${ECR_REPO}" --region "${AWS_REGION}" >/dev/null

# 2. Log Docker in to ECR.
echo "==> [2/6] Logging Docker in to ECR"
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# 3. Build and push the image (linux/amd64 is what App Runner expects).
echo "==> [3/6] Building and pushing image"
docker build --platform linux/amd64 -t "${ECR_REPO}:${IMAGE_TAG}" .
docker tag "${ECR_REPO}:${IMAGE_TAG}" "${ECR_URI}:${IMAGE_TAG}"
docker push "${ECR_URI}:${IMAGE_TAG}"

# 4. Create two IAM roles:
#    - instance role: lets the RUNNING app call Bedrock.
#    - access role:   lets App Runner PULL the image from your private ECR.
echo "==> [4/6] Ensuring App Runner IAM roles exist"

# Instance role (Bedrock access for the app itself).
if ! aws iam get-role --role-name "${INSTANCE_ROLE}" >/dev/null 2>&1; then
  aws iam create-role --role-name "${INSTANCE_ROLE}" \
    --assume-role-policy-document file://apprunner-trust-policy.json >/dev/null
fi
aws iam put-role-policy --role-name "${INSTANCE_ROLE}" \
  --policy-name DrCloudBedrockInvoke \
  --policy-document file://apprunner-role-policy.json
INSTANCE_ROLE_ARN="$(aws iam get-role --role-name "${INSTANCE_ROLE}" --query Role.Arn --output text)"
echo "    Instance role: ${INSTANCE_ROLE_ARN}"

# Access role (ECR pull for App Runner's build service).
if ! aws iam get-role --role-name "${ACCESS_ROLE}" >/dev/null 2>&1; then
  aws iam create-role --role-name "${ACCESS_ROLE}" \
    --assume-role-policy-document file://apprunner-access-trust-policy.json >/dev/null
fi
aws iam attach-role-policy --role-name "${ACCESS_ROLE}" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess
ACCESS_ROLE_ARN="$(aws iam get-role --role-name "${ACCESS_ROLE}" --query Role.Arn --output text)"
echo "    Access role:   ${ACCESS_ROLE_ARN}"

# App Runner needs a moment for brand-new roles to propagate.
sleep 10

# 5. Create (or update) the App Runner service.
echo "==> [5/6] Creating / updating App Runner service"
SERVICE_ARN="$(aws apprunner list-services --region "${AWS_REGION}" \
  --query "ServiceSummaryList[?ServiceName=='${APP_NAME}'].ServiceArn" --output text)"

SOURCE_CONFIG=$(cat <<JSON
{
  "ImageRepository": {
    "ImageIdentifier": "${ECR_URI}:${IMAGE_TAG}",
    "ImageRepositoryType": "ECR",
    "ImageConfiguration": {
      "Port": "8080",
      "RuntimeEnvironmentVariables": {
        "DRCLOUD_MODEL_ID": "${MODEL_ID}",
        "AWS_REGION": "${AWS_REGION}"
      }
    }
  },
  "AutoDeploymentsEnabled": false,
  "AuthenticationConfiguration": {
    "AccessRoleArn": "${ACCESS_ROLE_ARN}"
  }
}
JSON
)

if [ -z "${SERVICE_ARN}" ]; then
  aws apprunner create-service --region "${AWS_REGION}" \
    --service-name "${APP_NAME}" \
    --source-configuration "${SOURCE_CONFIG}" \
    --instance-configuration "{\"InstanceRoleArn\":\"${INSTANCE_ROLE_ARN}\",\"Cpu\":\"1 vCPU\",\"Memory\":\"2 GB\"}" \
    --health-check-configuration '{"Protocol":"HTTP","Path":"/health","Interval":10,"Timeout":5,"HealthyThreshold":1,"UnhealthyThreshold":5}' \
    >/dev/null
  SERVICE_ARN="$(aws apprunner list-services --region "${AWS_REGION}" \
    --query "ServiceSummaryList[?ServiceName=='${APP_NAME}'].ServiceArn" --output text)"
else
  echo "    Service exists, starting a new deployment with the fresh image"
  aws apprunner start-deployment --region "${AWS_REGION}" --service-arn "${SERVICE_ARN}" >/dev/null
fi

# 6. Show the public URL.
echo "==> [6/6] Done. Fetching service URL (it may take a few minutes to go RUNNING)"
URL="$(aws apprunner describe-service --region "${AWS_REGION}" --service-arn "${SERVICE_ARN}" \
  --query 'Service.ServiceUrl' --output text)"
echo ""
echo "    Dr. Cloud will be live at: https://${URL}"
echo "    Check status: aws apprunner describe-service --region ${AWS_REGION} --service-arn ${SERVICE_ARN} --query 'Service.Status' --output text"
