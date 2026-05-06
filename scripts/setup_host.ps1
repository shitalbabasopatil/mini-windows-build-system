# Copyright 2026 Shital Babaso Patil <shitalbabasopatil@gmail.com>
# Setup script to verify host requirements for WinBuild Cloud

Write-Host "Checking WinBuild Cloud Host Requirements..." -ForegroundColor Cyan

# 1. Check if running as Admin
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "Please run this script as Administrator to check Windows features."
}

# 2. Check Windows Features
$features = @("Containers", "Hyper-V", "Microsoft-Hyper-V-All")
foreach ($f in $features) {
    $check = Get-WindowsOptionalFeature -Online -FeatureName $f -ErrorAction SilentlyContinue
    if ($check -and $check.State -eq "Enabled") {
        Write-Host "[OK] Feature '$f' is enabled." -ForegroundColor Green
    } else {
        Write-Host "[MISSING] Feature '$f' is NOT enabled." -ForegroundColor Red
    }
}

# 3. Check Docker Desktop
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $dockerInfo = docker info --format '{{.OSType}}'
    if ($dockerInfo -eq "windows") {
        Write-Host "[OK] Docker is running in Windows Containers mode." -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Docker is running in Linux mode. Please switch to Windows Containers." -ForegroundColor Red
    }
} else {
    Write-Host "[ERROR] Docker is not installed or not in PATH." -ForegroundColor Red
}

Write-Host "Setup check complete." -ForegroundColor Cyan
