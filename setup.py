#!/usr/bin/env python3
"""
SkylightSync Setup Script
Provides interactive setup for either terminal or Docker installation
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

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Docker found")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ Docker not found")
    return False

def check_docker_compose():
    """Check if Docker Compose is available"""
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Docker Compose found")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ Docker Compose not found")
    return False

def setup_terminal():
    """Setup for terminal usage"""
    print("\n🔧 Setting up for terminal usage...")
    
    # Check prerequisites
    check_python_version()
    chrome_ok = check_chrome()
    chromedriver_ok = check_chromedriver()
    
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
    
    print("\n✅ Terminal setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your email credentials")
    print("2. Run: python skylight_sync.py --once")
    print("3. Or run continuously: python skylight_sync.py")
    return True

def setup_docker():
    """Setup for Docker usage"""
    print("\n🐳 Setting up for Docker usage...")
    
    # Check Docker
    if not check_docker():
        print("\n❌ Docker is required for Docker setup")
        print("Install Docker from: https://docs.docker.com/get-docker/")
        return False
    
    if not check_docker_compose():
        print("\n❌ Docker Compose is required for Docker setup")
        print("Install Docker Compose from: https://docs.docker.com/compose/install/")
        return False
    
    # Setup environment
    if not setup_env_file():
        return False
    
    print("\n✅ Docker setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your email credentials")
    print("2. Run: docker-compose up -d")
    print("3. View logs: docker-compose logs -f")
    print("4. Access web UI: http://localhost:5003")
    return True

def main():
    print_banner()
    
    print("Choose your installation method:")
    print("1. Terminal (Recommended for development)")
    print("2. Docker (Recommended for production)")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            success = setup_terminal()
            break
        elif choice == "2":
            success = setup_docker()
            break
        elif choice == "3":
            print("Setup cancelled.")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("Check the README.md for detailed usage instructions.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 