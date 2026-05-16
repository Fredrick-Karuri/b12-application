# System Design
## B12 Application Submission Pipeline

**Version:** 1.0

---

## 1. Overview

A single Python script triggered by GitHub Actions that constructs, signs, and POSTs a canonical JSON payload to the B12 submission endpoint. Linear flow, no state, no external dependencies.

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────┐
│                   GitHub Actions                     │
│                                                      │
│  env vars (name, email, resume, secret)              │
│  built-ins (SERVER_URL, REPOSITORY, RUN_ID)          │
│                          │                           │
│                          ▼                           │
│            ┌─────────────────────────┐               │
│            │      submit.py          │               │
│            │                         │               │
│            │  1. Build payload dict  │               │
│            │  2. Canonicalize JSON   │               │
│            │  3. Sign (HMAC-SHA256)  │               │
│            │  4. POST to B12         │               │
│            │  5. Print receipt       │               │
│            └────────────┬────────────┘               │
└─────────────────────────│────────────────────────────┘
                          │  HTTPS POST
                          ▼
              https://b12.io/apply/submission
```

---

## 3. Data Flow

### 3.1 Payload Construction

Six fields assembled from env vars and GitHub built-ins:

```
GITHUB_SERVER_URL + GITHUB_REPOSITORY          → repository_link
GITHUB_SERVER_URL + GITHUB_REPOSITORY + RUN_ID → action_run_link
datetime.now(UTC).isoformat(ms)                → timestamp
APPLICANT_NAME / EMAIL / RESUME_LINK           → name / email / resume_link
```

### 3.2 Canonicalization

```python
json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
```

Three constraints enforced simultaneously:
- **Compact** — `separators=(',', ':')` strips all padding spaces
- **Sorted** — `sort_keys=True` guarantees alphabetical key order
- **UTF-8** — `.encode('utf-8')` produces the raw bytes to sign

### 3.3 Signing

```
HMAC-SHA256(key=secret_bytes, msg=canonical_json_bytes) → hex_digest
Header: X-Signature-256: sha256={hex_digest}
```

### 3.4 Transmission

```python
urllib.request.urlopen(req)   # stdlib only, no requests/httpx
```

Response must be HTTP 200. Anything else → print error body → exit(1).

---

## 4. Project Structure

```
b12-application/
├── .github/
│   └── workflows/
│       └── apply.yml        # CI trigger + env var injection
├── scripts/
│   └── submit.py            # Single-file core logic
└── README.md
```


---

## 5. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Library strategy | stdlib only | No pip install step; faster CI; no supply chain risk |
| File structure | Single script | Complexity proportional to the problem (one POST) |
| Secret handling | Env var → GitHub Actions secret | Never appears in source or logs |
| Error handling | Print + exit(1) | Fails the CI run visibly; no silent failures |
| Timestamp precision | milliseconds + Z suffix | Matches B12's ISO 8601 example exactly |

---

## 6. Verification

The B12 docs provide a known-good test vector:

| Input | Expected |
|-------|----------|
| Payload (compact, sorted) | `{"action_run_link":"https://...","email":"you@example.com",...}` |
| Secret | `hello-there-from-b12` |
| HMAC-SHA256 hex digest | `c5db257a56e3c258ec1162459c9a295280871269f4cf70146d2c9f1b52671d45` |

The script can be tested locally before pushing by manually setting the env vars and checking the digest matches.

---

## 7. CI Trigger Strategy

`workflow_dispatch` (manual trigger) is preferred over `push`:
- Submission should happen exactly once, not on every commit
- Avoids accidental re-submissions during iterative development
- Can also add `push` to `main` once the script is validated locally