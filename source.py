import os
import dotenv
from pathlib import Path

# First print all environment files found
root_dir = Path("C:/Users/Ali/Desktop/hellfast")
print("== Environment files found ==")
for file in root_dir.glob("**/.env*"):
    print(f"Found env file: {file}")

# Load each .env file and check PADDLE_SANDBOX value
print("\n== Contents of PADDLE_SANDBOX in each file ==")
for file in root_dir.glob("**/.env*"):
    try:
        env_vars = dotenv.dotenv_values(file)
        if "PADDLE_SANDBOX" in env_vars:
            print(f"{file}: PADDLE_SANDBOX={repr(env_vars['PADDLE_SANDBOX'])}")
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Check current environment variable
print("\n== Current environment ==")
print(f"os.environ['PADDLE_SANDBOX'] = {repr(os.environ.get('PADDLE_SANDBOX', 'Not set'))}")