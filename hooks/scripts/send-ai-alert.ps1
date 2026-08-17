# send-ai-alert.ps1 -- Fire-and-forget POST to the AI alert API.
# Called by Devin CLI hooks on Stop and SessionEnd events.
# Always exits 0 so it never blocks the agent.
#
# NOTE: This script previously tried to detect and skip subagent invocations by
# walking the parent process tree looking for a `devin.exe acp` ancestor. That
# heuristic was unreliable and was replaced (see below) with the same
# sessions.db-based `is_subagent` check that send-ai-alert.sh uses, via
# session-info.py.

# -- Version ------------------------------------------------------------------------
# Bump this whenever the script's alerting behavior changes, so alerts in flight
# can be traced back to the version that emitted them.
$ScriptVersion = "1.6.0"

# -- Configuration ----------------------------------------------------------------
$ApiBase = if ($env:ECHO_ALERT_API_BASE) { $env:ECHO_ALERT_API_BASE } else { "https://echo.uk.hos.accessacloud.com" }
$ApiKey = $env:ECHO_ALERT_API_KEY

# -- Read stdin (hook event JSON) --------------------------------------------------
try {
    $Input_ = [Console]::In.ReadToEnd()
    $Event = $Input_ | ConvertFrom-Json -ErrorAction Stop
}
catch {
    $Event = @{}
}

# Helper: safe property read
function Get-JsonVal($obj, $key, $default) {
    if ($obj.PSObject.Properties.Name -contains $key) { return $obj.$key }
    return $default
}

$EventName = Get-JsonVal $Event 'hook_event_name' 'unknown'
$SessionId = Get-JsonVal $Event 'session_id' ''

# -- Look up the session's real title and last agent message from the local
#    Devin CLI sessions.db (SQLite), so alerts show useful context instead of
#    a generic placeholder. Also determines:
#      * IsSubagent: whether this session is itself a subagent (spawned via
#        run_subagent), so we can skip alerting for it -- only the parent
#        session should notify.
#      * HasPendingSubagents: whether the session has launched subagents
#        (background OR foreground) that haven't completed yet. A Stop event
#        while subagents are still pending isn't a real "waiting for you"
#        moment -- the orchestrator will auto-resume once they finish -- so
#        we skip it too.
#    Best-effort: any failure here is silently ignored, and both flags
#    default to $false so we fail open (still alert).
$SessionTitle = $null
$LastMessage = $null
$IsSubagent = $false
$HasPendingSubagents = $false
if ($SessionId) {
    $SessionsDb = Join-Path $env:APPDATA 'devin\cli\sessions.db'
    $HelperScript = Join-Path $PSScriptRoot 'session-info.py'
    if ((Test-Path $SessionsDb) -and (Test-Path $HelperScript) -and (Get-Command python -ErrorAction SilentlyContinue)) {
        try {
            $InfoJson = python $HelperScript $SessionsDb $SessionId 2>$null
            $Info = $InfoJson | ConvertFrom-Json -ErrorAction Stop
            if ($Info.title) { $SessionTitle = $Info.title }
            if ($Info.last_message) { $LastMessage = $Info.last_message }
            if ($Info.is_subagent) { $IsSubagent = [bool]$Info.is_subagent }
            if ($Info.has_pending_subagents) { $HasPendingSubagents = [bool]$Info.has_pending_subagents }
        }
        catch {}
    }
}

# Skip alerts (and the sound) for subagent sessions -- only the parent
# session should notify.
if ($IsSubagent) { exit 0 }

# Skip Stop alerts while subagents (background or foreground) are still
# running -- the orchestrator will auto-resume on its own, so this isn't
# really "waiting for user input". SessionEnd events still alert even with
# pending subagents, since that would mean the session ended abnormally.
if ($EventName -eq 'Stop' -and $HasPendingSubagents) { exit 0 }

