import os
import subprocess
import sys

# Define a function to run pip install commands
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install packages
install("pyautogen~=0.2.0b4")
install("openai==0.28")
install("PyGithub")
install("python-dotenv")
install("pyautogen~=0.2.0b4")
