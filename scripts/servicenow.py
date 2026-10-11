"""Small ServiceNow REST API helper used by the GitHub Actions pipeline.

Commands:
  open-change    create a change request, print its number and sys_id
  close-change   close the change request given by $CHANGE_SYS_ID
  open-incident  create an incident that links to the failed workflow run
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def base_url():
    host = os.environ.get("SN_INSTANCE", "").strip().rstrip("/")
    if not host:
        fail("SN_INSTANCE is not set (add it as a GitHub secret)")
    if not host.startswith(("http://", "https://")):
        host = "https://" + host
    return host


def call(method, path, payload=None):
    user = os.environ.get("SN_USER", "").strip()
    password = os.environ.get("SN_PASSWORD", "").strip()
    print("DEBUG password length:", "-".join(str(len(password))), file=sys.stderr)


    if not user or not password:
        fail("SN_USER / SN_PASSWORD are not set (add them as GitHub secrets)")

    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    request = urllib.request.Request(
        base_url() + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())["result"]
    except urllib.error.HTTPError as error:
        fail(f"ServiceNow returned HTTP {error.code}: {error.read().decode()[:500]}")
    except urllib.error.URLError as error:
        fail(f"Could not reach ServiceNow: {error.reason}")


def run_url():
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "unknown/repo")
    run_id = os.environ.get("GITHUB_RUN_ID", "0")
    return f"{server}/{repo}/actions/runs/{run_id}"


def write_output(key, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as handle:
            handle.write(f"{key}={value}\n")


def open_change():
    sha = os.environ.get("GITHUB_SHA", "unknown")[:7]
    repo = os.environ.get("GITHUB_REPOSITORY", "unknown/repo")
    result = call(
        "POST",
        "/api/now/table/change_request",
        {
            "short_description": f"CI/CD deployment of {repo} ({sha})",
            "description": (
                "Automated change opened by GitHub Actions before deployment.\n"
                f"Commit: {sha}\n"
                f"Triggered by: {os.environ.get('GITHUB_ACTOR', 'unknown')}\n"
                f"Pipeline run: {run_url()}"
            ),
            "type": "normal",
        },
    )
    print(f"Opened change {result['number']} (sys_id {result['sys_id']})")
    write_output("sys_id", result["sys_id"])
    write_output("number", result["number"])


def close_change():
    sys_id = os.environ.get("CHANGE_SYS_ID", "")
    if not sys_id:
        fail("CHANGE_SYS_ID is not set")
    result = call(
        "PATCH",
        f"/api/now/table/change_request/{sys_id}",
        {
            "state": "3",
            "close_code": "successful",
            "close_notes": f"Deployment and staging smoke test passed. Run: {run_url()}",
        },
    )
    print(f"Closed change {result.get('number', sys_id)}")


def open_incident():
    repo = os.environ.get("GITHUB_REPOSITORY", "unknown/repo")
    result = call(
        "POST",
        "/api/now/table/incident",
        {
            "short_description": f"CI/CD pipeline failed for {repo}",
            "description": (
                "A stage of the GitHub Actions pipeline failed.\n"
                f"Failed run: {run_url()}"
            ),
            "urgency": "2",
            "impact": "2",
        },
    )
    print(f"Opened incident {result['number']}")


COMMANDS = {
    "open-change": open_change,
    "close-change": close_change,
    "open-incident": open_incident,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        fail("usage: servicenow.py {open-change|close-change|open-incident}")
    COMMANDS[sys.argv[1]]()

