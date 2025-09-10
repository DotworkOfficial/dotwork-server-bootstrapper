#!/usr/bin/env python3
"""
Build script for creating executable
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_exe():
    """Build executable using PyInstaller"""
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip3", "install", "pyinstaller"])
    
    # Build command
    # Use proper separator for add-data (: for Unix, ; for Windows)
    separator = ";" if sys.platform == "win32" else ":"
    
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window (GUI app)
        "--name=DotworkBootstrapper",    # Executable name
        "--icon=icon.ico",              # Icon (if exists)
        f"--add-data=templates{separator}templates",  # Include templates folder
        "--hidden-import=PyQt5.sip",    # Include hidden imports
        "--hidden-import=jinja2",
        "--hidden-import=yaml",
        "main.py"
    ]
    
    # Remove icon option if file doesn't exist
    if not os.path.exists("icon.ico"):
        cmd.remove("--icon=icon.ico")
    
    print("Building executable...")
    print("Command:", " ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        print("\nBuild successful!")
        print("Executable location: dist/DotworkBootstrapper.exe")
        
        # Copy templates to dist folder
        dist_templates = "dist/templates"
        if os.path.exists(dist_templates):
            shutil.rmtree(dist_templates)
        shutil.copytree("templates", dist_templates)
        print("Templates copied to: dist/templates")
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False
    
    return True

def clean_build():
    """Clean build artifacts"""
    paths_to_clean = ["build", "dist", "__pycache__", "*.spec"]
    
    for path in paths_to_clean:
        if "*" in path:
            import glob
            for file in glob.glob(path):
                if os.path.isfile(file):
                    os.remove(file)
                    print(f"Removed: {file}")
        else:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"Removed directory: {path}")
                else:
                    os.remove(path)
                    print(f"Removed file: {path}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_build()
    else:
        if build_exe():
            print("\nBuild completed successfully!")
            print("Ready for distribution!")
        else:
            print("\nBuild failed!")
            sys.exit(1)