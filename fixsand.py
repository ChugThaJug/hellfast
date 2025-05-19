import re
from pathlib import Path

# Path to settings.py
settings_path = Path("app/core/settings.py")
content = settings_path.read_text()

# Create a backup
backup_path = settings_path.with_suffix(".py.bak")
if not backup_path.exists():
    backup_path.write_text(content)
    print(f"Backup created at {backup_path}")

# Find and modify the PADDLE_SANDBOX field
# Look for different patterns of how it might be defined
patterns = [
    r"PADDLE_SANDBOX\s*:\s*bool\s*=\s*.*",  # General pattern
    r"PADDLE_SANDBOX\s*=\s*.*",  # Simple assignment
    r'PADDLE_SANDBOX\s*:\s*bool\s*=\s*Field\(.*\)',  # Field pattern
    r'PADDLE_SANDBOX\s*:\s*bool\s*=\s*os\.getenv\(.*\)'  # os.getenv pattern
]

replacement = "PADDLE_SANDBOX: bool = True  # Hardcoded to bypass env issue"
modified = False

for pattern in patterns:
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        modified = True
        print(f"Modified PADDLE_SANDBOX using pattern: {pattern}")

if modified:
    settings_path.write_text(content)
    print("Settings file updated successfully!")
else:
    print("⚠️ Could not find PADDLE_SANDBOX definition in settings.py")
    print("Please inspect the file manually at:", settings_path.absolute())

# Also create a clean environment runner
runner_path = Path("run_clean.py")
runner_code = """
import os
import sys
import subprocess

# Force override the problematic environment variable
os.environ['PADDLE_SANDBOX'] = 'true'  

# Run with clean environment
python_exe = sys.executable
result = subprocess.run([python_exe, 'main.py'], env=os.environ)
sys.exit(result.returncode)
"""
runner_path.write_text(runner_code)
print(f"Created clean runner at {runner_path}")
print("Run it with: python run_clean.py")