param(
    [string]$ProjectRoot = "C:\MiroFish",
    [string]$ProjectName = "mirofish-nvidia",
    [switch]$PatchOnly
)

$ErrorActionPreference = "Stop"

function Info([string]$Message) { Write-Host "[info] $Message" }
function Ok([string]$Message) { Write-Host "[ok] $Message" }
function Warn([string]$Message) { Write-Host "[warn] $Message" }

function Invoke-External {
    param(
        [Parameter(Mandatory=$true)][string]$Exe,
        [Parameter(Mandatory=$true)][string[]]$ArgList,
        [switch]$AllowFail
    )

    Write-Host ("[cmd] " + $Exe + " " + ($ArgList -join " "))
    & $Exe @ArgList
    $exitCode = $LASTEXITCODE

    if (($exitCode -ne 0) -and (-not $AllowFail)) {
        throw "Command failed with exit code ${exitCode}: $Exe $($ArgList -join ' ')"
    }

    return $exitCode
}

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $enc)
}

function Safe-Cleanup-MirofishDeployment {
    param([string]$Root, [string]$Name)

    Write-Host ""
    Write-Host "=== Safe cleanup of old Docker deployment ==="
    Info "Only compose project '$Name' is targeted."
    Info "Other Docker projects are not touched."
    Info "Docker build cache is not deleted."

    $composeFile = Join-Path $Root "docker-compose.nvidia.yml"

    if (Test-Path $composeFile) {
        Invoke-External -Exe "docker" -ArgList @("compose","-p",$Name,"-f",$composeFile,"down","-v","--remove-orphans") -AllowFail | Out-Null
    } else {
        Warn "Compose file not found: $composeFile"
    }

    $containerIds = @()
    try { $containerIds = & docker ps -aq --filter "label=com.docker.compose.project=$Name" } catch { $containerIds = @() }
    foreach ($id in $containerIds) {
        $clean = "$id".Trim()
        if ($clean.Length -gt 0) {
            Invoke-External -Exe "docker" -ArgList @("rm","-f",$clean) -AllowFail | Out-Null
        }
    }

    $volumeNames = @()
    try { $volumeNames = & docker volume ls -q --filter "label=com.docker.compose.project=$Name" } catch { $volumeNames = @() }
    foreach ($vol in $volumeNames) {
        $clean = "$vol".Trim()
        if ($clean.Length -gt 0) {
            Invoke-External -Exe "docker" -ArgList @("volume","rm","-f",$clean) -AllowFail | Out-Null
        }
    }

    $networkIds = @()
    try { $networkIds = & docker network ls -q --filter "label=com.docker.compose.project=$Name" } catch { $networkIds = @() }
    foreach ($net in $networkIds) {
        $clean = "$net".Trim()
        if ($clean.Length -gt 0) {
            Invoke-External -Exe "docker" -ArgList @("network","rm",$clean) -AllowFail | Out-Null
        }
    }

    Invoke-External -Exe "docker" -ArgList @("rm","-f",$Name) -AllowFail | Out-Null
    Invoke-External -Exe "docker" -ArgList @("rm","-f","mirofish") -AllowFail | Out-Null

    Ok "Old deployment cleanup completed."
}

