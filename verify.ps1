# Static verification for the built 1.21.1 (NeoForge) patch jar - no game launch needed.
#
# Usage:
#   .\verify.ps1
#   .\verify.ps1 -Jar dist\goetyownedfix-2.0.0-neoforge-1.21.1.jar

param(
    [string]$Jar = '',
    [string]$ToolsDir = (Join-Path (Split-Path -Parent $PSScriptRoot) '_mc1211_tools'),
    [switch]$Audit
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root

if (-not $Jar) {
    $Jar = Get-ChildItem (Join-Path $root 'dist') -Filter 'goetyownedfix-*.jar' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $Jar -or -not (Test-Path $Jar)) { throw 'No jar to verify. Run .\build.ps1 first.' }

$deps = Join-Path $ToolsDir 'deps'
$goety = Join-Path $deps 'goety-3.1.5.1.jar'
$client = Join-Path $deps 'neoforge-21.1.219-client.jar'
foreach ($p in @($goety, $client)) {
    if (-not (Test-Path $p)) { throw "Missing dependency for verification: $p" }
}

$verifier = Join-Path $root 'tools\verify1211.py'
if (-not (Test-Path $verifier)) { throw "Missing verifier: $verifier" }
$parser = Join-Path $root 'tools\cfparse.py'
if (-not (Test-Path $parser)) { throw "Missing classfile parser: $parser" }

$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { throw 'Python 3 is required for verification.' }

Write-Host "verifying: $Jar"
& $python $verifier $Jar $goety $client $ToolsDir
$rc = $LASTEXITCODE

if ($Audit) {
    $auditor = Join-Path $root 'tools\audit_allied.py'
    if (-not (Test-Path $auditor)) { throw "Missing auditor: $auditor" }
    Write-Host ''
    Write-Host '--- bytecode audit: does Goety 3.1.5.1 still deref a null argument? ---'
    & $python $auditor $goety
    if ($LASTEXITCODE -ne 0) { $rc = $LASTEXITCODE }
}

exit $rc
