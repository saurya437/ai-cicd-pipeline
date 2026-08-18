import os
import json
import anthropic
from dotenv import load_dotenv

# .env file se environment variables load karo
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def load_failure_report(filepath="latest_failure_report.json"):
    """Phase 3 me jo report save ki thi, usko load karo"""
    with open(filepath, "r") as f:
        return json.load(f)


def build_prompt(report):
    """Claude ko bhejne ke liye ek clear prompt banao"""

    # Sab failed jobs ke error lines ko ek text me combine karo
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

    # Kabhi kabhi model markdown backticks laga deta hai, unhe hata do
    cleaned_text = response_text.replace("```json", "").replace("```", "").strip()

    try:
        analysis = json.loads(cleaned_text)
        return analysis
    except json.JSONDecodeError:
        print("⚠️  AI response ko JSON me parse nahi kar paye. Raw response:")
        print(response_text)
        return None


def main():
    report = load_failure_report()

    print(f"Analyzing failure for run: {report['run_id']}")
    print(f"Commit: {report['commit_message']}\n")

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

        # Analysis ko file me save kar do
        with open("latest_ai_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)

        print("\n✅ Analysis 'latest_ai_analysis.json' me save ho gayi.")


if __name__ == "__main__":
    main()