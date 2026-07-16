#Requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# The repo must be cloned into the user's home as ~/.agents so the parent of
# $PSScriptRoot is the correct user profile.
$UserRoot = Split-Path -Parent $PSScriptRoot

$canonicalAgentsRoot = Join-Path $PSScriptRoot 'agents'
$canonicalSkillsRoot = Join-Path $PSScriptRoot 'skills'

$claudeRoot = Join-Path $UserRoot '.claude'
$devinRoot = Join-Path $UserRoot 'AppData\Roaming\devin'

function Remove-Safe {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }

    $item = Get-Item -LiteralPath $Path
    if ($item.LinkType -eq 'SymbolicLink') {
        $item.Delete()
    } elseif ($item.PSIsContainer) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    } else {
        Remove-Item -LiteralPath $Path -Force
    }
}

function Install-Agents {
    if (-not (Test-Path $canonicalAgentsRoot)) { return }

    $claudeAgentsDir = Join-Path $claudeRoot 'agents'
    $devinAgentsDir = Join-Path $devinRoot 'agents'
    $claudePresent = Test-Path $claudeRoot
    $devinPresent = Test-Path $devinRoot

    if (-not $claudePresent -and -not $devinPresent) { return }

    if ($claudePresent) {
        New-Item -ItemType Directory -Force -Path $claudeAgentsDir | Out-Null
    }

    foreach ($agentDir in Get-ChildItem -Directory -Path $canonicalAgentsRoot | Sort-Object Name) {
        $name = $agentDir.Name
        $sourceFile = Join-Path $agentDir.FullName 'AGENT.md'

        if (-not (Test-Path $sourceFile)) {
            Write-Warning "SKIP $name — no AGENT.md at $sourceFile"
            continue
        }

        if ($claudePresent) {
            $claudeFile = Join-Path $claudeAgentsDir "$name.md"
            Remove-Safe -Path $claudeFile
            New-Item -ItemType SymbolicLink -Path $claudeFile -Target $sourceFile | Out-Null
            Write-Host "Linked Claude agent: $name"
        }

        if ($devinPresent) {
            $devinFolder = Join-Path $devinAgentsDir $name
            Remove-Safe -Path $devinFolder
            Write-Host "Removed stale Devin agent copy: $name"
        }
    }
}

function Install-Skills {
    if (-not (Test-Path $canonicalSkillsRoot)) { return }

    $claudeSkillsDir = Join-Path $claudeRoot 'skills'
    $devinSkillsDir = Join-Path $devinRoot 'skills'
    $claudePresent = Test-Path $claudeRoot
    $devinPresent = Test-Path $devinRoot

    if (-not $claudePresent -and -not $devinPresent) { return }

    if ($claudePresent) {
        New-Item -ItemType Directory -Force -Path $claudeSkillsDir | Out-Null
    }

    foreach ($skillDir in Get-ChildItem -Directory -Path $canonicalSkillsRoot | Sort-Object Name) {
        $name = $skillDir.Name
        $sourceFolder = $skillDir.FullName
        $sourceFile = Join-Path $sourceFolder 'SKILL.md'

        if (-not (Test-Path $sourceFile)) {
            Write-Warning "SKIP $name — no SKILL.md at $sourceFile"
            continue
        }

        if ($claudePresent) {
            $claudeLink = Join-Path $claudeSkillsDir $name
            Remove-Safe -Path $claudeLink
            New-Item -ItemType SymbolicLink -Path $claudeLink -Target $sourceFolder | Out-Null
            Write-Host "Linked Claude skill: $name"
        }

        if ($devinPresent) {
            $devinDupe = Join-Path $devinSkillsDir $name
            Remove-Safe -Path $devinDupe
            Write-Host "Removed stale Devin skill copy: $name"
        }
    }
}

if (-not (Test-Path $UserRoot)) {
    throw "User root not found: $UserRoot"
}

if (-not (Test-Path $claudeRoot)) {
    Write-Warning "Claude folder not found at $claudeRoot — skipping Claude links"
}
if (-not (Test-Path $devinRoot)) {
    Write-Warning "Devin folder not found at $devinRoot — skipping Devin cleanup"
}

Install-Agents
Install-Skills
