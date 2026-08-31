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
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if (-not $item) { return }

    if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        if ($item.PSIsContainer) {
            [System.IO.Directory]::Delete($Path, $false)
        } else {
            [System.IO.File]::Delete($Path)
        }
    } elseif ($item.PSIsContainer) {
        [System.IO.Directory]::Delete($Path, $true)
    } else {
        [System.IO.File]::Delete($Path)
    }
}

function ConvertTo-ClaudeDefinition {
    param([string]$Content, [string]$SourcePath)

    $modelMap = @{
        opus   = 'opus'
        sonnet = 'sonnet'
        swe    = 'haiku'
    }
    $frontmatter = [regex]::Match($Content, '\A---\r?\n(?<body>.*?)\r?\n---(?=\r?\n)', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $frontmatter.Success) {
        return $Content
    }

    $modelMatches = [regex]::Matches($frontmatter.Groups['body'].Value, '(?m)^model:[ \t]*(?<model>[A-Za-z0-9_-]+)[ \t]*\r?$')
    if ($modelMatches.Count -eq 0) {
        return $Content
    }
    if ($modelMatches.Count -gt 1) {
        throw "Expected at most one model declaration in $SourcePath, found $($modelMatches.Count)"
    }

    $sourceModel = $modelMatches[0].Groups['model'].Value
    if (-not $modelMap.ContainsKey($sourceModel)) {
        throw "No Claude Code model mapping for '$sourceModel' in $SourcePath"
    }
    $carriageReturn = if ($modelMatches[0].Value.EndsWith("`r")) { "`r" } else { '' }

    $renderedFrontmatter = [regex]::Replace(
        $frontmatter.Value,
        '(?m)^model:[ \t]*[A-Za-z0-9_-]+[ \t]*\r?$',
        "model: $($modelMap[$sourceModel])$carriageReturn"
    )
    return $renderedFrontmatter + $Content.Substring($frontmatter.Length)
}

function Write-ClaudeDefinition {
    param([string]$SourcePath, [string]$DestinationPath)

    $content = [System.IO.File]::ReadAllText($SourcePath)
    $rendered = ConvertTo-ClaudeDefinition -Content $content -SourcePath $SourcePath
    [System.IO.File]::WriteAllText($DestinationPath, $rendered, [System.Text.UTF8Encoding]::new($false))
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
            Write-ClaudeDefinition -SourcePath $sourceFile -DestinationPath $claudeFile
            Write-Host "Rendered Claude agent: $name"
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
            $claudeFolder = Join-Path $claudeSkillsDir $name
            Remove-Safe -Path $claudeFolder
            Copy-Item -LiteralPath $sourceFolder -Destination $claudeFolder -Recurse
            Write-ClaudeDefinition -SourcePath $sourceFile -DestinationPath (Join-Path $claudeFolder 'SKILL.md')
            Write-Host "Rendered Claude skill: $name"
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
        New-Item -ItemType HardLink -Path $claudeSettingsLocal -Value $canonicalHooksFile | Out-Null
        Write-Host "Linked hooks: settings.local.json (hardlink)"
    }
}

function Install-SkillDependencies {
    $python = Get-Command py -ErrorAction SilentlyContinue
    $pythonArgs = @('-3')
    if (-not $python) {
        $python = Get-Command python -ErrorAction SilentlyContinue
        $pythonArgs = @()
    }
    if (-not $python) {
        throw 'Python 3 is required to install screenshot and browser-control dependencies.'
    }

    $screenshotRequirements = Join-Path $canonicalSkillsRoot 'screenshot\requirements.txt'
    $browserRequirements = Join-Path $canonicalSkillsRoot 'browser-control\requirements.txt'
    & $python.Source @pythonArgs -m pip install -r $screenshotRequirements -r $browserRequirements
    if ($LASTEXITCODE -ne 0) { throw 'Failed to install screenshot and browser-control Python dependencies.' }
    & $python.Source @pythonArgs -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw 'Failed to install Playwright Chromium.' }
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

Install-SkillDependencies
Install-Agents
Install-Skills
Install-Hooks

function Test-ClaudeDefinition {
    param([string]$SourcePath, [string]$InstalledPath)
    if (-not (Test-Path $InstalledPath -PathType Leaf)) {
        return "$InstalledPath is missing"
    }
    $item = Get-Item -LiteralPath $InstalledPath
    if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        return "$InstalledPath is still a symlink"
    }

    $source = [System.IO.File]::ReadAllText($SourcePath)
    $expected = ConvertTo-ClaudeDefinition -Content $source -SourcePath $SourcePath
    $actual = [System.IO.File]::ReadAllText($InstalledPath)
    if ($actual -cne $expected) {
        return "$InstalledPath does not match the rendered source definition"
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
                $failure = Test-ClaudeDefinition -SourcePath $sourceFile -InstalledPath $claudeFile
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
            $claudeFolder = Join-Path $claudeSkillsDir $name
            $claudeFile = Join-Path $claudeFolder 'SKILL.md'

            if (-not (Test-Path $sourceFile)) { continue }

            if (Test-Path $claudeRoot) {
                $folderItem = Get-Item -LiteralPath $claudeFolder -ErrorAction SilentlyContinue
                if (-not $folderItem -or ($folderItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
                    $failures.Add("$claudeFolder is missing or still a symlink")
                } else {
                    $failure = Test-ClaudeDefinition -SourcePath $sourceFile -InstalledPath $claudeFile
                    if ($failure) { $failures.Add($failure) }
                }
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

    Write-Host "Install verified: all Claude definitions are rendered correctly and no stale Devin copies remain."
}

Test-Install
