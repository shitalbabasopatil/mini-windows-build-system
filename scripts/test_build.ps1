$apiUrl = "http://localhost:8000/build"
$localRepoPath = (Get-Item .).FullName.Replace('\', '/')
$repoUrl = "file:///$localRepoPath/sample_app"

$body = @{
    repo_url = $repoUrl
    branch = "main"
    project_path = "./src/App.csproj"
    build_command = "dotnet publish -c Release -o out"
} | ConvertTo-Json

Write-Host "Submitting build request to $apiUrl..." -ForegroundColor Cyan
$response = Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -ContentType "application/json"

$buildId = $response.build_id
Write-Host "Build Submitted! ID: $buildId" -ForegroundColor Green

Write-Host "Polling for logs (Ctrl+C to stop)..." -ForegroundColor Yellow
while ($true) {
    $statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/build/$buildId"
    $logsResponse = Invoke-RestMethod -Uri "http://localhost:8000/build/$buildId/logs"
    
    Clear-Host
    Write-Host "Build ID: $buildId | Status: $($statusResponse.status)" -ForegroundColor White -BackgroundColor Blue
    Write-Host "----------------------------------------------------"
    
    foreach ($log in $logsResponse) {
        Write-Host "[$($log.timestamp)] $($log.message)"
    }
    
    if ($statusResponse.status -eq "SUCCESS" -or $statusResponse.status -eq "FAILED") {
        Write-Host "----------------------------------------------------"
        Write-Host "Build Finished with status: $($statusResponse.status)" -ForegroundColor ($if($statusResponse.status -eq "SUCCESS") {"Green"} else {"Red"})
        break
    }
    
    Start-Sleep -Seconds 2
}
