import os
import json
import requests
import anthropic
from dotenv import load_dotenv

# .env file se environment variables load karo
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ============================================================
# PHASE 3: FAILURE DETECTION
# ============================================================

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


# ============================================================
# PHASE 4: AI ROOT CAUSE ANALYSIS
# ============================================================

def build_prompt(report):
    """Claude ko bhejne ke liye ek clear prompt banao"""
    error_details = ""
    for job in report["failed_jobs"]:
        error_details += f"\nJob: {job['job_name']}\n"
        error_details += "\n".join(job["error_lines"])
        error_details += "\n"

    prompt = f"""Tumhe ek CI/CD pipeline failure diya ja raha hai. Iska root cause analysis karo.

Commit message: {report['commit_message']}
Branch: {report['branch']}

Failure logs:
{error_details}

Neeche diye gaye JSON format me hi jawab do, aur kuch mat likho (koi extra text, koi markdown backticks nahi):

{{
  "root_cause": "ek ya do line me, kya galat hua uska clear reason",
  "explanation": "thoda detail me samjhao ki ye error kyun aaya",
  "suggested_fix": "specific steps ya code change jo is problem ko fix kare",
  "severity": "low, medium, ya high me se ek",
  "auto_fixable": true ya false (kya ye automatically fix ho sakta hai bina insaan ke)
}}"""

    return prompt


def get_ai_analysis(report):
    """Claude API ko call karo aur structured analysis lo"""
    prompt = build_prompt(report)

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text
    cleaned_text = response_text.replace("```json", "").replace("```", "").strip()

    try:
        analysis = json.loads(cleaned_text)
        return analysis
    except json.JSONDecodeError:
        print("⚠️  AI response ko JSON me parse nahi kar paye. Raw response:")
        print(response_text)
        return None


# ============================================================
# MAIN: END-TO-END FLOW
# ============================================================

def main():
    print("🔎 Latest workflow run check kar rahe hain...\n")
    run = get_latest_workflow_run()

    print(f"Run ID: {run['id']}")
    print(f"Status: {run['status']}")
    print(f"Conclusion: {run['conclusion']}")
    print(f"Branch: {run['head_branch']}")
    print(f"Commit message: {run['head_commit']['message']}")
    print(f"Created at: {run['created_at']}")

    if run['conclusion'] == 'success':
        print("\n✅ Pipeline passed successfully. Koi failure nahi mila, analysis ki zaroorat nahi.")
        return

    if run['conclusion'] == 'failure':
        print("\n⚠️  PIPELINE FAILED! Failure report bana rahe hain...\n")

        failed_jobs = get_failed_jobs(run['id'])
        report = build_failure_report(run, failed_jobs)

        with open("latest_failure_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("✅ Failure report 'latest_failure_report.json' me save ho gayi.\n")

        print("🤖 Claude se root cause analysis maang rahe hain...\n")
        analysis = get_ai_analysis(report)

        if analysis:
            print("=" * 50)
            print("AI ROOT CAUSE ANALYSIS")
            print("=" * 50)
            print(f"\n🔍 Root Cause: {analysis['root_cause']}")
            print(f"\n📖 Explanation: {analysis['explanation']}")
            print(f"\n🛠️  Suggested Fix: {analysis['suggested_fix']}")
            print(f"\n⚡ Severity: {analysis['severity']}")
            print(f"\n🤖 Auto-fixable: {analysis['auto_fixable']}")

            with open("latest_ai_analysis.json", "w") as f:
                json.dump(analysis, f, indent=2)

            print("\n✅ Analysis 'latest_ai_analysis.json' me save ho gayi.")


if __name__ == "__main__":
    main()