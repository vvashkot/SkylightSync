#!/usr/bin/env python3
"""
SkylightSync Setup Script
Provides interactive setup for virtual environment installation
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("           SkylightSync Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_virtual_environment():
    """Check if we're in a virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️  Virtual environment not detected")
        print("It's recommended to run this in a virtual environment:")
        print("  python -m venv venv")
        print("  source venv/bin/activate  # On macOS/Linux")
        print("  venv\\Scripts\\activate     # On Windows")
        return False

def check_chrome():
    """Check if Chrome is installed"""
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "/usr/bin/google-chrome",  # Linux
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Windows
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print("✅ Chrome browser found")
            return True
    
    print("⚠️  Chrome browser not found")
    print("Please install Google Chrome from https://www.google.com/chrome/")
    return False

def check_chromedriver():
    """Check if ChromeDriver is installed"""
    try:
        result = subprocess.run(['chromedriver', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ ChromeDriver found")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("⚠️  ChromeDriver not found")
    return False

def install_chromedriver():
    """Install ChromeDriver"""
    print("\n📦 Installing ChromeDriver...")
    
    if sys.platform == "darwin":  # macOS
        try:
            subprocess.run(['brew', 'install', 'chromedriver'], check=True)
            print("✅ ChromeDriver installed via Homebrew")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install ChromeDriver via Homebrew")
            print("Please install manually: brew install chromedriver")
            return False
    else:
        print("Please install ChromeDriver manually:")
        print("Download from: https://chromedriver.chromium.org/")
        return False

def setup_env_file():
    """Create .env file from template"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ .env.example not found")
        return False
    
    print("\n📝 Creating .env file from template...")
    shutil.copy(env_example, env_file)
    print("✅ .env file created")
    print("⚠️  Please edit .env file with your email credentials")
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment directory already exists")
        return True
    
    print("\n🔧 Creating virtual environment...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print("✅ Virtual environment created")
        print("⚠️  Please activate it and run this setup again:")
        print("   source venv/bin/activate  # On macOS/Linux")
        print("   venv\\Scripts\\activate     # On Windows")
        print("   python setup.py")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment")
        return False

def create_run_script():
    """Create a shell script to run SkylightSync with virtual environment"""
    current_dir = Path.cwd().absolute()
    
    if sys.platform == "win32":
        # Windows batch script
        script_path = current_dir / "run_skylight_sync.bat"
        script_content = f"""@echo off
cd /d "{current_dir}"
call venv\\Scripts\\activate.bat
python skylight_sync.py --once
pause
"""
    else:
        # macOS/Linux shell script
        script_path = current_dir / "run_skylight_sync.sh"
        script_content = f"""#!/bin/bash
cd "{current_dir}"
source venv/bin/activate
python skylight_sync.py --once
"""
    
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable on Unix-like systems
        if sys.platform != "win32":
            os.chmod(script_path, 0o755)
        
        print(f"✅ Run script created: {script_path}")
        return script_path
    except Exception as e:
        print(f"❌ Failed to create run script: {e}")
        return None

def setup_cron_job():
    """Set up a cron job for daily execution"""
    if sys.platform == "win32":
        return setup_windows_task()
    else:
        return setup_unix_cron()

def setup_unix_cron():
    """Set up cron job on macOS/Linux"""
    print("\n⏰ Setting up cron job for daily execution...")
    
    script_path = create_run_script()
    if not script_path:
        return False
    
    # Create cron entry (runs at 9 AM daily)
    cron_line = f"0 9 * * * {script_path} >> {Path.cwd()}/cron.log 2>&1"
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], 
                              capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        
        # Check if our job already exists
        if str(script_path) in current_cron:
            print("✅ Cron job already exists")
            return True
        
        # Add our job
        new_cron = current_cron + cron_line + "\n"
        
        # Install new crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(new_cron)
        
        if process.returncode == 0:
            print("✅ Cron job created successfully")
            print(f"   Runs daily at 9:00 AM")
            print(f"   Script: {script_path}")
            print(f"   Logs: {Path.cwd()}/cron.log")
            return True
        else:
            print("❌ Failed to create cron job")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up cron job: {e}")
        return False

def setup_windows_task():
    """Set up Windows Task Scheduler task"""
    print("\n⏰ Setting up Windows Task Scheduler for daily execution...")
    
    script_path = create_run_script()
    if not script_path:
        return False
    
    task_name = "SkylightSync_Daily"
    
    try:
        # Create task using schtasks
        cmd = [
            'schtasks', '/create',
            '/tn', task_name,
            '/tr', str(script_path),
            '/sc', 'daily',
            '/st', '09:00',
            '/f'  # Force overwrite if exists
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Windows Task created successfully")
            print(f"   Task Name: {task_name}")
            print(f"   Runs daily at 9:00 AM")
            print(f"   Script: {script_path}")
            return True
        else:
            print(f"❌ Failed to create Windows Task: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up Windows Task: {e}")
        return False

def setup_terminal():
    """Setup for terminal usage"""
    print("\n🔧 Setting up SkylightSync...")
    
    # Check prerequisites
    check_python_version()
    venv_ok = check_virtual_environment()
    chrome_ok = check_chrome()
    chromedriver_ok = check_chromedriver()
    
    if not venv_ok:
        print("\n⚠️  Virtual environment recommended but not required")
        response = input("Continue without virtual environment? (y/N): ").strip().lower()
        if response != 'y':
            create_virtual_environment()
            return False
    
    if not chrome_ok:
        print("\n❌ Chrome browser is required")
        return False
    
    if not chromedriver_ok:
        if not install_chromedriver():
            return False
    
    # Install dependencies
    if not install_python_dependencies():
        return False
    
    # Setup environment
    if not setup_env_file():
        return False
    
    # Ask about cron job setup
    print("\n⏰ Automated Scheduling Setup")
    print("Would you like to set up automatic daily sync?")
    if sys.platform == "win32":
        print("This will create a Windows Task Scheduler task to run daily at 9:00 AM")
    else:
        print("This will create a cron job to run daily at 9:00 AM")
    
    response = input("Set up automated daily sync? (y/N): ").strip().lower()
    cron_success = True
    if response == 'y':
        cron_success = setup_cron_job()
    
    print("\n✅ Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your email credentials")
    
    if cron_success and response == 'y':
        print("2. Automated sync is configured - no manual intervention needed!")
        print("3. To test manually, run: python skylight_sync.py --once")
        if sys.platform == "win32":
            print("4. To view/modify the task: Task Scheduler > SkylightSync_Daily")
        else:
            print("4. To view/modify cron job: crontab -e")
            print("5. Check logs at: cron.log")
    else:
        if venv_ok:
            print("2. Run manually: python skylight_sync.py --once")
            print("3. Or run continuously: python skylight_sync.py")
        else:
            print("2. Activate virtual environment: source venv/bin/activate")
            print("3. Run manually: python skylight_sync.py --once")
            print("4. Or run continuously: python skylight_sync.py")
    
    return True

def main():
    print_banner()
    
    print("This will set up SkylightSync for virtual environment usage.")
    print("Virtual environments help isolate dependencies and avoid conflicts.")
    print()
    
    response = input("Continue with setup? (Y/n): ").strip().lower()
    if response == 'n':
        print("Setup cancelled.")
        sys.exit(0)
    
    success = setup_terminal()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("Check the README.md for detailed usage instructions.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 