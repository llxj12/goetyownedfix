param(
    # Goety jar used only as a compile-time classpath entry (the mixins subclass its types).
    # Defaults to the newest 1.20.1 (2.x) jar in 修改目标MOD.
    [string]$GoetyJar = '',
    # RevelationFix jar is needed only to compile the RevelationFix caller-side mixins
    # (HereticServant / MaverickServant / ApostleServant).
    # Defaults to the bundled jar found in the workspace (the class usually ships inside
    # GoetyRevelation's JarJar bundle, so a plain mods-folder jar may not exist).
    [string]$RevelationJar = '',
    [string]$Jdk = 'E:\.minecraft\jdk-17.0.18+8',
    # Defaults to the version in META-INF/mods.toml so the jar name can never drift from the metadata.
    [string]$Version = ''
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$root = $PSScriptRoot
$modsToml = Join-Path $root 'META-INF\mods.toml'

function Fail([string]$message) {
    Write-Host "[build] ERROR: $message" -ForegroundColor Red
    exit 1
}

# ---- resolve version ---------------------------------------------------------
if (-not $Version) {
    $match = Select-String -LiteralPath $modsToml -Pattern '^version\s*=\s*"([^"]+)"' | Select-Object -First 1
    if (-not $match) { Fail 'version not found in META-INF/mods.toml' }
    $Version = $match.Matches[0].Groups[1].Value
}
Write-Host "[build] version $Version (from mods.toml)"

# ---- resolve Goety jar -------------------------------------------------------
if (-not $GoetyJar) {
    # The target-mods folder name is non-ASCII, so locate the jar by file name instead
    # of by path literal (PowerShell 5 reads BOM-less scripts as ANSI).
    $candidates = Get-ChildItem -LiteralPath $root -Recurse -Filter '*.jar' -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -notmatch '\\\.recon\\' -and
            $_.Name -match '(^|\s)goety-(\d+\.\d+\.\d+(?:\.\d+)?)\.jar$' -and
            $_.Name -notmatch 'goety-3\.'
        } |
        Sort-Object { [version]($_.Name -replace '^.*goety-([0-9.]+)\.jar$', '$1') } -Descending
    if (-not $candidates) { Fail 'no 1.20.1 goety jar found, pass -GoetyJar explicitly' }
    $GoetyJar = $candidates[0].FullName
}
if (-not (Test-Path -LiteralPath $GoetyJar)) { Fail "Goety jar not found: $GoetyJar" }
Write-Host "[build] classpath goety: $(Split-Path -Leaf $GoetyJar)"

# ---- resolve RevelationFix jar (HereticServant mixin) ------------------------
if (-not $RevelationJar) {
    $rev = Get-ChildItem -LiteralPath $root -Recurse -Filter '*RevelationFix*.jar' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\\META-INF\\' } |
        Sort-Object Length -Descending |
        Select-Object -First 1
    if ($rev) { $RevelationJar = $rev.FullName }
}
if ($RevelationJar -and -not (Test-Path -LiteralPath $RevelationJar)) { Fail "RevelationFix jar not found: $RevelationJar" }
if ($RevelationJar) { Write-Host "[build] classpath revelationfix: $(Split-Path -Leaf $RevelationJar)" }
else { Write-Host "[build] WARNING: no RevelationFix jar found; the RevelationFix servant mixins will not compile" -ForegroundColor Yellow }

# ---- resolve Forge 1.20.1 compile dependencies -------------------------------
$lib = 'E:\.minecraft\libraries'
$compileJars = @(
    (Join-Path $lib 'org\spongepowered\mixin\0.8.5\mixin-0.8.5.jar'),
    (Join-Path $lib 'net\minecraftforge\javafmllanguage\1.20.1-47.4.22\javafmllanguage-1.20.1-47.4.22.jar'),
    (Join-Path $lib 'net\minecraftforge\forge\1.20.1-47.4.22\forge-1.20.1-47.4.22-universal.jar'),
    (Join-Path $lib 'net\minecraft\client\1.20.1-20230612.114412\client-1.20.1-20230612.114412-srg.jar')
) + $GoetyJar
if ($RevelationJar) { $compileJars += $RevelationJar }
foreach ($jar in $compileJars) {
    if (-not (Test-Path -LiteralPath $jar)) { Fail "missing compile dependency: $jar" }
}