# -- Dedupe identical back-to-back alerts -------------------------------------------
# Long-running autonomous tasks (e.g. the ship/quality-audit skills) can end their
# turn more than once with no real progress -- same session, same event, same last
# message -- before anything has actually changed (e.g. waiting out a backend
# retry/rate-limit). Skip sending (and playing the sound for) an exact repeat of the
# same alert within a short cooldown window. Best-effort: any failure here should
# not block a genuinely new alert, so it defaults to "send".
$DedupeScript = Join-Path $PSScriptRoot 'alert-dedupe.py'
if ((Test-Path $DedupeScript) -and (Get-Command python -ErrorAction SilentlyContinue)) {
    try {
        $LastMessageForKey = if ($LastMessage -and $LastMessage.Length -gt 300) { $LastMessage.Substring(0, 300) } else { $LastMessage }
        $DedupeKey = "$SessionId|$EventName|$LastMessageForKey"
        $DedupeResult = python $DedupeScript $DedupeKey 300 2>$null
        if ($DedupeResult -eq 'skip') { exit 0 }
    }
    catch {}
}

# -- Play sound for Stop events ----------------------------------------------------
if ($EventName -eq 'Stop') {
    try {
        (New-Object System.Media.SoundPlayer 'C:/Windows/Media/tada.wav').PlaySync()
    }
    catch {}
}

if (-not $ApiKey) { exit 0 }

$Endpoint = "${ApiBase}/api/alerts/aialert?apikey=${ApiKey}&type=notification"

# -- Derive repo (org/repo) from git remote ----------------------------------------
$Repo = ''
$ProjectDir = if ($env:DEVIN_PROJECT_DIR) { $env:DEVIN_PROJECT_DIR } else { $PWD.Path }

try {
    $null = git -C $ProjectDir rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -eq 0) {
        $RemoteUrl = git -C $ProjectDir remote get-url origin 2>$null
        if ($RemoteUrl) {
            if ($RemoteUrl -match 'dev\.azure\.com') {
                # Azure DevOps: dev.azure.com/org/project/_git/repo -> org/project/repo
                if ($RemoteUrl -match 'dev\.azure\.com/([^/]+)/([^/]+)/_git/(.+)$') {
                    $Repo = "$($Matches[1])/$($Matches[2])/$($Matches[3])" -replace '%20', ' '
                }
            }
            else {
                # GitHub/GitLab SSH or HTTPS: extract org/repo
                $cleaned = $RemoteUrl -replace '\.git$', ''
                if ($cleaned -match '[:/]([^/]+/[^/]+)$') {
                    $Repo = $Matches[1]
                }
            }
        }
    }
}
catch {}

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
}
catch {}

if (-not $TaskDesc) {
    $TaskDesc = "AI session in $Repo"
}

# Prefer the session's actual title (from sessions.db) over the derived guess.
if ($SessionTitle) {
    $TaskDesc = $SessionTitle
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

# Append the agent's last message to the user, when available, so the alert
# shows what actually happened rather than just the generic event reason.
# Truncated to keep the alert payload/notification reasonably sized.
if ($LastMessage) {
    $Truncated = if ($LastMessage.Length -gt 500) { $LastMessage.Substring(0, 500) + '...' } else { $LastMessage }
    $Reason = "$Reason`n`nLast message: $Truncated"
}

# Tag the reason with the emitting script's version, so alerts can be traced
# back to the script version that sent them.
# Include the emitting session's own ID (there's no separate "parent session
# id" recorded in sessions.db for subagents to link back to -- the isolation
# is done purely via the is_subagent/has_pending_subagents content heuristics
# above) so a misfire can be traced straight back to the exact session via
# `python session-info.py <SessionId>` without needing to guess.
$SessionIdSuffix = if ($SessionId) { " | Session: $SessionId" } else { "" }
$Reason = "[send-ai-alert.ps1 v$ScriptVersion] $Reason$SessionIdSuffix"

# -- Timestamp ----------------------------------------------------------------------
$Timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# -- Session URL (no web UI session for local CLI runs) ------------------------------
$SessionUrl = if ($env:DEVIN_SESSION_URL) { $env:DEVIN_SESSION_URL } else { $null }

# -- Build JSON payload -------------------------------------------------------------
$Payload = @{
    taskDescription = $TaskDesc
    repo            = $Repo
    reason          = $Reason
    sessionUrl      = $SessionUrl
    timestamp       = $Timestamp
} | ConvertTo-Json -Compress

if (-not $Payload) { exit 0 }

# -- POST (fire-and-forget) ---------------------------------------------------------
try {
    Invoke-RestMethod -Uri $Endpoint -Method Post -ContentType 'application/json' -Body $Payload -TimeoutSec 10 -ErrorAction SilentlyContinue | Out-Null
}
catch {
    Write-Host "send-ai-alert.ps1: failed to POST alert" -ForegroundColor Red
}

exit 0
