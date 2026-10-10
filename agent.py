"""Dr. Cloud: a friendly first-aid agent for AWS errors, built with Strands Agents + Amazon Bedrock."""

import os

from strands import Agent, tool
from strands.models import BedrockModel

from knowledge import COMMON_ERRORS

# Override with env vars if your account uses a different model or region.
MODEL_ID = os.getenv("DRCLOUD_MODEL_ID", "us.amazon.nova-pro-v1:0")
REGION = os.getenv("AWS_REGION", "us-east-1")

SYSTEM_PROMPT = """You are Dr. Cloud, a warm and slightly funny doctor for AWS errors.
Your patients are beginners who just hit a scary error message.

Scope rules (very important):
- You ONLY help with AWS, cloud infrastructure, and the errors/tooling around them
  (IAM, S3, Lambda, EC2, Bedrock, CLI/SDK, networking, deployment, billing, etc.).
- If the user asks about anything outside that scope (math, history, general trivia,
  cooking, homework, coding puzzles unrelated to AWS, etc.), do NOT answer it.
  Politely decline in-character as a doctor and steer back to AWS. For example:
  "Ese no es mi campo, soy especialista en nube ☁️. Tráeme un error de AWS y te atiendo."
- Greetings and small talk are fine: respond briefly and invite them to share an AWS error.
- Never break character to answer off-topic questions, even if the user insists.

Style rules:
- Reply in the same language the user writes in.
- Always follow this structure, using these exact headings (translate them if needed):
  1. 🩺 Diagnosis: one or two plain sentences, no jargon.
  2. 💊 Prescription: numbered steps, each with the exact console path or CLI command.
  3. 🧪 Check-up: one command or action to confirm it is fixed.
- Start with a short reassuring line (one sentence). Light humor with medical puns is welcome, but never at the expense of clarity or the user.
- Never ask the user to paste secrets. If they paste keys or tokens, tell them to rotate those keys.
- Prefer least-privilege fixes. Never suggest AdministratorAccess or "Action: *" as the solution.
- If you are not sure, say so and list what extra info you need (error code, service, region).
- Use the lookup_common_error tool first when the message matches a known error code.
"""


@tool
def lookup_common_error(error_text: str) -> str:
    """Look up a known AWS error in Dr. Cloud's medical records.

    Args:
        error_text: The error code or message the user got (e.g. "AccessDenied", "Task timed out").
    """
    text = error_text.lower()
    matches = [
        (name, info) for name, info in COMMON_ERRORS.items()
        if all(word in text for word in name.lower().split())
    ]
    if not matches:
        return "No record found. Reason from the error message and AWS best practices."
    lines = []
    for name, info in matches:
        lines.append(f"{name}: {info['diagnosis']}")
        lines.extend(f"- {c}" for c in info["checks"])
    return "\n".join(lines)


def create_agent() -> Agent:
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION, temperature=0.4)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[lookup_common_error],
        callback_handler=None,  # the UI handles display
    )


def friendly_error(exc: Exception) -> str:
    """Turn technical exceptions into messages that match Dr. Cloud's bedside manner."""
    msg = str(exc)
    if "NoCredentials" in msg or "Unable to locate credentials" in msg:
        return ("😷 I can't find your AWS credentials, so I can't examine anyone yet. "
                "Run `aws configure` (or `aws sso login`) and try again.")
    if "AccessDenied" in msg or "not authorized" in msg:
        return ("🔒 The clinic door is locked: your account can't use this Bedrock model. "
                "Enable model access in the Bedrock console and check bedrock:InvokeModel permission.")
    if "ExpiredToken" in msg:
        return "⏰ Your session expired. Refresh it with `aws sso login` and come back."
    if "Throttling" in msg:
        return "🚑 Too many patients at once. Wait a few seconds and try again."
    return f"🤒 Something went wrong in the clinic, not with you. Details: {msg}"
