#Requires -Version 5.1
[CmdletBinding()]
param(
    # The user's profile/home directory. Defaults to the parent of this .agents repo.
    [string]$UserRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

$canonicalAgentsRoot = Join-Path $PSScriptRoot 'agents'
$canonicalSkillsRoot = Join-Path $PSScriptRoot 'skills'

$claudeRoot = Join-Path $UserRoot '.claude'
$devinRoot = Join-Path $UserRoot 'AppData\Roaming\devin'

function Remove-LinkIfExists {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }

    $item = Get-Item -LiteralPath $Path
    if ($item.LinkType -eq 'SymbolicLink') {
        $item.Delete()
        Write-Host "Removed: $Path"
    }
}

if (-not (Test-Path $UserRoot)) {
    throw "User root not found: $UserRoot"
}

if (Test-Path $claudeRoot) {
    $claudeAgentsDir = Join-Path $claudeRoot 'agents'
    $claudeSkillsDir = Join-Path $claudeRoot 'skills'

    if (Test-Path $canonicalAgentsRoot) {
        foreach ($agentDir in Get-ChildItem -Directory -Path $canonicalAgentsRoot | Sort-Object Name) {
            $claudeFile = Join-Path $claudeAgentsDir "$($agentDir.Name).md"
            Remove-LinkIfExists -Path $claudeFile
        }
    }

    if (Test-Path $canonicalSkillsRoot) {
        foreach ($skillDir in Get-ChildItem -Directory -Path $canonicalSkillsRoot | Sort-Object Name) {
            $claudeLink = Join-Path $claudeSkillsDir $skillDir.Name
            Remove-LinkIfExists -Path $claudeLink
        }
    }
} else {
    Write-Warning "Claude folder not found at $claudeRoot — nothing to remove"
}

if (Test-Path $devinRoot) {
    $devinAgentsDir = Join-Path $devinRoot 'agents'
    $devinSkillsDir = Join-Path $devinRoot 'skills'

    if (Test-Path $canonicalAgentsRoot) {
        foreach ($agentDir in Get-ChildItem -Directory -Path $canonicalAgentsRoot | Sort-Object Name) {
            $devinFolder = Join-Path $devinAgentsDir $agentDir.Name
            Remove-LinkIfExists -Path $devinFolder
        }
    }

    if (Test-Path $canonicalSkillsRoot) {
        foreach ($skillDir in Get-ChildItem -Directory -Path $canonicalSkillsRoot | Sort-Object Name) {
            $devinDupe = Join-Path $devinSkillsDir $skillDir.Name
            Remove-LinkIfExists -Path $devinDupe
        }
    }
} else {
    Write-Warning "Devin folder not found at $devinRoot — nothing to remove"
}