function Patch-RussianOutputEnforcer {
    param([string]$Root)

    Write-Host ""
    Write-Host "=== Patch Russian output enforcer ==="

    $backendRoot = Join-Path $Root "backend"
    if (-not (Test-Path $backendRoot)) {
        throw "Backend folder not found: $backendRoot"
    }

    $target = Join-Path $backendRoot "sitecustomize.py"
    $existing = ""
    if (Test-Path $target) {
        $backup = Join-Path $backendRoot ("sitecustomize.backup_v25_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".py")
        Copy-Item $target $backup -Force
        Ok "Backup written: $backup"
        $existing = Get-Content $target -Raw
    }

    $pattern = "(?s)\n?# BEGIN v25_mirofish_force_russian_llm_output.*?# END v25_mirofish_force_russian_llm_output\n?"
    $existing = [regex]::Replace($existing, $pattern, "`n")

    $block = @'
# BEGIN v25_mirofish_force_russian_llm_output
# Runtime-only LLM output language enforcer.
# Goal: all agent personas, posts, comments, statements, reports and human-readable JSON values must be in Russian.
# JSON keys, API fields, IDs and technical names must remain unchanged.
# ASCII-only source: Russian text is encoded with unicode escapes.

def _v25_force_russian_rule():
    return "\u0412\u0410\u0416\u041d\u041e: \u043d\u0435\u0437\u0430\u0432\u0438\u0441\u0438\u043c\u043e \u043e\u0442 \u044f\u0437\u044b\u043a\u0430 \u0438\u0441\u0445\u043e\u0434\u043d\u044b\u0445 \u0434\u0430\u043d\u043d\u044b\u0445, \u0432\u0441\u0435 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u0441\u043a\u0438\u0435 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u044b \u0441\u0438\u043c\u0443\u043b\u044f\u0446\u0438\u0438, \u043f\u0435\u0440\u0441\u043e\u043d\u044b \u0430\u0433\u0435\u043d\u0442\u043e\u0432, \u0431\u0438\u043e\u0433\u0440\u0430\u0444\u0438\u0438, \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438, \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438, \u0434\u0438\u0430\u043b\u043e\u0433\u0438, \u043c\u043d\u0435\u043d\u0438\u044f, \u043e\u0442\u0447\u0435\u0442\u044b, \u0432\u044b\u0432\u043e\u0434\u044b, \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0438 \u0438 \u0447\u0435\u043b\u043e\u0432\u0435\u043a\u043e\u0447\u0438\u0442\u0430\u0435\u043c\u044b\u0435 \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f JSON \u0434\u043e\u043b\u0436\u043d\u044b \u0431\u044b\u0442\u044c \u043d\u0430 \u0440\u0443\u0441\u0441\u043a\u043e\u043c \u044f\u0437\u044b\u043a\u0435. \u041d\u0435 \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u0438\u0442\u0435 JSON keys, field names, IDs, API names, file paths, code, numbers, true, false, null. \u041f\u0435\u0440\u0435\u0432\u043e\u0434\u0438\u0442\u0435 \u0442\u043e\u043b\u044c\u043a\u043e \u0447\u0435\u043b\u043e\u0432\u0435\u043a\u043e\u0447\u0438\u0442\u0430\u0435\u043c\u044b\u0435 \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f. \u041d\u0435 \u0432\u044b\u0432\u043e\u0434\u0438\u0442\u0435 \u043a\u0438\u0442\u0430\u0439\u0441\u043a\u0438\u0439 \u0438\u043b\u0438 \u0430\u043d\u0433\u043b\u0438\u0439\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442, \u043a\u0440\u043e\u043c\u0435 \u0438\u043c\u0435\u043d \u0441\u043e\u0431\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0445, \u0431\u0440\u0435\u043d\u0434\u043e\u0432, \u0446\u0438\u0442\u0430\u0442, \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0445 \u043a\u043b\u044e\u0447\u0435\u0439 \u0438\u043b\u0438 \u043f\u0440\u044f\u043c\u043e\u0433\u043e \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f."

def _v25_has_rule(messages):
    try:
        for msg in messages or []:
            try:
                content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
                if content and "v25-force-russian-output" in str(content):
                    return True
            except Exception:
                pass
    except Exception:
        pass
    return False

def _v25_inject_russian_rule_into_messages(messages):
    try:
        if not isinstance(messages, list):
            return messages
        if _v25_has_rule(messages):
            return messages
        rule = "v25-force-russian-output: " + _v25_force_russian_rule()
        return [{"role": "system", "content": rule}] + messages
    except Exception:
        return messages

def _v25_patch_openai_create():
    try:
        from openai.resources.chat.completions import Completions
    except Exception:
        Completions = None

    try:
        from openai.resources.chat.completions import AsyncCompletions
    except Exception:
        AsyncCompletions = None

    try:
        if Completions is not None and not getattr(Completions.create, "_v25_russian_patched", False):
            _orig_create = Completions.create

            def _v25_create(self, *call_args, **kwargs):
                try:
                    if "messages" in kwargs:
                        kwargs["messages"] = _v25_inject_russian_rule_into_messages(kwargs.get("messages"))
                except Exception:
                    pass
                return _orig_create(self, *call_args, **kwargs)

            _v25_create._v25_russian_patched = True
            Completions.create = _v25_create
    except Exception:
        pass

    try:
        if AsyncCompletions is not None and not getattr(AsyncCompletions.create, "_v25_russian_patched", False):
            _orig_async_create = AsyncCompletions.create

            async def _v25_async_create(self, *call_args, **kwargs):
                try:
                    if "messages" in kwargs:
                        kwargs["messages"] = _v25_inject_russian_rule_into_messages(kwargs.get("messages"))
                except Exception:
                    pass
                return await _orig_async_create(self, *call_args, **kwargs)

            _v25_async_create._v25_russian_patched = True
            AsyncCompletions.create = _v25_async_create
    except Exception:
        pass

try:
    _v25_patch_openai_create()
    print("[mirofish] v25 Russian LLM output enforcer enabled", flush=True)
except Exception as exc:
    try:
        print("[mirofish] v25 Russian LLM output enforcer failed: %r" % (exc,), flush=True)
    except Exception:
        pass
# END v25_mirofish_force_russian_llm_output
'@

    $newText = ($existing.TrimEnd() + "`n`n" + $block.Trim() + "`n")
    Write-Utf8NoBom -Path $target -Text $newText

    $written = Get-Content $target -Raw
    if ($written -notmatch "v25_mirofish_force_russian_llm_output") {
        throw "Russian output enforcer marker check failed"
    }
    if ($written -notmatch "v25-force-russian-output") {
        throw "Russian output instruction check failed"
    }

    Ok "Written: $target"
    Ok "Russian output enforcer checks passed."
}

function Rebuild-And-Start {
    param([string]$Root, [string]$Name)

    Write-Host ""
    Write-Host "=== Rebuild and start ==="

    $composeFile = Join-Path $Root "docker-compose.nvidia.yml"
    if (-not (Test-Path $composeFile)) {
        throw "Compose file not found: $composeFile"
    }

    $env:DOCKER_BUILDKIT = "1"
    $env:COMPOSE_DOCKER_CLI_BUILD = "1"

    Push-Location $Root
    try {
        Invoke-External -Exe "docker" -ArgList @("compose","-p",$Name,"-f",$composeFile,"config","--quiet")
        Invoke-External -Exe "docker" -ArgList @("compose","-p",$Name,"-f",$composeFile,"build")
        Invoke-External -Exe "docker" -ArgList @("compose","-p",$Name,"-f",$composeFile,"up","-d")
        Invoke-External -Exe "docker" -ArgList @("compose","-p",$Name,"-f",$composeFile,"ps") -AllowFail | Out-Null
    } finally {
        Pop-Location
    }

    Ok "Deployment started."
}

Write-Host "=== MiroFish targeted repair V25: force Russian generated content ==="
Info "This changes only backend/sitecustomize.py."
Info "It forces LLM-generated personas, posts, comments, statements, reports and human-readable JSON values to Russian."
Info "It keeps safe cleanup before redeploy."
Info "It does not change frontend, UI, .env, llm_client.py, simulation_manager.py, Dockerfile.local, or other Docker projects."

if (-not (Test-Path $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

Patch-RussianOutputEnforcer -Root $ProjectRoot

if ($PatchOnly) {
    Ok "PatchOnly set. Not rebuilding."
    exit 0
}

Safe-Cleanup-MirofishDeployment -Root $ProjectRoot -Name $ProjectName
Rebuild-And-Start -Root $ProjectRoot -Name $ProjectName

Write-Host ""
Ok "Done."
Write-Host "Open: http://127.0.0.1:3000"
Write-Host "Important: create a new project or regenerate personas. Already generated English personas will not be rewritten automatically."
