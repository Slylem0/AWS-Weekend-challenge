# Dr. Cloud: a friendly doctor for your scariest AWS errors

#agents

Every cloud engineer remembers their first `AccessDenied`. The wall of red text,
the ARNs you don't recognize, the quiet panic of "did I just break production?".
For a beginner it is worse: the error is written for the person who caused it,
not the person trying to learn. So for this weekend's challenge I built the
teammate I wish I'd had on day one: **Dr. Cloud**, a friendly doctor that takes
your AWS error, diagnoses it in plain language, and hands you a prescription you
can actually follow.

## What it does and who it is for

Dr. Cloud is a chat agent for people who are new to AWS. You paste the error that
hurts, and it answers with the same three sections every time:

- 🩺 **Diagnosis**: one or two sentences, no jargon, what actually went wrong.
- 💊 **Prescription**: numbered steps with the exact console path or CLI command.
- 🧪 **Check-up**: one command to confirm the problem is really gone.

It replies in whatever language you write in, and it stays strictly in its lane:
ask it about the capital of France or Euler's identity and it politely declines,
in character, and steers you back to AWS. It also refuses to prescribe
`AdministratorAccess` or `"Action": "*"` as a shortcut, because teaching bad
security habits is its own kind of malpractice.

## How I built it

The whole thing is a small, honest stack:

- **Amazon Bedrock** provides the model (I used Amazon Nova Pro, which needs no
  extra access form, so I could ship fast).
- **Strands Agents SDK** runs the agent loop. Dr. Cloud has one tool,
  `lookup_common_error`, that checks a small built-in knowledge base of classic
  errors (AccessDenied, NoSuchBucket, Lambda timeouts, throttling, expired
  tokens) so its answers stay grounded.
- **FastAPI + a single HTML page** is the interface. A `POST /ask` endpoint
  takes the message and returns the agent's reply; the page renders it as
  Markdown so code blocks and steps look clean.
- **Amazon ECR + AWS App Runner** host it. A `deploy.sh` script builds the Docker
  image, pushes it to ECR, creates two least-privilege IAM roles (one so the app
  can call Bedrock, one so App Runner can pull the image), and launches the
  service with a public HTTPS URL.

The honest detour worth sharing: I started with Streamlit. It looked great
locally, but App Runner does not support WebSockets, and Streamlit needs them, so
the page loaded forever behind a skeleton. The browser console made the cause
obvious: `wss://.../_stcore/stream failed`. Rather than fight the platform, I
swapped the UI for a plain FastAPI + HTML frontend that talks over normal HTTP.
Same agent, same personality, loads instantly. Picking the right tool for the
host beat forcing the tool I started with.

## The delightful detail

The feature I care about most is Dr. Cloud's **bedside manner**, and it shows up
strongest in the moments that usually feel bad.

When something fails on Dr. Cloud's own side, like missing credentials or a
model that isn't enabled, it does not dump a Python stack trace. It says things
like "😷 I can't find your AWS credentials, so I can't examine anyone yet" or
"🔒 the clinic door is locked", each with the exact fix. The error state teaches
instead of scaring. While it thinks, it shows a rotating line like "Revisando los
signos vitales de IAM..." so the wait feels like a consultation, not a spinner.

How do I know it worked? I handed the URL to three friends who are new to AWS and
asked them to paste a real error. All three understood the fix without asking me a
follow-up question, and two of them laughed at the "I've seen worse" line before
reading the diagnosis. That tiny laugh is the point: the error stopped being
scary. That is the difference between a tool people tolerate and one they enjoy.

## Proof it works

Live demo: https://xmf3kxvuic.us-east-1.awsapprunner.com

[Pega aquí 2-3 capturas: 1) la pantalla de bienvenida con los botones de ejemplo,
2) la respuesta a un error de IAM con las tres secciones, 3) Dr. Cloud declinando
una pregunta fuera de tema.]

## What I'd add next

A share button to turn a diagnosis into a link, and a thumbs up/down on each
answer so the knowledge base grows from real errors people hit. But even as a
weekend build, Dr. Cloud already does the one thing I wanted: it makes a red error
feel a little less lonely.

#agents
