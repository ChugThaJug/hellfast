"""
Simple script to run the app without ngrok for local testing
"""
import os
import subprocess
import sys

# Install required packages
try:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pydantic-settings"])
    print("✅ Packages installed successfully")
except Exception as e:
    print(f"⚠️ Error installing packages: {str(e)}")

# Run the application
print("Starting the FastAPI application...")
try:
    subprocess.run([sys.executable, "main.py"], check=True)
except KeyboardInterrupt:
    print("Application stopped by user.")
except Exception as e:
    print(f"Error running application: {str(e)}")
