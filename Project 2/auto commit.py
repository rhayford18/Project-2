#Usage:
    #python auto_commit.py                        # uses default message
    #python auto_commit.py "your commit message"  # custom message
 
import subprocess
import sys
import datetime
 
 
def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    return result.returncode
 
 
def auto_commit(message=None):
    if message is None:
        message = f"auto: update {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
 
    print("── Staging changes ───────────────────────")
    run("git add .")
 
    # check if there's anything to commit
    status = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if not status.stdout.strip():
        print("Nothing to commit — working tree clean.")
        return
 
    print(f"── Committing: '{message}' ───────────────")
    code = run(f'git commit -m "{message}"')
    if code != 0:
        print("Commit failed. Make sure git is configured:")
        print("  git config --global user.email 'you@example.com'")
        print("  git config --global user.name  'Your Name'")
        return
 
    print("── Pushing to GitHub ─────────────────────")
    code = run("git push")
    if code == 0:
        print("✅ Successfully pushed to GitHub!")
    else:
        print("Push failed. Check your remote URL and credentials.")
 
 
if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    auto_commit(msg)
 
