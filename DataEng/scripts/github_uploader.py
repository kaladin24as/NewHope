import os
import sys
import subprocess
import shutil

def run_command(command, cwd=None):
    """Run a shell command and print output."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(e.stderr)
        return None

def check_git_installed():
    """Check if git is installed."""
    if not shutil.which("git"):
        print("Error: git is not installed or not in PATH.")
        sys.exit(1)
    print("✅ Git is installed.")

def check_gitignore():
    """Check if .gitignore exists, create if not."""
    gitignore_path = ".gitignore"
    if not os.path.exists(gitignore_path):
        print("⚠️ .gitignore not found. Creating default .gitignore...")
        default_content = """
.venv/
__pycache__/
node_modules/
.env
*.pyc
.DS_Store
dist/
build/
.pytest_cache/
"""
        with open(gitignore_path, "w") as f:
            f.write(default_content.strip())
        print("✅ Created .gitignore.")
    else:
        print("✅ .gitignore exists.")

def init_repo():
    """Initialize git repo if not already initialized."""
    if not os.path.exists(".git"):
        print("Initializing git repository...")
        run_command("git init")
        print("✅ Git repository initialized.")
    else:
        print("✅ Git repository already initialized.")

def configure_user():
    """Ensure git user name and email are set."""
    user_name = run_command("git config user.name")
    user_email = run_command("git config user.email")
    
    if not user_name:
        name = input("Enter your Name for git config: ").strip()
        run_command(f'git config user.name "{name}"')
    
    if not user_email:
        email = input("Enter your Email for git config: ").strip()
        run_command(f'git config user.email "{email}"')

def add_files():
    """Stage all files."""
    print("Staging files...")
    run_command("git add .")
    print("✅ Files staged.")

def commit_changes():
    """Commit changes."""
    status = run_command("git status --porcelain")
    if not status:
        print("Nothing to commit.")
        return False
    
    message = input("Enter commit message (default: 'Initial commit'): ").strip()
    if not message:
        message = "Initial commit"
    
    run_command(f'git commit -m "{message}"')
    print(f"✅ Changes committed with message: '{message}'")
    return True

def setup_remote():
    """Setup remote origin."""
    remotes = run_command("git remote -v")
    if "origin" not in str(remotes):
        print("\n⚠️ No remote 'origin' configured.")
        url = input("Enter the GitHub Repository URL (e.g., https://github.com/user/repo.git): ").strip()
        if url:
            run_command(f"git remote add origin {url}")
            print(f"✅ Remote 'origin' added: {url}")
        else:
            print("❌ No URL provided. Cannot push.")
            return False
    else:
        print("✅ Remote 'origin' already configured.")
    return True

def push_changes():
    """Push changes to remote."""
    print("Pushing to GitHub...")
    # Check current branch name
    branch = run_command("git branch --show-current") or "main"
    
    # Push
    result = run_command(f"git push -u origin {branch}")
    if result is not None:
        print("✅ Successfully pushed to GitHub!")
    else:
        print("❌ Failed to push. You might need to set up credentials or specific token access.")

def main():
    print("🚀 Starting GitHub Upload Agent...")
    project_root = os.getcwd() # Assumes running from root
    print(f"Working directory: {project_root}")
    
    check_git_installed()
    check_gitignore()
    init_repo()
    configure_user()
    add_files()
    if commit_changes() or run_command("git status --porcelain") == "":
        # Proceed if committed or clean, but we might want to push existing commits
        if setup_remote():
            push_changes()
    
    print("\n🎉 Done!")

if __name__ == "__main__":
    main()
