param(
    [string] $SmokeDate = "2026-07-07"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$smokeEnvNames = @(
    "APP_ENV",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_ENABLED",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_BASE_URL",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_DATE",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_TIMEZONE",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_READ_ONLY",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_NON_PROD",
    "URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED",
    "URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED",
    "URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED"
)

function Convert-LocalSecureStringToPlainText {
    param(
        [Parameter(Mandatory = $true)]
        [System.Security.SecureString] $SecureValue
    )

    $bstr = [System.IntPtr]::Zero
    try {
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        if ($bstr -ne [System.IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }
}

function Get-LocalClipboardText {
    try {
        $clipboardValue = Get-Clipboard -ErrorAction Stop
        if ($null -eq $clipboardValue) {
            return ""
        }
        if ($clipboardValue -is [System.Array]) {
            return ($clipboardValue -join "`r`n")
        }
        return [string] $clipboardValue
    }
    catch {
        return ""
    }
}

function Clear-LocalClipboard {
    try {
        Set-Clipboard -Value "" -ErrorAction SilentlyContinue
    }
    catch {
    }
}

function Get-ValidatedSmokeDate {
    param(
        [Parameter(Mandatory = $true)]
        [string] $DateValue
    )

    $candidate = $DateValue.Trim()
    if ($candidate -notmatch "^\d{4}-\d{2}-\d{2}$") {
        throw "Refused: SmokeDate must use YYYY-MM-DD."
    }

    [datetime] $parsedDate = [datetime]::MinValue
    $validDate = [datetime]::TryParseExact(
        $candidate,
        "yyyy-MM-dd",
        [System.Globalization.CultureInfo]::InvariantCulture,
        [System.Globalization.DateTimeStyles]::None,
        [ref] $parsedDate
    )
    if (-not $validDate) {
        throw "Refused: SmokeDate must be a real calendar date."
    }

    return $candidate
}

$previousValues = @{}
$apiRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$authMaterial = $null
$authSecure = $null
$clipboardText = $null
$providerReference = "https://v3.football.api-sports.io/fixtures"
$smokeDateValue = $null

foreach ($envName in $smokeEnvNames) {
    $envItem = Get-Item -LiteralPath "Env:$envName" -ErrorAction SilentlyContinue
    $previousValues[$envName] = @{
        Exists = $null -ne $envItem
        Value = if ($null -ne $envItem) { $envItem.Value } else { $null }
    }
}

try {
    Write-Host "URIM Phase 33 fixture compact smoke runner is local-only. Credentials, provider references and provider content stay off logs and disk."

    $smokeDateValue = Get-ValidatedSmokeDate -DateValue $SmokeDate
    $clipboardText = Get-LocalClipboardText

    if (-not [string]::IsNullOrWhiteSpace($clipboardText)) {
        $authMaterial = $clipboardText.Trim()
    }
    else {
        $authSecure = Read-Host "Enter local API-Football auth material" -AsSecureString
        $authMaterial = Convert-LocalSecureStringToPlainText -SecureValue $authSecure
    }

    if ([string]::IsNullOrWhiteSpace($authMaterial)) {
        throw "Refused: local auth material is required."
    }

    $env:APP_ENV = "development"
    $env:URIM_API_FOOTBALL_FIXTURE_SMOKE_ENABLED = "1"
    $env:URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH = $authMaterial
    $env:URIM_API_FOOTBALL_FIXTURE_SMOKE_BASE_URL = $providerReference
    $env:URIM_API_FOOTBALL_FIXTURE_SMOKE_DATE = $smokeDateValue
    $env:URIM_API_FOOTBALL_FIXTURE_SMOKE_TIMEZONE = "Africa/Kinshasa"
    $env:URIM_API_FOOTBALL_FIXTURE_SMOKE_READ_ONLY = "1"
    $env:URIM_API_FOOTBALL_FIXTURE_SMOKE_NON_PROD = "1"
    $env:URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED = "1"
    $env:URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED = "1"
    $env:URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED = "1"

    Push-Location $apiRoot
    try {
        Write-Host "Running compact fixture smoke script with redacted local credentials."
        python .\scripts\api_football_fixture_first_real_local_smoke.py
        if ($LASTEXITCODE -ne 0) {
            throw "Local fixture compact smoke script failed."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    foreach ($envName in $smokeEnvNames) {
        if ($envName -eq "URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH") {
            Remove-Item -LiteralPath "Env:$envName" -ErrorAction SilentlyContinue
            continue
        }

        $previousValue = $previousValues[$envName]
        if ([bool] $previousValue["Exists"]) {
            Set-Item -LiteralPath "Env:$envName" -Value $previousValue["Value"]
        }
        else {
            Remove-Item -LiteralPath "Env:$envName" -ErrorAction SilentlyContinue
        }
    }

    Clear-LocalClipboard
    $authMaterial = $null
    $authSecure = $null
    $clipboardText = $null
    $providerReference = $null
    $smokeDateValue = $null
    Write-Host "Local fixture compact smoke environment cleaned."
}
