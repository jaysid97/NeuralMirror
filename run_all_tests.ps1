param(
    [switch]$SkipApi,
    [string]$PythonExe
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

if (-not $PythonExe) {
    $PythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
}

if (-not (Test-Path $PythonExe)) {
    throw "Python executable not found at: $PythonExe"
}

$steps = @()
$warnings = @()

function Add-StepResult {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Detail
    )

    $script:steps += [PSCustomObject]@{
        Step = $Name
        Ok = $Ok
        Detail = $Detail
    }
}

function Invoke-PythonStep {
    param(
        [string]$Name,
        [string[]]$CommandArgs,
        [switch]$AllowFailure
    )

    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    & $PythonExe @CommandArgs
    $code = $LASTEXITCODE

    if ($code -ne 0) {
        if ($AllowFailure) {
            Add-StepResult -Name $Name -Ok $false -Detail "Warning: exited with code $code"
            return $false
        }
        throw "$Name failed with exit code $code"
    }

    Add-StepResult -Name $Name -Ok $true -Detail "Passed"
    return $true
}

try {
    Write-Host "Using Python: $PythonExe" -ForegroundColor Yellow

    Invoke-PythonStep -Name "Python Version" -CommandArgs @("-c", "import sys; print(sys.version)") | Out-Null

    Invoke-PythonStep -Name "Syntax Compile" -CommandArgs @(
        "-m", "py_compile",
        "mirror.py",
        "ai_brain.py",
        "pulse_detector.py",
        "voice_output.py",
        "config.py"
    ) | Out-Null

    if ($SkipApi) {
        Add-StepResult -Name "System Verification" -Ok $true -Detail "Skipped (--SkipApi)"
    }
    else {
        Write-Host "`n=== System Verification ===" -ForegroundColor Cyan
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $output = & $PythonExe "test_system.py" 2>&1
        $ErrorActionPreference = $previousPreference
        $output | ForEach-Object { Write-Host $_ }
        $code = $LASTEXITCODE
        $text = (($output | ForEach-Object { $_.ToString() }) | Out-String)

        if ($code -ne 0) {
            throw "test_system.py failed with exit code $code"
        }

        if ($text -match "insufficient_quota|AI Analysis failed") {
            $warnings += "AI call warning: OpenAI quota/key issue detected."
            Add-StepResult -Name "System Verification" -Ok $false -Detail "Warning: AI API quota/key issue"
        }
        else {
            Add-StepResult -Name "System Verification" -Ok $true -Detail "Passed"
        }
    }

    Write-Host "`n=== Summary ===" -ForegroundColor Green
    foreach ($s in $steps) {
        $status = if ($s.Ok) { "PASS" } else { "WARN" }
        Write-Host ("[{0}] {1} - {2}" -f $status, $s.Step, $s.Detail)
    }

    if ($warnings.Count -gt 0) {
        Write-Host "`nWarnings:" -ForegroundColor Yellow
        $warnings | ForEach-Object { Write-Host ("- " + $_) }
    }

    Write-Host "`nDone." -ForegroundColor Green
}
catch {
    Add-StepResult -Name "Runner" -Ok $false -Detail $_.Exception.Message

    Write-Host "`n=== Summary ===" -ForegroundColor Red
    foreach ($s in $steps) {
        $status = if ($s.Ok) { "PASS" } else { "FAIL" }
        Write-Host ("[{0}] {1} - {2}" -f $status, $s.Step, $s.Detail)
    }

    Write-Host "`nRun failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
