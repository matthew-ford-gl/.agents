$skills = @(
    "analyse-bug",
    "iterate",
    "plan-task",
    "retrospective",
    "review-plans",
    "ship",
    "ui-review",
    "verify-fix"
)

$agentsSkillsRoot = "C:\Users\Matthew.Ford\.agents\skills"
$claudeSkillsRoot = ".\.claude\skills"
$devinAppDataRoot = "$env:APPDATA\devin\skills"

foreach ($name in $skills) {
    $target = Join-Path $agentsSkillsRoot $name
    $claudeLink = Join-Path $claudeSkillsRoot $name
    $devinDupe = Join-Path $devinAppDataRoot $name

    if (-not (Test-Path $target)) {
        Write-Host "SKIP $name — no canonical copy at $target" -ForegroundColor Yellow
        continue
    }

    # Remove the real Claude copy before linking over it
    if (Test-Path $claudeLink) {
        Remove-Item $claudeLink -Recurse -Force
    }

    New-Item -ItemType SymbolicLink -Path $claudeLink -Target $target | Out-Null
    Write-Host "Linked: $claudeLink -> $target"

    # Remove the stale Devin AppData duplicate, since Devin already reads .agents\skills natively
    if (Test-Path $devinDupe) {
        Remove-Item $devinDupe -Recurse -Force
        Write-Host "Removed duplicate: $devinDupe"
    }
}