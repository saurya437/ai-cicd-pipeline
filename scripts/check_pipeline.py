import os
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
    response.raise_for_status()  # agar error aaye to turant batao

    data = response.json()
    latest_run = data["workflow_runs"][0]  # sabse naya run
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


def main():
    run = get_latest_workflow_run()

    print(f"Run ID: {run['id']}")
    print(f"Status: {run['status']}")
    print(f"Conclusion: {run['conclusion']}")
    print(f"Branch: {run['head_branch']}")
    print(f"Commit message: {run['head_commit']['message']}")
    print(f"Created at: {run['created_at']}")

    if run['conclusion'] == 'failure':
        print("\n⚠️  PIPELINE FAILED! Failure detected.")

        failed_jobs = get_failed_jobs(run['id'])
        for job in failed_jobs:
            print(f"\n--- Failed Job: {job['name']} (ID: {job['id']}) ---")
            logs = get_job_logs(job['id'])

            relevant_lines = []
            for line in logs.split("\n"):
                if any(keyword in line for keyword in ["FAILED", "Error", "assert", "AssertionError"]):
                    relevant_lines.append(line)

            if relevant_lines:
                print("\n".join(relevant_lines))
            else:
                print(logs[-1500:])

    elif run['conclusion'] == 'success':
        print("\n✅ Pipeline passed successfully.")


if __name__ == "__main__":
    main()