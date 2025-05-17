import os
import subprocess
import json
import time
import re
import sys
import socket
from threading import Thread

# Instructions
print("Setting up ngrok for Paddle testing:")
print("1. Create a free account at https://ngrok.com/")
print("2. Install required packages")
print("3. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken")

# First install required dependencies
try:
    import pip
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok", "pydantic-settings"])
    print("✅ Packages installed successfully")
except Exception as e:
    print(f"⚠️ Error installing packages: {str(e)}")
    print("Please manually run: pip install pyngrok pydantic-settings")

# Function to check if port is in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Function to monitor FastAPI logs - fixed to handle string output correctly
def monitor_logs(process):
    for line in iter(process.stdout.readline, ''):
        # No need to decode since we're using universal_newlines=True
        print(f"FastAPI: {line.strip()}")

# Function to fix potential Pydantic settings issues
def fix_pydantic_settings_file():
    settings_path = os.path.join(os.getcwd(), 'app', 'core', 'settings.py')
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r') as f:
                content = f.read()
            
            # Check if ClassVar is imported
            if 'from typing import ClassVar' not in content and 'ClassVar' not in content:
                content = content.replace(
                    'from typing import ',
                    'from typing import ClassVar, '
                )
            
            # Fix common non-annotated attributes
            fixes = [
                ('FRONTEND_URL = ', 'FRONTEND_URL: ClassVar[str] = '),
                ('VERCEL_URL = ', 'VERCEL_URL: ClassVar[str] = '),
                ('API_V1_PREFIX = ', 'API_V1_PREFIX: ClassVar[str] = '),
                ('ALGORITHM = ', 'ALGORITHM: ClassVar[str] = '),
                ('SUBSCRIPTION_PLANS = ', 'SUBSCRIPTION_PLANS: ClassVar[Dict[str, Dict[str, Any]]] = ')
            ]
            
            for old, new in fixes:
                content = content.replace(old, new)
            
            # Add ignored_types config if not present
            if 'model_config' not in content:
                config_lines = """
    class Config:
        env_file = ".env"
        model_config = {
            "ignored_types": (ClassVar,)
        }
"""
                content = content.replace(
                    'class Config:\n        env_file = ".env"',
                    config_lines
                )
                
            with open(settings_path, 'w') as f:
                f.write(content)
                
            print("✅ Fixed Pydantic settings file for compatibility with Pydantic 2.x")
            return True
        except Exception as e:
            print(f"⚠️ Could not fix settings file: {str(e)}")
            print("   You'll need to manually add type annotations to class variables in settings.py")
            return False
    return False

