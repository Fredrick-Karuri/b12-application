# B12 Application Submission

Automated submission pipeline for the [B12 Full Stack Engineer (Backend Emphasis)](https://b12.io/careers) role. Runs via GitHub Actions, constructs a canonical signed payload, and POSTs it to the B12 submission endpoint.

---

## How It Works

1. GitHub Actions injects applicant details and GitHub context as environment variables
2. `scripts/submit.py` builds a canonicalized JSON payload (compact, alphabetically sorted, UTF-8)
3. The payload is signed with HMAC-SHA256 using the signing secret
4. An HTTP POST is made to `https://b12.io/apply/submission` with the signature header
5. The receipt token is printed to the CI console

---

## Project Structure

```
b12-application/
├── .github/
│   └── workflows/
│       └── apply.yml       # CI workflow (manual trigger)
├── scripts/
│   └── submit.py           # Submission script (stdlib only)
└── README.md
```

---

## Setup

### 1. Add the signing secret

Go to **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|------|-------|
| `SIGNING_SECRET` | `hello-there-from-b12` |

### 2. Update applicant details in `apply.yml`

```yaml
env:
  APPLICANT_NAME: "Your Name"
  APPLICANT_EMAIL: "you@example.com"
  RESUME_LINK: "https://linkedin.com/in/yourprofile"
```

### 3. Trigger the workflow

Go to **Actions → Submit Application to B12 → Run workflow → Run workflow**

The receipt token will appear in the step logs:

```
Submission accepted. Receipt: your-submission-receipt
```

---

## Running Locally

```bash
export APPLICANT_NAME="Your Name"
export APPLICANT_EMAIL="you@example.com"
export RESUME_LINK="https://linkedin.com/in/yourprofile"
export SIGNING_SECRET="hello-there-from-b12"
export GITHUB_SERVER_URL="https://github.com"
export GITHUB_REPOSITORY="username/repo"
export GITHUB_RUN_ID="0"

python scripts/submit.py
```

> Note: Running locally won't produce a valid `action_run_link` for B12 to verify. Use the GitHub Actions run for the real submission.

---

## Dependencies

None. Uses Python stdlib only: `json`, `hmac`, `hashlib`, `urllib.request`, `datetime`.