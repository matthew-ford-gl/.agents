# Platform Commands

Platform-specific (PowerShell / Bash) command pairs for the ui-review workflow. Use
whichever matches the current shell. Placeholders in `{braces}` are substituted from
config/state exactly as described in the referring SKILL.md step.

## Screenshot cleanup (Step 0)

PowerShell:
```powershell
if (Test-Path "{appDir}/{screenshotsDir}") {
    Remove-Item "{appDir}/{screenshotsDir}/*" -Recurse -Force
}
```

Bash:
```bash
if [ -d "{appDir}/{screenshotsDir}" ]; then
    rm -rf "{appDir}/{screenshotsDir}"/*
fi
```

## Prerequisite services (Step 3)

PowerShell:
```powershell
$up = (Test-NetConnection localhost -Port {port} -WarningAction SilentlyContinue).TcpTestSucceeded
if (-not $up) {
    Start-Process cmd -ArgumentList "/c {startCommand}" `
        -WorkingDirectory (Resolve-Path "{workingDir}") -NoNewWindow
    Start-Sleep -Seconds {startupDelay}
}
```

Bash:
```bash
if ! nc -z localhost {port} 2>/dev/null; then
    (cd {workingDir} && {startCommand} &)
    sleep {startupDelay}
fi
```

## Capture (Step 4)

PowerShell:
```powershell
$env:{tierEnvVar} = "{tier}"; $env:{routeEnvVar} = "{current}"; npx playwright test --project={playwrightProject}
```

Bash:
```bash
{tierEnvVar}={tier} {routeEnvVar}={current} npx playwright test --project={playwrightProject}
```

Screenshots land in `{appDir}/{screenshotsDir}/{current}--{viewport}.png`.
