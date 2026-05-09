param(
    [string]$SourceRoot = "C:\MiroFish",
    [string]$PublishRoot = "C:\MiroFish_publish_clean",
    [string]$RepoUrl = "https://github.com/NeoCtepx/MiroFish_Russian_speaking_mod.git",
    [string]$Branch = "main",
    [string]$CommitMessage = "Initial Russian speaking MiroFish mod"
)

$ErrorActionPreference = "Stop"

function Info($m) { Write-Host "[info] $m" }
function Ok($m) { Write-Host "[ok] $m" }
function Fail($m) { throw "[error] $m" }

function Run($exe, [string[]]$argv, [switch]$AllowFail) {
    Write-Host ("[cmd] " + $exe + " " + ($argv -join " "))
    & $exe @argv
    $code = $LASTEXITCODE
    if (($code -ne 0) -and (-not $AllowFail)) {
        Fail "Command failed with exit code ${code}: $exe $($argv -join ' ')"
    }
    return $code
}

function Write-Utf8NoBom($path, $text) {
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($path, $text, $enc)
}

Write-Host "=== MiroFish clean GitHub publish V7 ==="
Info "This script does NOT publish directly from C:\MiroFish."
Info "It creates a clean copy without env/secrets/local data, then pushes that copy."

if (-not (Test-Path $SourceRoot)) {
    Fail "Source folder not found: $SourceRoot"
}

Run "git" @("--version") | Out-Null

if (Test-Path $PublishRoot) {
    Info "Removing old clean publish folder: $PublishRoot"
    Remove-Item -Recurse -Force $PublishRoot
}

New-Item -ItemType Directory -Force -Path $PublishRoot | Out-Null

Write-Host ""
Write-Host "=== Copy safe project files ==="

$xd = @(
    ".git",
    "node_modules",
    ".venv",
    "__pycache__",
    "logs",
    "reports",
    "data",
    "storage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache"
)

$xf = @(
    ".env",
    ".env.*",
    "*.env",
    "*.env.*",
    "*.env.backup*",
    "_mirofish_*_core.py",
    "*_core.py",
    "setup_mirofish_*V*.ps1",
    "setup_mirofish_targeted_repair_V*.ps1",
    "setup_mirofish_safe_redeploy_V*.ps1",
    "setup_mirofish_cache_patch_V*.ps1",
    "setup_mirofish_fixed_redeploy_V*.ps1",
    "publish_mirofish_to_github_safe*.ps1",
    "*.log",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.zip",
    "*.tar",
    "*.tar.gz",
    "*.7z",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "mirofish_nvidia_capacity.json"
)

$robocopyArgs = @($SourceRoot, $PublishRoot, "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/XD") + $xd + @("/XF") + $xf
& robocopy @robocopyArgs
$rc = $LASTEXITCODE
if ($rc -ge 8) {
    Fail "robocopy failed with exit code $rc"
}
Ok "Safe copy created: $PublishRoot"

Write-Host ""
Write-Host "=== Write .gitignore and .env.example in clean copy ==="

$gitignore = @'
.env
.env.*
*.env
*.env.*
*.env.backup*

node_modules/
.venv/
backend/.venv/
frontend/node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd

logs/
reports/
data/
storage/
*.log
*.db
*.sqlite
*.sqlite3

_mirofish_*_core.py
*_core.py
setup_mirofish_*V*.ps1
setup_mirofish_targeted_repair_V*.ps1
setup_mirofish_safe_redeploy_V*.ps1
setup_mirofish_cache_patch_V*.ps1
setup_mirofish_fixed_redeploy_V*.ps1
publish_mirofish_to_github_safe*.ps1

.DS_Store
Thumbs.db
'@
Write-Utf8NoBom (Join-Path $PublishRoot ".gitignore") ($gitignore.TrimEnd() + "`n")

