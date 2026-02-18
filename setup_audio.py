#!/usr/bin/env python3
"""
Setup helper script for MindMate audio integration.
Verifies all requirements and OpenAI API access.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python 3.8+ is installed."""
    print("✓ Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ✗ Python 3.8+ required, but found {version.major}.{version.minor}")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro} found")
    return True

def check_pip_packages():
    """Check if required packages are installed."""
    print("\n✓ Checking pip packages...")
    required = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'openai',
        'python-multipart',
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (NOT INSTALLED)")
            missing.append(package)
    
    if missing:
        print(f"\n  Install with: pip install {' '.join(missing)}")
        return False
    return True

def check_openai_api_key():
    """Check if OpenAI API key is configured."""
    print("\n✓ Checking OpenAI API key...")
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("  ✗ OPENAI_API_KEY not set")
        print("  Get key from: https://platform.openai.com/api-keys")
        print("\n  Set with:")
        print("    Windows (PowerShell): $env:OPENAI_API_KEY = 'sk-...'")
        print("    Linux/Mac: export OPENAI_API_KEY='sk-...'")
        return False
    
    if not api_key.startswith('sk-'):
        print(f"  ✗ Invalid key format (should start with 'sk-')")
        return False
    
    print(f"  ✓ API key configured (starts with sk-...{api_key[-4:]})")
    return True

def check_openai_connection():
    """Test connection to OpenAI API."""
    print("\n✓ Testing OpenAI API connection...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Test with a simple query
        response = client.models.list()
        print(f"  ✓ Successfully connected to OpenAI API")
        print(f"  ✓ Available models: {len(response.data)} models found")
        return True
    except Exception as e:
        print(f"  ✗ Failed to connect to OpenAI API: {str(e)}")
        print(f"  Check: API key validity, internet connection, API quota")
        return False

def check_node_installation():
    """Check if Node.js is installed (for frontend)."""
    print("\n✓ Checking Node.js installation...")
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"  ✓ Node.js {version} found")
        return True
    except FileNotFoundError:
        print("  ✗ Node.js not found")
        print("  Download from: https://nodejs.org/")
        return False

def check_npm_packages():
    """Check if npm is available."""
    print("\n✓ Checking npm...")
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"  ✓ npm {version} found")
        return True
    except FileNotFoundError:
        print("  ✗ npm not found (should be included with Node.js)")
        return False

def check_project_structure():
    """Check if required directories exist."""
    print("\n✓ Checking project structure...")
    required_dirs = [
        'backend',
        'backend/agents',
        'backend/graph',
        'frontend',
        'frontend/src',
    ]
    
    missing = []
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ✗ {dir_path}/ (NOT FOUND)")
            missing.append(dir_path)
    
    if missing:
        print(f"\n  Run this script from the project root directory")
        return False
    return True

def run_all_checks():
    """Run all checks and report status."""
    print("=" * 60)
    print("SYNAPSE COUNCIL - Audio Integration Setup Checker")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Pip Packages", check_pip_packages),
        ("OpenAI API Key", check_openai_api_key),
        ("OpenAI Connection", check_openai_connection),
        ("Node.js Installation", check_node_installation),
        ("npm Package Manager", check_npm_packages),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            passed = check_func()
            results.append((name, passed))
        except Exception as e:
            print(f"  ✗ Error during check: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! You're ready to start the services.")
        print("\nNext steps:")
        print("1. Terminal 1: cd backend && python -m uvicorn api:app --reload")
        print("2. Terminal 2: cd frontend && npm run dev")
        print("3. Open http://localhost:3000 in your browser")
    else:
        print("\n✗ Some checks failed. Please fix the issues above and try again.")
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
