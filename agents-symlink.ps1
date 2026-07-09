$agents = @(
    "guardian","craftsman","pragmatist","architect","user-advocate","historian",
    "director","orchestrator","iterative-orchestrator","senior-engineer",
    "qa-gatekeeper","security-analyst","code-reviewer","accessibility-reviewer",
    "dependency-reviewer","docs-updater","migration-reviewer",
    "observability-reviewer","performance-reviewer"
)

$canonicalRoot = "C:\Users\Matthew.Ford\.agents\agents"
$claudeRoot = "C:\Users\Matthew.Ford\.claude\agents"
$devinRoot = "C:\Users\Matthew.Ford\AppData\Roaming\devin\agents"

New-Item -ItemType Directory -Force -Path $claudeRoot | Out-Null
New-Item -ItemType Directory -Force -Path $devinRoot | Out-Null

foreach ($name in $agents) {
    $canonicalFolder = Join-Path $canonicalRoot $name
    $canonicalFile = Join-Path $canonicalFolder "AGENT.md"

    if (-not (Test-Path $canonicalFile)) {
        Write-Host "SKIP $name — no AGENT.md at $canonicalFile" -ForegroundColor Yellow
        continue
    }

    # Claude: flat file symlink pointing at the canonical AGENT.md
    $claudeFile = Join-Path $claudeRoot "$name.md"
    if (Test-Path $claudeFile) { Remove-Item $claudeFile -Force }
    New-Item -ItemType SymbolicLink -Path $claudeFile -Target $canonicalFile | Out-Null

    # Devin: whole-folder symlink, same shape as canonical already
    $devinFolder = Join-Path $devinRoot $name
    if (Test-Path $devinFolder) { Remove-Item $devinFolder -Recurse -Force }
    New-Item -ItemType SymbolicLink -Path $devinFolder -Target $canonicalFolder | Out-Null

    Write-Host "Linked: $name"
}