$envExample = @'
LLM_API_KEY=PUT_YOUR_NVIDIA_API_KEY_HERE
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL_NAME=PUT_WORKING_NVIDIA_MODEL_HERE

LLM_BOOST_API_KEY=PUT_YOUR_NVIDIA_API_KEY_HERE
LLM_BOOST_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_BOOST_MODEL_NAME=PUT_WORKING_NVIDIA_MODEL_HERE

ZEP_API_KEY=PUT_YOUR_ZEP_API_KEY_HERE
'@
Write-Utf8NoBom (Join-Path $PublishRoot ".env.example") ($envExample.TrimEnd() + "`n")

Ok ".gitignore and .env.example written"

Write-Host ""
Write-Host "=== Hard safety check ==="

$badFiles = Get-ChildItem -Path $PublishRoot -Recurse -Force -File | Where-Object {
    $_.Name -ne ".env.example" -and (
        $_.Name -eq ".env" -or
        $_.Name -like ".env.*" -or
        $_.Name -like "*.env" -or
        $_.Name -like "*.env.*" -or
        $_.Name -like "*.env.backup*" -or
        $_.Name -like "_mirofish_*_core.py" -or
        $_.Name -like "setup_mirofish_*V*.ps1" -or
        $_.Name -like "publish_mirofish_to_github_safe*.ps1"
    )
}

if ($badFiles.Count -gt 0) {
    Write-Host "Blocked files found in clean copy:"
    $badFiles | ForEach-Object { Write-Host (" - " + $_.FullName) }
    Fail "Clean copy contains blocked files. Stop."
}

$secretHits = @()
$scanFiles = Get-ChildItem -Path $PublishRoot -Recurse -Force -File | Where-Object {
    $_.Length -lt 5MB -and
    $_.Extension -notin @(".png",".jpg",".jpeg",".gif",".webp",".ico",".svg",".pdf",".zip",".7z",".tar",".gz")
}

foreach ($file in $scanFiles) {
    try {
        $txt = Get-Content $file.FullName -Raw -ErrorAction Stop
        if ($txt -match "nvapi-[A-Za-z0-9_\-]{20,}") { $secretHits += $file.FullName; continue }
        if ($txt -match "sk-[A-Za-z0-9_\-]{20,}") { $secretHits += $file.FullName; continue }
    } catch {}
}

if ($secretHits.Count -gt 0) {
    Write-Host "Real-looking secrets found:"
    $secretHits | ForEach-Object { Write-Host (" - " + $_) }
    Fail "Secrets found. Stop."
}

Ok "No blocked env files and no real-looking NVIDIA/OpenAI API tokens found"

Write-Host ""
Write-Host "=== Git init, commit, push ==="

Push-Location $PublishRoot
try {
    Run "git" @("init") | Out-Null
    Run "git" @("branch","-M",$Branch) | Out-Null
    Run "git" @("add",".") | Out-Null

    $trackedEnvRaw = & git ls-files | Select-String -Pattern '(^|/)\.env($|[./_])|\.env\.backup'
    $trackedEnv = @()
    foreach ($hit in $trackedEnvRaw) {
        $line = "$hit"
        if ($line -notmatch '(^|/)\.env\.example$') {
            $trackedEnv += $line
        }
    }
    if ($trackedEnv.Count -gt 0) {
        Write-Host $trackedEnv
        Fail "Env-like file is tracked. Stop."
    }

    Run "git" @("commit","-m",$CommitMessage) | Out-Null
    Run "git" @("remote","add","origin",$RepoUrl) | Out-Null
    Run "git" @("push","-u","origin",$Branch,"--force") | Out-Null
} finally {
    Pop-Location
}

Ok "Pushed clean copy to GitHub: $RepoUrl"
Write-Host ""
Write-Host "Clean publish folder: $PublishRoot"
Write-Host "Your working folder was not used as the git repo: $SourceRoot"
Write-Host "If any key was ever pushed before, revoke/regenerate it anyway."
