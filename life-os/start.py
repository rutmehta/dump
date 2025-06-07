#!/usr/bin/env python3
"""
Life OS Startup Script
Checks dependencies and starts the application with proper error handling.
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        print(f"Current version: {sys.version}")
        return False
    
    if sys.version_info >= (3, 12):
        print(f"✅ Python {sys.version.split()[0]} detected")
        print("ℹ️  Note: Using Python 3.12+ which removed 'distutils' module")
        print("   Updated dependencies to use 'setuptools' instead")
        return True
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_environment_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("📋 Please copy config_template.env to .env and configure your settings:")
        print("   cp config_template.env .env")
        return False
    print("✅ Environment configuration found")
    return True

def check_setuptools():
    """Check if setuptools is available (required for Python 3.12+)"""
    try:
        import setuptools
        print(f"✅ setuptools {setuptools.__version__} available")
        return True
    except ImportError:
        print("❌ setuptools not found")
        print("📦 Installing setuptools (required for Python 3.12+):")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "setuptools>=75.0.0"], check=True)
            print("✅ setuptools installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install setuptools")
            return False

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        from google import genai  # Updated to new Gen AI SDK
        import weaviate
        import neo4j
        import twilio
        print("✅ Core dependencies installed (including new Google Gen AI SDK)")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("📦 Please install dependencies:")
        print("   pip install -r requirements.txt")
        if "google" in str(e):
            print("   Note: Make sure you have the new google-genai package installed")
        if "distutils" in str(e):
            print("   Note: distutils was removed in Python 3.12, using setuptools instead")
        return False

def install_dependencies():
    """Install dependencies with proper error handling"""
    try:
        print("📦 Installing dependencies...")
        # Upgrade pip first to ensure compatibility
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # Install setuptools first for Python 3.12 compatibility
        if sys.version_info >= (3, 12):
            subprocess.run([sys.executable, "-m", "pip", "install", "setuptools>=75.0.0"], check=True)
        
        # Install requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        if sys.version_info >= (3, 12):
            print("💡 Troubleshooting for Python 3.12:")
            print("   1. Some packages may not yet support Python 3.12")
            print("   2. Try using Python 3.11 if you encounter persistent issues")
            print("   3. Ensure you have the latest pip: python -m pip install --upgrade pip")
        return False

def check_storage_directories():
    """Create storage directories if they don't exist"""
    storage_dirs = [
        "storage/media",
        "storage/vector_index", 
        "storage/knowledge_graph_db"
    ]
    
    for dir_path in storage_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Storage directories ready")
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Life OS with Enhanced Gemini Gen AI SDK...")
    print("=" * 60)
    
    # Check Python version first
    if not check_python_version():
        sys.exit(1)
    
    # Check setuptools for Python 3.12+
    if sys.version_info >= (3, 12):
        if not check_setuptools():
            sys.exit(1)
    
    # Check other requirements
    checks = [
        check_environment_file(),
        check_storage_directories()
    ]
    
    # Check dependencies, install if missing
    if not check_dependencies():
        print("\n📦 Dependencies missing, attempting to install...")
        if not install_dependencies():
            print("\n❌ Dependency installation failed")
            print("💡 Manual installation steps:")
            print("   1. pip install --upgrade pip setuptools")
            print("   2. pip install -r requirements.txt")
            sys.exit(1)
        
        # Re-check after installation
        if not check_dependencies():
            print("\n❌ Dependencies still missing after installation")
            sys.exit(1)
    
    if not all(checks):
        print("\n❌ Startup failed - please fix the issues above")
        sys.exit(1)
    
    print("\n✅ All checks passed!")
    print("🌟 Starting Life OS server with:")
    print("   • Gemini 2.0 Flash Experimental model")
    print("   • Enhanced multimodal processing (text, image, audio, video)")
    print("   • 2M token context window")
    print("   • Improved long context capabilities")
    if sys.version_info >= (3, 12):
        print("   • Python 3.12+ compatibility (using setuptools)")
    print("=" * 60)
    
    # Start the application
    try:
        os.chdir(Path(__file__).parent)
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Life OS stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Application failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 