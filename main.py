import json
import re
import os
import urllib.request
import glob
from github import Github
import sys
from pathlib import Path
import subprocess

local = os.environ.get('CI') != 'true'

if local:
    token = None
    print("Running on LOCAL mode!!")
else:
    token  = os.environ.get('GH_TOKEN')
    print("Added token")
    print(f"Token length: {len(token)}")
    
if token is None:
    g = Github()
else:
    g = Github(token)
repo_name = os.environ.get('GITHUB_REPOSITORY')

# if repo_name is None:
#     repo_name = 'KITmetricslab/hospitalization-nowcast-hub'
repo = g.get_repo(repo_name)

print(f"Github repository: {repo_name}")
print(f"Github event name: {os.environ.get('GITHUB_EVENT_NAME')}")