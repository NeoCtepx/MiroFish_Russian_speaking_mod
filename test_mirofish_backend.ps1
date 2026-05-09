$ErrorActionPreference = "Stop"
Write-Host "Testing MiroFish backend history endpoint..."
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:5001/api/simulation/history?limit=1" | ConvertTo-Json -Depth 20
