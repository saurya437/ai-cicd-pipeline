import os
import json
import requests
from dotenv import load_dotenv

# .env file se environment variables load karo
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def get_latest_workflow_run():
    """Sabse recent workflow run fetch karo"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    data = response.json()
    latest_run = data["workflow_runs"][0]
    return latest_run


def get_failed_jobs(run_id):
    """Us run ke andar kaunse jobs fail hue, wo fetch karo"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}/jobs"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    data = response.json()
    failed_jobs = [job for job in data["jobs"] if job["conclusion"] == "failure"]
    return failed_jobs


def get_job_logs(job_id):
    """Ek specific job ke logs fetch karo"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/jobs/{job_id}/logs"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text


def extract_relevant_error_lines(logs):
    """Logs ke andar se sirf error-related lines nikaalo"""
    relevant_lines = []
    for line in logs.split("\n"):
        if any(keyword in line for keyword in ["FAILED", "Error", "assert", "AssertionError"]):
            relevant_lines.append(line.strip())

    if relevant_lines:
        return relevant_lines
    else:
        # Fallback: kuch specific na mile to last kuch lines de do
        return logs.split("\n")[-20:]


def build_failure_report(run, failed_jobs):
    """Sab kuch ek clean, structured dictionary me organize karo"""
    report = {
        "run_id": run["id"],
        "branch": run["head_branch"],
        "commit_message": run["head_commit"]["message"],
        "commit_sha": run["head_sha"],
        "created_at": run["created_at"],
        "status": run["conclusion"],
        "failed_jobs": []
    }

    for job in failed_jobs:
        logs = get_job_logs(job["id"])
        error_lines = extract_relevant_error_lines(logs)

        job_info = {
            "job_name": job["name"],
            "job_id": job["id"],
            "error_lines": error_lines
        }
        report["failed_jobs"].append(job_info)

    return report


def main():
    run = get_latest_workflow_run()

    print(f"Run ID: {run['id']}")
    print(f"Status: {run['status']}")
    print(f"Conclusion: {run['conclusion']}")
    print(f"Branch: {run['head_branch']}")
    print(f"Commit message: {run['head_commit']['message']}")
    print(f"Created at: {run['created_at']}")

    if run['conclusion'] == 'failure':
        print("\n⚠️  PIPELINE FAILED! Building structured failure report...\n")

        failed_jobs = get_failed_jobs(run['id'])
        report = build_failure_report(run, failed_jobs)

        # Structured JSON print karo (yahi Phase 4 me AI ko jayega)
        print(json.dumps(report, indent=2))

        # Report ko file me bhi save kar do, baad me use karne ke liye
        with open("latest_failure_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n✅ Failure report 'latest_failure_report.json' me save ho gayi.")

    elif run['conclusion'] == 'success':
        print("\n✅ Pipeline passed successfully. Koi failure nahi mila.")


if __name__ == "__main__":
    main()