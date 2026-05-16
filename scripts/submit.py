import hashlib
import hmac
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

ENDPOINT = "https://b12.io/apply/submission"


def build_payload() -> dict:
    server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")
    repo = os.getenv("GITHUB_REPOSITORY", "username/repo")
    run_id = os.getenv("GITHUB_RUN_ID", "0")

    timestamp = (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )

    return {
        "action_run_link": f"{server_url}/{repo}/actions/runs/{run_id}",
        "email": os.environ["APPLICANT_EMAIL"],
        "name": os.environ["APPLICANT_NAME"],
        "repository_link": f"{server_url}/{repo}",
        "resume_link": os.environ["RESUME_LINK"],
        "timestamp": timestamp,
    }


def canonicalize(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sign(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def post(body: bytes, signature: str) -> str:
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature-256": signature,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            response = json.loads(resp.read().decode("utf-8"))
            return response["receipt"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP {e.code} error: {error_body}", file=sys.stderr)
        sys.exit(1)


def main():
    try:
        payload = build_payload()
    except KeyError as e:
        print(f"Missing required environment variable: {e}", file=sys.stderr)
        sys.exit(1)

    secret = os.getenv("SIGNING_SECRET", "hello-there-from-b12")
    body = canonicalize(payload)
    signature = sign(body, secret)
    receipt = post(body, signature)

    print(f"Submission accepted. Receipt: {receipt}")


if __name__ == "__main__":
    main()