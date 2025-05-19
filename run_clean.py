
import os
import sys
import subprocess

# Force override the problematic environment variable
os.environ['PADDLE_SANDBOX'] = 'true'  

# Run with clean environment
python_exe = sys.executable
result = subprocess.run([python_exe, 'main.py'], env=os.environ)
sys.exit(result.returncode)
