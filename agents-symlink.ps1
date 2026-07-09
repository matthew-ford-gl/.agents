$agents = @(
    "guardian","craftsman","pragmatist","architect","user-advocate","historian",
    "director","orchestrator","iterative-orchestrator","senior-engineer",
    "qa-gatekeeper","security-analyst","code-reviewer","accessibility-reviewer",
    "dependency-reviewer","docs-updater","migration-reviewer",
    "observability-reviewer","performance-reviewer"
)

$canonicalRoot = "C:\Users\Matthew.Ford\.agents\agents"   # flat .md files live here
$claudeRoot = ".\.claude\agents"
$devinRoot = "$env:APPDATA\devin\agents"

New-Item -ItemType Directory -Force -Path $canonicalRoot | Out-Null

foreach ($name in $agents) {
    $canonicalFile = Join-Path $canonicalRoot "$name.md"
    $existingClaudeFile = Join-Path $claudeRoot "$name.md"
    $existingDevinFile = Join-Path $devinRoot "$name\AGENT.md"

    # Move the current Claude copy to canonical, first time only
    if ((Test-Path $existingClaudeFile) -and -not (Test-Path $canonicalFile)) {
        Move-Item $existingClaudeFile $canonicalFile
    }

    if (-not (Test-Path $canonicalFile)) {
        Write-Host "SKIP $name — no source file found" -ForegroundColor Yellow
        continue
    }

    # Claude: flat symlink
    if (Test-Path $existingClaudeFile) { Remove-Item $existingClaudeFile -Force }
    New-Item -ItemType SymbolicLink -Path $existingClaudeFile -Target $canonicalFile | Out-Null

    # Devin: needs its own folder, then a file symlink named AGENT.md inside it
    $devinFolder = Join-Path $devinRoot $name
    New-Item -ItemType Directory -Force -Path $devinFolder | Out-Null
    if (Test-Path $existingDevinFile) { Remove-Item $existingDevinFile -Force }
    New-Item -ItemType SymbolicLink -Path $existingDevinFile -Target $canonicalFile | Out-Null

    Write-Host "Linked: $name"
}