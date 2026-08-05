# send-ai-alert.ps1 -- Fire-and-forget POST to the AI alert API.
# Called by Devin CLI hooks on Stop and SessionEnd events.
# Always exits 0 so it never blocks the agent.

# -- Configuration ----------------------------------------------------------------
$ApiBase = if ($env:ECHO_ALERT_API_BASE) { $env:ECHO_ALERT_API_BASE } else { "https://echo.uk.hos.accessacloud.com" }
$ApiKey  = $env:ECHO_ALERT_API_KEY

if (-not $ApiKey) { exit 0 }

$Endpoint = "${ApiBase}/api/alerts/aialert?apikey=${ApiKey}&type=standard"

# -- Read stdin (hook event JSON) --------------------------------------------------
try {
    $Input_ = [Console]::In.ReadToEnd()
    $Event  = $Input_ | ConvertFrom-Json -ErrorAction Stop
} catch {
    $Event = @{}
}

# Helper: safe property read
function Get-JsonVal($obj, $key, $default) {
    if ($obj.PSObject.Properties.Name -contains $key) { return $obj.$key }
    return $default
}

$EventName = Get-JsonVal $Event 'hook_event_name' 'unknown'

# -- Derive repo (org/repo) from git remote ----------------------------------------
$Repo       = ''
$ProjectDir = if ($env:DEVIN_PROJECT_DIR) { $env:DEVIN_PROJECT_DIR } else { $PWD.Path }

try {
    $null = git -C $ProjectDir rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -eq 0) {
        $RemoteUrl = git -C $ProjectDir remote get-url origin 2>$null
        if ($RemoteUrl) {
            if ($RemoteUrl -match 'dev\.azure\.com') {
                # Azure DevOps: dev.azure.com/org/project/_git/repo -> org/project/repo
                if ($RemoteUrl -match 'dev\.azure\.com/([^/]+)/([^/]+)/_git/(.+)$') {
                    $Repo = "$($Matches[1])/$($Matches[2])/$($Matches[3])" -replace '%20',' '
                }
            } else {
                # GitHub/GitLab SSH or HTTPS: extract org/repo
                $cleaned = $RemoteUrl -replace '\.git$',''
                if ($cleaned -match '[:/]([^/]+/[^/]+)$') {
                    $Repo = $Matches[1]
                }
            }
        }
    }
} catch {}

# Fallback: use the directory name
if (-not $Repo) {
    $Repo = Split-Path $ProjectDir -Leaf
}

# -- Derive taskDescription from git branch or directory ----------------------------
$TaskDesc = ''
try {
    $null = git -C $ProjectDir rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -eq 0) {
        $Branch = git -C $ProjectDir symbolic-ref --short HEAD 2>$null
        if ($Branch -and $Branch -ne 'main' -and $Branch -ne 'master') {
            $TaskDesc = "Working on branch: $Branch"
        }
    }
} catch {}

if (-not $TaskDesc) {
    $TaskDesc = "AI session in $Repo"
}

# -- Build reason from event type ---------------------------------------------------
switch ($EventName) {
    'Stop' {
        $StopActive = Get-JsonVal $Event 'stop_hook_active' 'false'
        $Reason = "Agent stopped - waiting for user input (stop_hook_active: $StopActive)"
    }
    'SessionEnd' {
        $EndReason = Get-JsonVal $Event 'reason' 'session closed'
        $Reason = "Session ended - $EndReason"
    }
    default {
        $Reason = "Hook event: $EventName"
    }
}

# -- Timestamp ----------------------------------------------------------------------
$Timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# -- Build JSON payload -------------------------------------------------------------
$Payload = @{
    taskDescription = $TaskDesc
    repo            = $Repo
    reason          = $Reason
    timestamp       = $Timestamp
} | ConvertTo-Json -Compress

if (-not $Payload) { exit 0 }

# -- POST (fire-and-forget) ---------------------------------------------------------
try {
    Invoke-RestMethod -Uri $Endpoint -Method Post -ContentType 'application/json' -Body $Payload -TimeoutSec 10 -ErrorAction SilentlyContinue | Out-Null
} catch {}

exit 0
