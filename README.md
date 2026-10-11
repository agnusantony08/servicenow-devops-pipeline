# ServiceNow-Integrated CI/CD Pipeline (DevOps + ITSM)

A small Flask app whose GitHub Actions pipeline follows ITIL change management:
it opens a ServiceNow change request before deploying, closes it when the
staging smoke test passes, and opens an incident if any stage fails.

## Pipeline
push to main -> pytest -> Docker build + Trivy scan -> open change request
-> deploy to staging + smoke test -> close change request

If any stage fails, a ServiceNow incident is opened with a link to the failed run.

- A failing test blocks the release.
- HIGH or CRITICAL Trivy findings fail the pipeline.
- ServiceNow credentials live in GitHub Secrets, never in the repo.

## Project layout
```
app.py                       Flask app (/ and /health)
tests/test_app.py            3 automated pytest tests
Dockerfile                   non-root container image
scripts/servicenow.py        ServiceNow REST API helper (standard library only)
.github/workflows/ci.yml     the pipeline
```

## Setup
1. Get a free ServiceNow Personal Developer Instance at developer.servicenow.com
   (instances hibernate when idle, so wake it up before running the pipeline).
2. In the repo go to Settings -> Secrets and variables -> Actions and add:
   - `SN_INSTANCE` = your instance host, e.g. `dev12345.service-now.com`
   - `SN_USER` = your ServiceNow user name (e.g. `admin`)
   - `SN_PASSWORD` = that user's password
3. Push to `main` and watch the Actions tab. Check Change -> All and
   Incident -> All in ServiceNow to see the records.

## Run the tests locally
```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

## Security notes
- Container runs as a non-root user (UID 10001)
- Trivy fails the pipeline on HIGH/CRITICAL findings (unfixed ones are ignored)
- Trivy runs from a pinned container image rather than a mutable Action tag
- Credentials are passed through GitHub Secrets as environment variables
