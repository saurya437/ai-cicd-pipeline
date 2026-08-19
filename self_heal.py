import os
import re
import json
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def load_json(filepath):
    """Koi bhi JSON file load karo"""
    with open(filepath, "r") as f:
        return json.load(f)


def rerun_workflow(run_id):
    """GitHub API se failed workflow ko re-run karo"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}/rerun"
    response = requests.post(url, headers=HEADERS)

    if response.status_code == 201:
        return True
    else:
        print(f"⚠️  Re-run request fail hui. Status code: {response.status_code}")
        print(response.text)
        return False


def detect_missing_module(analysis, failure_report):
    """
    Root cause aur error logs me dhundo ki koi Python module missing to nahi hai.
    Return: module ka naam (string) agar mila, warna None
    """
    combined_text = analysis.get("root_cause", "") + " " + analysis.get("explanation", "")

    for job in failure_report.get("failed_jobs", []):
        combined_text += " " + " ".join(job.get("error_lines", []))

    match = re.search(r"No module named ['\"]?([a-zA-Z0-9_\-]+)['\"]?", combined_text)

    if match:
        return match.group(1)
    return None


def add_dependency_and_push(module_name):
    """
    requirements.txt me module add karo, phir commit aur push karo.
    """
    req_file = "requirements.txt"

    with open(req_file, "r") as f:
        content = f.read()

    if module_name.lower() in content.lower():
        print(f"ℹ️  '{module_name}' already requirements.txt me hai. Skip kar rahe hain.")
        return False

    with open(req_file, "a") as f:
        f.write(f"\n{module_name}\n")

    print(f"✅ '{module_name}' ko requirements.txt me add kar diya.")

    try:
        subprocess.run(["git", "add", req_file], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Self-heal: auto-add missing dependency '{module_name}'"],
            check=True
        )
        subprocess.run(["git", "push"], check=True)
        print("🚀 Fix commit aur push ho gaya GitHub pe.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation fail hui: {e}")
        return False


def decide_action(analysis):
    """AI ke analysis ke basis pe decide karo kya action lena hai"""
    severity = analysis.get("severity", "high")
    auto_fixable = analysis.get("auto_fixable", False)

    if auto_fixable and severity in ["low", "medium"]:
        return "auto_retry"
    else:
        return "manual_review_needed"


def main():
    failure_report = load_json("latest_failure_report.json")
    analysis = load_json("latest_ai_analysis.json")

    run_id = failure_report["run_id"]

    # Verify karo ki ye report abhi ke latest run ki hi hai, purani stale file nahi hai
    latest_run_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs?per_page=1"
    latest_run_response = requests.get(latest_run_url, headers=HEADERS)
    latest_run_response.raise_for_status()
    current_latest_run = latest_run_response.json()["workflow_runs"][0]

    if current_latest_run["id"] != run_id:
        print("⚠️  'latest_failure_report.json' purani (stale) hai — ye current latest run se match nahi karti.")
        print("Pehle 'python main.py' chala ke fresh report generate karo.")
        return

    if current_latest_run["conclusion"] != "failure":
        print("✅ Latest run me koi failure nahi hai. Self-healing ki zaroorat nahi.")
        return

    print("🩺 Self-Healing Decision Engine\n")
    print(f"Run ID: {run_id}")
    print(f"Root Cause: {analysis['root_cause']}")
    print(f"Severity: {analysis['severity']}")
    print(f"Auto-fixable: {analysis['auto_fixable']}\n")

    missing_module = detect_missing_module(analysis, failure_report)

    if missing_module:
        print(f"🔍 Missing dependency detect hui: '{missing_module}'\n")
        print("🛠️  Self-Heal Action: Dependency ko automatically add kar rahe hain...\n")

        fixed = add_dependency_and_push(missing_module)

        if fixed:
            print("\n🔁 Fix push ho gaya. Workflow ko retry kar rahe hain...\n")
            success = rerun_workflow(run_id)
            if success:
                print(f"✅ Workflow re-run trigger ho gaya (Run ID: {run_id}).")
            else:
                print("❌ Re-run trigger nahi ho paya. GitHub Actions tab manually check karo.")
        return

    action = decide_action(analysis)

    if action == "auto_retry":
        print("✅ Decision: Ye issue chhota hai aur auto-fixable hai. Workflow ko automatically retry kar rahe hain...\n")

        success = rerun_workflow(run_id)

        if success:
            print(f"🔁 Workflow re-run trigger ho gaya (Run ID: {run_id}).")
            print("GitHub Actions tab pe jaake dekh sakte ho naya attempt.")
        else:
            print("❌ Re-run trigger nahi ho paya. Manual check zaroori hai.")

    else:
        print("🚫 Decision: Ye issue risky hai (high severity ya not auto-fixable).")
        print("Self-healing skip kar rahe hain — manual review ki zaroorat hai.")
        print(f"\nSuggested Fix (for human review): {analysis['suggested_fix']}")


if __name__ == "__main__":
    main()