$javac = Join-Path $Jdk 'bin\javac.exe'
if (-not (Test-Path -LiteralPath $javac)) { Fail "javac not found: $javac" }

# ---- clean staging -----------------------------------------------------------
$stageName = 'build' + ($Version -replace '\.', '')
$stage = Join-Path $root $stageName
if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage -Force | Out-Null

# ---- compile ----------------------------------------------------------------
$sources = Get-ChildItem -LiteralPath (Join-Path $root 'llxj') -Recurse -Filter '*.java' -File |
    ForEach-Object { $_.FullName }
if (-not $sources) { Fail 'no java sources under llxj' }

Write-Host "[build] compiling $($sources.Count) source files"
# Classes land at the jar root (llxj/...), not under a "classes" folder.
& $javac -encoding UTF-8 -proc:none -source 17 -target 17 -cp ($compileJars -join ';') -d $stage $sources
if ($LASTEXITCODE -ne 0) { Fail "javac failed with exit code $LASTEXITCODE" }

# ---- assemble jar contents ---------------------------------------------------
New-Item -ItemType Directory -Path (Join-Path $stage 'META-INF') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'META-INF\mods.toml') -Destination (Join-Path $stage 'META-INF\mods.toml') -Force
Copy-Item -LiteralPath (Join-Path $root 'mixins.goetyownedfix.json') -Destination $stage -Force
Copy-Item -LiteralPath (Join-Path $root 'pack.mcmeta') -Destination $stage -Force

$manifest = Join-Path $stage 'META-INF\MANIFEST.MF'
$manifestText = @(
    'Manifest-Version: 1.0',
    'Implementation-Title: goetyownedfix',
    "Implementation-Version: $Version",
    'MixinConfigs: mixins.goetyownedfix.json',
    '',
    ''
) -join "`r`n"
# The JAR manifest must be US-ASCII with CRLF line breaks.
[System.IO.File]::WriteAllText($manifest, $manifestText, [System.Text.Encoding]::ASCII)

# ---- package -----------------------------------------------------------------
# ZipFile.CreateFromDirectory on Windows writes backslash entry names, which is not a
# valid JAR; every entry is therefore added manually with forward slashes.
$jarPath = Join-Path $root ("goetyownedfix-$Version.jar")
if (Test-Path -LiteralPath $jarPath) { Remove-Item -LiteralPath $jarPath -Force }

$zip = [System.IO.Compression.ZipFile]::Open($jarPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    $files = @(Get-ChildItem -LiteralPath $stage -Recurse -File)
    # Manifest first (conventional ordering), everything else after.
    $ordered = @($files | Where-Object { $_.Name -eq 'MANIFEST.MF' }) + @($files | Where-Object { $_.Name -ne 'MANIFEST.MF' })
    foreach ($file in $ordered) {
        $relative = $file.FullName.Substring($stage.Length + 1).Replace('\', '/')
        $entry = $zip.CreateEntry($relative, [System.IO.Compression.CompressionLevel]::Optimal)
        # Fixed timestamp so repeated builds of unchanged sources produce the same jar
        # (otherwise every build gets a new SHA-256 and the artifact cannot be verified).
        $entry.LastWriteTime = [DateTimeOffset]::new(2000, 1, 1, 0, 0, 0, [TimeSpan]::Zero)
        $out = $entry.Open()
        $in = [System.IO.File]::OpenRead($file.FullName)
        try { $in.CopyTo($out) } finally { $in.Dispose(); $out.Dispose() }
    }
} finally {
    $zip.Dispose()
}

$hash = (Get-FileHash -LiteralPath $jarPath -Algorithm SHA256).Hash.ToLower()
$read = [System.IO.Compression.ZipFile]::OpenRead($jarPath)
try {
    $names = @($read.Entries | ForEach-Object { $_.FullName })
} finally {
    $read.Dispose()
}
if ($names -match '\\') { Fail 'jar contains backslash entry names' }
if ($names -notcontains 'META-INF/MANIFEST.MF') { Fail 'jar is missing META-INF/MANIFEST.MF' }
if ($names -notcontains 'mixins.goetyownedfix.json') { Fail 'jar is missing mixins.goetyownedfix.json' }

Write-Host "[build] wrote $jarPath"
Write-Host "[build] entries: $($names.Count), size: $((Get-Item -LiteralPath $jarPath).Length) bytes"
Write-Host "[build] sha256: $hash"
