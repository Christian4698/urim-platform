Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$smokeEnvNames = @(
    "APP_ENV",
    "URIM_API_FOOTBALL_SMOKE_ENABLED",
    "URIM_API_FOOTBALL_SMOKE_AUTH",
    "URIM_API_FOOTBALL_SMOKE_BASE_URL",
    "URIM_API_FOOTBALL_SMOKE_READ_ONLY",
    "URIM_API_FOOTBALL_SMOKE_NON_PROD",
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

$previousValues = @{}
$apiRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$authMaterial = $null
$providerReference = $null

foreach ($envName in $smokeEnvNames) {
    $envItem = Get-Item -LiteralPath "Env:$envName" -ErrorAction SilentlyContinue
    $previousValues[$envName] = @{
        Exists = $null -ne $envItem
        Value = if ($null -ne $envItem) { $envItem.Value } else { $null }
    }
}

try {
    Write-Host "URIM Phase 24 local-only runner. No secret or provider URL will be displayed or written."

    $authSecure = Read-Host "Enter local API-Football auth material" -AsSecureString
    $referenceSecure = Read-Host "Enter local API-Football provider URL" -AsSecureString

    $authMaterial = Convert-LocalSecureStringToPlainText -SecureValue $authSecure
    $providerReference = Convert-LocalSecureStringToPlainText -SecureValue $referenceSecure

    if ([string]::IsNullOrWhiteSpace($authMaterial)) {
        throw "Refused: local auth material is required."
    }

    if ([string]::IsNullOrWhiteSpace($providerReference)) {
        throw "Refused: local provider URL is required."
    }

    if (-not $providerReference.StartsWith("https://", [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refused: local provider URL must use the https scheme."
    }

    $env:APP_ENV = "development"
    $env:URIM_API_FOOTBALL_SMOKE_ENABLED = "1"
    $env:URIM_API_FOOTBALL_SMOKE_AUTH = $authMaterial
    $env:URIM_API_FOOTBALL_SMOKE_BASE_URL = $providerReference
    $env:URIM_API_FOOTBALL_SMOKE_READ_ONLY = "1"
    $env:URIM_API_FOOTBALL_SMOKE_NON_PROD = "1"
    $env:URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED = "1"
    $env:URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED = "1"
    $env:URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED = "1"

    Push-Location $apiRoot
    try {
        Write-Host "Running local smoke script with redacted operator-provided credentials."
        python .\scripts\api_football_first_real_local_smoke.py
        if ($LASTEXITCODE -ne 0) {
            throw "Local smoke script failed."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    foreach ($envName in $smokeEnvNames) {
        $previousValue = $previousValues[$envName]
        if ([bool] $previousValue["Exists"]) {
            Set-Item -LiteralPath "Env:$envName" -Value $previousValue["Value"]
        }
        else {
            Remove-Item -LiteralPath "Env:$envName" -ErrorAction SilentlyContinue
        }
    }

    $authMaterial = $null
    $providerReference = $null
    Write-Host "Local smoke environment cleaned."
}
