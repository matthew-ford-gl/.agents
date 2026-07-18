#Requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# The repo must be cloned into the user's home as ~/.agents so the parent of
# $PSScriptRoot is the correct user profile.
$UserRoot = Split-Path -Parent $PSScriptRoot

$canonicalAgentsRoot = Join-Path $PSScriptRoot 'agents'
$canonicalSkillsRoot = Join-Path $PSScriptRoot 'skills'
$canonicalHooksFile  = Join-Path $PSScriptRoot 'hooks\hooks.json'

$claudeRoot = Join-Path $UserRoot '.claude'
$devinRoot = Join-Path $UserRoot 'AppData\Roaming\devin'

function Remove-LinkIfExists {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }

    $item = Get-Item -LiteralPath $Path
    if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        # Only remove reparse points (symbolic links, junctions, etc.), never real files.
        if ($item.PSIsContainer) {
            [System.IO.Directory]::Delete($Path, $false)
        } else {
            [System.IO.File]::Delete($Path)
        }
        Write-Host "Removed: $Path"
    }
}

function Remove-Safe {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }

    $item = Get-Item -LiteralPath $Path
    if ($item.PSIsContainer) {
        # .NET Directory.Delete removes a directory reparse point (symlink/junction)
        # without recursing into the target. For real directories it recurses.
        [System.IO.Directory]::Delete($Path, $true)
    } else {
        [System.IO.File]::Delete($Path)
    }
    Write-Host "Removed: $Path"
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

    # Remove hooks symlink
    $claudeSettingsLocal = Join-Path $claudeRoot 'settings.local.json'
    Remove-LinkIfExists -Path $claudeSettingsLocal
} else {
    Write-Warning "Claude folder not found at $claudeRoot — nothing to remove"
}

if (Test-Path $devinRoot) {
    $devinAgentsDir = Join-Path $devinRoot 'agents'
    $devinSkillsDir = Join-Path $devinRoot 'skills'

    if (Test-Path $canonicalAgentsRoot) {
        foreach ($agentDir in Get-ChildItem -Directory -Path $canonicalAgentsRoot | Sort-Object Name) {
            $devinFolder = Join-Path $devinAgentsDir $agentDir.Name
            Remove-Safe -Path $devinFolder
        }
    }

    if (Test-Path $canonicalSkillsRoot) {
        foreach ($skillDir in Get-ChildItem -Directory -Path $canonicalSkillsRoot | Sort-Object Name) {
            $devinDupe = Join-Path $devinSkillsDir $skillDir.Name
            Remove-Safe -Path $devinDupe
        }
    }
} else {
    Write-Warning "Devin folder not found at $devinRoot — nothing to remove"
}
