# 🩺 Dr. Cloud

First aid for AWS errors. Paste the error that hurts, and Dr. Cloud gives you a
plain-language diagnosis, a prescription with exact steps, and a check-up to
confirm the fix. It stays in character and only talks about AWS and the cloud.

Built for the AWS Builder Center "Weekend Challenge: build an agent people
actually enjoy using."

## What it does

- Explains scary AWS errors (IAM, S3, Lambda, Bedrock, networking, CLI/SDK...)
  in beginner-friendly language.
- Answers in whatever language you write in.
- Structures every answer as 🩺 Diagnosis → 💊 Prescription → 🧪 Check-up.
- Refuses off-topic questions in character and steers you back to AWS.
- Never suggests `AdministratorAccess` or `"Action": "*"`; prefers least privilege.

## Stack

- **Amazon Bedrock** (Amazon Nova Pro) as the model.
- **Strands Agents SDK** for the agent loop and tool use.
- **Streamlit** for the chat UI.
- **Amazon ECR + AWS App Runner** for a public HTTPS deployment.
- **IAM** least-privilege roles (one to invoke Bedrock, one to pull from ECR).

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
aws configure            # or aws sso login
streamlit run app.py
```

The model is set with `DRCLOUD_MODEL_ID` (default `us.amazon.nova-pro-v1:0`)
and the region with `AWS_REGION` (default `us-east-1`).

## Deploy to AWS App Runner

```bash
bash deploy.sh
```

The script creates the ECR repo, builds and pushes the image, creates the IAM
roles, and launches the App Runner service, then prints the public URL.

## Clean up (stop paying for it)

```bash
aws apprunner delete-service --region us-east-1 --service-arn <service-arn>
```
