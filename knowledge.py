"""Small knowledge base of common AWS errors that Dr. Cloud can look up."""

COMMON_ERRORS = {
    "AccessDenied": {
        "diagnosis": "Your identity (user or role) is not allowed to do this action, or a policy is explicitly denying it.",
        "checks": [
            "Read the full message: it names the action (e.g. s3:GetObject) and the resource ARN.",
            "Check the IAM policy attached to the user/role for that exact action and resource.",
            "Look for an explicit Deny in SCPs, permission boundaries or bucket/resource policies.",
            "If using a role, confirm you really assumed it (aws sts get-caller-identity).",
        ],
    },
    "NoSuchBucket": {
        "diagnosis": "The bucket name does not exist, is misspelled, or lives in another region/account.",
        "checks": [
            "Bucket names are global and case-sensitive: check for typos.",
            "Confirm the region with aws s3api get-bucket-location.",
            "Make sure you are in the right AWS account (aws sts get-caller-identity).",
        ],
    },
    "ExpiredToken": {
        "diagnosis": "Your temporary credentials expired.",
        "checks": [
            "Refresh them: aws sso login (or re-assume the role).",
            "Remove stale AWS_SESSION_TOKEN values from your environment.",
        ],
    },
    "ResourceNotFoundException": {
        "diagnosis": "The resource (Lambda function, table, etc.) was not found in this region/account.",
        "checks": [
            "Verify the name and ARN spelling.",
            "Check the region your CLI/SDK is using (aws configure get region).",
        ],
    },
    "Task timed out": {
        "diagnosis": "A Lambda function hit its configured timeout before finishing.",
        "checks": [
            "Raise the timeout in the function configuration (max 15 minutes).",
            "Check if the function is waiting on a network call (VPC without NAT or endpoint is a classic).",
            "Look at CloudWatch Logs for the last line printed before the timeout.",
        ],
    },
    "ThrottlingException": {
        "diagnosis": "You are calling an API faster than your quota allows.",
        "checks": [
            "Add exponential backoff with jitter (the AWS SDKs have retry modes).",
            "Check Service Quotas to see if you can request an increase.",
        ],
    },
    "AccessDeniedException bedrock": {
        "diagnosis": "Bedrock model access is not enabled for this model in this region, or IAM lacks bedrock:InvokeModel.",
        "checks": [
            "Open the Bedrock console and make sure the model is available to your account in this region.",
            "Add bedrock:InvokeModel and bedrock:InvokeModelWithResponseStream to your policy.",
        ],
    },
}
