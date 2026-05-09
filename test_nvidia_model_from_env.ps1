$ErrorActionPreference = "Stop"
$envPath = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envPath)) { throw ".env not found" }

$map = @{}
foreach ($line in Get-Content $envPath) {
    $t = $line.Trim()
    if ($t.Length -eq 0 -or $t.StartsWith("#")) { continue }
    $idx = $t.IndexOf("=")
    if ($idx -le 0) { continue }
    $k = $t.Substring(0, $idx).Trim()
    $v = $t.Substring($idx + 1).Trim().Trim('"')
    $map[$k] = $v
}

$key = $map["LLM_API_KEY"]
$base = $map["LLM_BASE_URL"].TrimEnd("/")
$model = $map["LLM_MODEL_NAME"]

if (-not $key) { throw "LLM_API_KEY missing" }
if (-not $base) { throw "LLM_BASE_URL missing" }
if (-not $model) { throw "LLM_MODEL_NAME missing" }

$headers = @{
    "Authorization" = "Bearer $key"
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}
$body = @{
    model = $model
    messages = @(
        @{ role = "system"; content = "Reply with OK only." },
        @{ role = "user"; content = "test" }
    )
    max_tokens = 8
    temperature = 0
} | ConvertTo-Json -Depth 12 -Compress

Write-Host "[info] Testing model: $model"
$r = Invoke-RestMethod -Method Post -Uri "$base/chat/completions" -Headers $headers -Body $body -TimeoutSec 90
$r | ConvertTo-Json -Depth 20
Write-Host "[ok] NVIDIA model works"
