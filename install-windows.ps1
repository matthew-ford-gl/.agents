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

function Install-Hooks {
    if (-not (Test-Path $canonicalHooksFile)) { return }
    if (-not (Test-Path $claudeRoot)) { return }

    $claudeSettingsLocal = Join-Path $claudeRoot 'settings.local.json'
    Remove-Safe -Path $claudeSettingsLocal
    # Try symlink first; fall back to hardlink (no elevation required for files)
    try {
        New-Item -ItemType SymbolicLink -Path $claudeSettingsLocal -Target $canonicalHooksFile -ErrorAction Stop | Out-Null
        Write-Host "Linked hooks: settings.local.json (symlink)"
    } catch {
        New-Item -ItemType HardLink -Path $claudeSettingsLocal -Target $canonicalHooksFile | Out-Null
        Write-Host "Linked hooks: settings.local.json (hardlink)"
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
Install-Hooks

function Test-Link {
    param([string]$Path, [string]$ExpectedTarget)
    if (-not (Test-Path $Path)) {
        return "$Path is missing"
    }
    $item = Get-Item -LiteralPath $Path
    if (-not $item.Target) {
        return "$Path is not a symlink/junction"
    }
    $actual = $item.Target | Select-Object -First 1
    if ($actual -ne $ExpectedTarget) {
        return "$Path points to $actual, expected $ExpectedTarget"
    }
    return $null
}

function Test-NoStaleDevin {
    param([string]$Path, [string]$Name)
    if (Test-Path $Path) {
        return "Stale Devin copy remains: $Name at $Path"
    }
    return $null
}

function Test-Install {
    $failures = [System.Collections.Generic.List[string]]::new()

    # Verify Claude agent symlinks
    if (Test-Path $canonicalAgentsRoot -PathType Container) {
        $claudeAgentsDir = Join-Path $claudeRoot 'agents'
        foreach ($agentDir in Get-ChildItem -Directory -Path $canonicalAgentsRoot | Sort-Object Name) {
            $name = $agentDir.Name
            $sourceFile = Join-Path $agentDir.FullName 'AGENT.md'
            $claudeFile = Join-Path $claudeAgentsDir "$name.md"

            if (-not (Test-Path $sourceFile)) { continue }

            if (Test-Path $claudeRoot) {
                $failure = Test-Link -Path $claudeFile -ExpectedTarget $sourceFile
                if ($failure) { $failures.Add($failure) }
            }

            if (Test-Path $devinRoot) {
                $devinFolder = Join-Path $devinRoot "agents\$name"
                $failure = Test-NoStaleDevin -Path $devinFolder -Name $name
                if ($failure) { $failures.Add($failure) }
            }
        }
    }

    # Verify Claude skill symlinks
    if (Test-Path $canonicalSkillsRoot -PathType Container) {
        $claudeSkillsDir = Join-Path $claudeRoot 'skills'
        foreach ($skillDir in Get-ChildItem -Directory -Path $canonicalSkillsRoot | Sort-Object Name) {
            $name = $skillDir.Name
            $sourceFolder = $skillDir.FullName
            $sourceFile = Join-Path $sourceFolder 'SKILL.md'
            $claudeLink = Join-Path $claudeSkillsDir $name

            if (-not (Test-Path $sourceFile)) { continue }

            if (Test-Path $claudeRoot) {
                $failure = Test-Link -Path $claudeLink -ExpectedTarget $sourceFolder
                if ($failure) { $failures.Add($failure) }
            }

            if (Test-Path $devinRoot) {
                $devinDupe = Join-Path $devinRoot "skills\$name"
                $failure = Test-NoStaleDevin -Path $devinDupe -Name $name
                if ($failure) { $failures.Add($failure) }
            }
        }
    }

    # Verify hooks link (symlink or hardlink)
    if (Test-Path $canonicalHooksFile) {
        if (Test-Path $claudeRoot) {
            $claudeSettingsLocal = Join-Path $claudeRoot 'settings.local.json'
            if (-not (Test-Path $claudeSettingsLocal)) {
                $failures.Add("$claudeSettingsLocal is missing")
            } else {
                $item = Get-Item -LiteralPath $claudeSettingsLocal
                # Accept symlink pointing to the right target, or hardlink (same content)
                if ($item.Target) {
                    $actual = $item.Target | Select-Object -First 1
                    if ($actual -ne $canonicalHooksFile) {
                        $failures.Add("$claudeSettingsLocal points to $actual, expected $canonicalHooksFile")
                    }
                } else {
                    # Hardlink — verify content matches
                    $expected = Get-Content -Raw $canonicalHooksFile
                    $actual = Get-Content -Raw $claudeSettingsLocal
                    if ($expected -ne $actual) {
                        $failures.Add("$claudeSettingsLocal content does not match $canonicalHooksFile")
                    }
                }
            }
        }
    }

    if ($failures.Count -gt 0) {
        throw "Install verification failed:`n$($failures -join "`n")"
    }

    Write-Host "Install verified: all Claude links are correct and no stale Devin copies remain."
}

Test-Install
