# Copyright 2026 Shital Babaso Patil <shitalbabasopatil@gmail.com>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

LABEL author="Shital Babaso Patil"
LABEL email="shitalbabasopatil@gmail.com"

# escape=`
FROM python:3.11-windowsservercore-ltsc2022

WORKDIR C:\app

# Install Git (required for cloning repos)
# We use a simple approach to download and install git or assume it's in the image
# For this demo, we'll use the official python image which might need git.
# Let's install git via PowerShell
RUN powershell -Command `
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; `
    Invoke-WebRequest -Uri https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe -OutFile gitinstall.exe; `
    Start-Process -FilePath .\gitinstall.exe -ArgumentList '/VERYSILENT /NORESTART /NOCANCEL /SP-' -Wait; `
    Remove-Item .\gitinstall.exe

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose API port
EXPOSE 8000

# Start the application
CMD ["python", "main.py"]