try:
    # Kill any existing ngrok processes first to avoid session limits
    print("Checking for existing ngrok processes...")
    if os.name == 'nt':  # Windows
        os.system('taskkill /f /im ngrok.exe >nul 2>&1')
    else:  # Linux/Mac
        os.system('pkill ngrok 2>/dev/null || true')
    print("Starting fresh session...")
    
    # Check if port 8000 is already in use
    if is_port_in_use(8000):
        print("⚠️ Port 8000 is already in use. This might be your FastAPI app or another service.")
        choice = input("Continue with ngrok tunnel anyway? (y/n): ").lower()
        if choice != 'y':
            print("Exiting...")
            sys.exit(1)
    else:
        # Try to fix Pydantic settings before starting app
        print("Checking Pydantic settings compatibility...")
        fix_pydantic_settings_file()
        
        print("Port 8000 is available. Starting FastAPI application...")
        
        # Start FastAPI app with proper output handling
        app_process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )
        
        # Start monitoring logs in a separate thread
        log_thread = Thread(target=monitor_logs, args=(app_process,))
        log_thread.daemon = True
        log_thread.start()
        
        # Wait for FastAPI to start
        print("Waiting for FastAPI to start (15 seconds)...")
        attempts = 0
        while attempts < 30:
            if is_port_in_use(8000):
                print("FastAPI app is running on port 8000!")
                break
            time.sleep(0.5)
            attempts += 1
        
        if not is_port_in_use(8000):
            print("⚠️ FastAPI application doesn't seem to be running on port 8000.")
            print("Check for errors in the output above.")
            choice = input("Continue with ngrok tunnel anyway? (y/n): ").lower()
            if choice != 'y':
                if app_process:
                    app_process.terminate()
                print("Exiting...")
                sys.exit(1)
    
    # Start ngrok tunnel
    from pyngrok import ngrok, conf
    
    # Set up ngrok auth token
    token = input("Enter your ngrok authtoken: ")
    conf.get_default().auth_token = token
    
    print("Starting ngrok tunnel...")
    tunnel_info = ngrok.connect(8000, "http")
    
    # Extract the clean URL using regex
    match = re.search(r'https://[^"]+', str(tunnel_info))
    if match:
        clean_url = match.group(0)
    else:
        clean_url = str(tunnel_info)  # Fallback to the full string if regex fails
    
    print(f"Public URL: {clean_url}")
    print("\nImportant: Update these settings:")
    print(f"1. Set FRONTEND_URL={clean_url} in your .env file")
    print(f"2. Add {clean_url} to your Paddle allowed domains")
    
    # Also update the .env file automatically
    env_file_paths = [
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.getcwd(), 'app', '.env')
    ]
    
    env_updated = False
    for env_path in env_file_paths:
        if os.path.exists(env_path):
            try:
                print(f"Updating .env file at {env_path}")
                # Read current .env file
                with open(env_path, 'r') as f:
                    env_content = f.read()
                
                # Update FRONTEND_URL and PADDLE URLs
                env_content = re.sub(r'FRONTEND_URL=.*', f'FRONTEND_URL={clean_url}', env_content)
                
                # Add PADDLE checkout URLs if they don't exist
                if 'PADDLE_CHECKOUT_SUCCESS_URL' not in env_content:
                    env_content += f'\nPADDLE_CHECKOUT_SUCCESS_URL={clean_url}/subscription/success\n'
                else:
                    env_content = re.sub(r'PADDLE_CHECKOUT_SUCCESS_URL=.*', 
                                     f'PADDLE_CHECKOUT_SUCCESS_URL={clean_url}/subscription/success', env_content)
                
                if 'PADDLE_CHECKOUT_CANCEL_URL' not in env_content:
                    env_content += f'\nPADDLE_CHECKOUT_CANCEL_URL={clean_url}/subscription/cancel\n'
                else:
                    env_content = re.sub(r'PADDLE_CHECKOUT_CANCEL_URL=.*', 
                                     f'PADDLE_CHECKOUT_CANCEL_URL={clean_url}/subscription/cancel', env_content)
                
                # Write updated .env file
                with open(env_path, 'w') as f:
                    f.write(env_content)
                print(f"✅ .env file updated successfully with the new ngrok URL!")
                env_updated = True
            except Exception as e:
                print(f"⚠️ Could not automatically update .env file {env_path}: {str(e)}")
    
    if not env_updated:
        print("⚠️ No .env file found to update")
    
    # Also create or update CORS settings in a runtime file
    cors_file = os.path.join(os.getcwd(), 'app', 'core', 'cors_domains.py')
    try:
        cors_content = f"""# filepath: {cors_file}
# Auto-generated CORS domains file
CORS_DOMAINS = [
    "http://localhost:5173",
    "http://localhost:4173",
    "{clean_url}"
]
"""
        with open(cors_file, 'w') as f:
            f.write(cors_content)
        print(f"✅ CORS settings updated to include the ngrok domain")
    except Exception as e:
        print(f"⚠️ Could not update CORS settings: {str(e)}")
    
    print("\nℹ️ Paddle Setup Instructions:")
    print("1. Go to your Paddle dashboard")
    print("2. Navigate to Developer Tools > Authentication > Integration")
    print(f"3. Add {clean_url} to your approved domains")
    print("4. Save changes and test your checkout")
    
    print("\nPress CTRL+C to stop the tunnel and app")
    
    # Keep alive until interrupted
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("Shutting down...")
    ngrok.kill()
    if 'app_process' in locals():
        app_process.terminate()
    print("Done!")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
