# Build script for goetyownedfix 1.21.1 (NeoForge) - no Gradle required.
#
# Compiles the mixin-only patch against:
#   - NeoForge 21.1.x (client jar = patched Minecraft, official Mojang names)
#   - Minecraft 1.21.1 client jar
#   - Mixin (sponge-mixin 0.15.2+mixin.0.8.7, ships with NeoForge 1.21.1)
#   - Goety 3.1.5.1 (NeoForge 1.21.1 build) as the mixin target
#
# Usage (PowerShell):
#   .\build.ps1                 # uses ..\_mc1211_tools\jdk\...\bin\javac.exe if present, else PATH javac
#   .\build.ps1 -Javac "C:\path\to\javac.exe"
#
# Output: dist\goetyownedfix-2.0.0-neoforge-1.21.1.jar

param(
    [string]$Javac = '',
    [string]$Jar = '',
    [string]$ToolsDir = (Join-Path (Split-Path -Parent $PSScriptRoot) '_mc1211_tools'),
    [string]$Version = '2.0.0',
    # fixed timestamp for reproducible jars; 2026-09-26T17:00:00Z by default
    [long]$SourceDateEpoch = 1790432400
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root

function Find-Exe([string]$name, [string]$explicit) {
    if ($explicit -and (Test-Path $explicit)) { return $explicit }
    # prefer a JDK shipped next to this project (tools dir), newest version wins
    $cand = Get-ChildItem -Path (Join-Path $ToolsDir 'jdk') -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { Join-Path $_.FullName "bin\$name.exe" } |
        Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($cand) { return $cand }
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw "Cannot find $name. Pass -$(if ($name -eq 'javac') {'Javac'} else {'Jar'}) <path>."
}

$javacExe = Find-Exe 'javac' $Javac
$jarExe = Find-Exe 'jar' $Jar
Write-Host "javac: $javacExe"
Write-Host "jar  : $jarExe"

$mcRoot = 'E:\.minecraft\libraries'
$cpEntries = @(
    (Join-Path $ToolsDir 'deps\neoforge-21.1.219-client.jar'),
    (Join-Path $ToolsDir 'deps\client-1.21.1-20240808.144430-srg.jar'),
    (Join-Path $ToolsDir 'deps\sponge-mixin-0.15.2+mixin.0.8.7.jar'),
    (Join-Path $ToolsDir 'deps\loader-4.0.42.jar'),
    (Join-Path $ToolsDir 'deps\goety-3.1.5.1.jar')
)
# fall back to the live launcher libraries if a copy is missing
$fallbacks = @{
    (Join-Path $ToolsDir 'deps\neoforge-21.1.219-client.jar')        = (Join-Path $mcRoot 'net\neoforged\neoforge\21.1.219\neoforge-21.1.219-client.jar')
    (Join-Path $ToolsDir 'deps\client-1.21.1-20240808.144430-srg.jar') = (Join-Path $mcRoot 'net\minecraft\client\1.21.1-20240808.144430\client-1.21.1-20240808.144430-srg.jar')
    (Join-Path $ToolsDir 'deps\sponge-mixin-0.15.2+mixin.0.8.7.jar')   = (Join-Path $mcRoot 'net\fabricmc\sponge-mixin\0.15.2+mixin.0.8.7\sponge-mixin-0.15.2+mixin.0.8.7.jar')
    (Join-Path $ToolsDir 'deps\loader-4.0.42.jar')                     = (Join-Path $mcRoot 'net\neoforged\fancymodloader\loader\4.0.42\loader-4.0.42.jar')
}
$resolved = @()
foreach ($e in $cpEntries) {
    if (Test-Path $e) { $resolved += $e; continue }
    if ($fallbacks.ContainsKey($e) -and (Test-Path $fallbacks[$e])) { $resolved += $fallbacks[$e]; continue }
    throw "Missing classpath entry: $e"
}
foreach ($e in $resolved) { Write-Host ("  cp: {0} ({1:N1} MB)" -f (Split-Path $e -Leaf), ((Get-Item $e).Length / 1MB)) }

$build = Join-Path $root 'build\classes'
$dist = Join-Path $root 'dist'
Remove-Item $build, $dist -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $build, $dist -Force | Out-Null

$sources = Get-ChildItem (Join-Path $root 'src\main\java') -Recurse -Filter '*.java' | ForEach-Object { $_.FullName }
Write-Host "compiling $($sources.Count) source files ..."
$cp = ($resolved -join ';')
& $javacExe -encoding UTF-8 -proc:none --release 17 -nowarn -cp $cp -d $build @sources
if ($LASTEXITCODE -ne 0) { throw "javac failed with exit code $LASTEXITCODE" }
Write-Host 'javac OK'

# stage resources + manifest
$stage = Join-Path $root 'build\stage'
New-Item -ItemType Directory -Path $stage -Force | Out-Null
Copy-Item (Join-Path $build '*') -Destination $stage -Recurse -Force
Copy-Item (Join-Path $root 'src\main\resources\*') -Destination $stage -Recurse -Force

$manifestPath = Join-Path $root 'build\MANIFEST.MF'
@(
    'Manifest-Version: 1.0',
    'MixinConfigs: mixins.goetyfix.json'
) -join "`r`n" | Set-Content -Path $manifestPath -Encoding ASCII

# Reproducible build: pin every staged file's timestamp to a fixed instant so the
# jar's entry timestamps (and therefore its SHA-256) do not change per build.
# Override with -SourceDateEpoch <unix seconds>.
$stamp = [System.DateTimeOffset]::FromUnixTimeSeconds($SourceDateEpoch).UtcDateTime
Get-ChildItem $stage -Recurse -Force | ForEach-Object {
    $_.LastWriteTimeUtc = $stamp
    $_.CreationTimeUtc = $stamp
}
(Get-Item $stage).LastWriteTimeUtc = $stamp
(Get-Item $stage).CreationTimeUtc = $stamp
$env:SOURCE_DATE_EPOCH = "$SourceDateEpoch"
Write-Host ("pinned timestamps to {0} (SOURCE_DATE_EPOCH={1})" -f $stamp.ToString('u'), $SourceDateEpoch)

$jarName = "goetyownedfix-$Version-neoforge-1.21.1.jar"
$outJar = Join-Path $dist $jarName
& $jarExe --create --file $outJar --manifest $manifestPath -C $stage .
if ($LASTEXITCODE -ne 0) { throw "jar failed with exit code $LASTEXITCODE" }
Remove-Item Env:\SOURCE_DATE_EPOCH -ErrorAction SilentlyContinue
$sha = (Get-FileHash $outJar -Algorithm SHA256).Hash.ToLower()
Write-Host "built: $outJar ($((Get-Item $outJar).Length) bytes)"
Write-Host "sha256: $sha"
