[CmdletBinding()]
param(
    [switch]$SkipPythonDeps
)

# Installs the runtimes used by the snippet runner below runtime/toolchains.
# Nothing in this script changes the machine PATH, registry, or a global SDK.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root 'runtime'
$toolchains = Join-Path $runtime 'toolchains'
New-Item -ItemType Directory -Force -Path $toolchains | Out-Null

function Fail-Network([string]$name, [object]$errorRecord) {
    throw "[$name] Download metadata or archive failed. Connect to the Internet and rerun start.bat. Details: $($errorRecord.Exception.Message)"
}

function Get-VerifiedArchive([string]$name, [string]$uri, [string]$expectedHash, [string]$destination) {
    if (Test-Path -LiteralPath $destination) {
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash.ToLowerInvariant()
        if ($actual -eq $expectedHash.ToLowerInvariant()) { return }
        Remove-Item -LiteralPath $destination -Force
    }
    $partial = "$destination.download"
    Remove-Item -LiteralPath $partial -Force -ErrorAction SilentlyContinue
    try {
        Invoke-WebRequest -Uri $uri -OutFile $partial -UseBasicParsing
    } catch {
        Fail-Network $name $_
    }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $partial).Hash.ToLowerInvariant()
    if ($actual -ne $expectedHash.ToLowerInvariant()) {
        Remove-Item -LiteralPath $partial -Force -ErrorAction SilentlyContinue
        throw "[$name] SHA-256 verification failed for $uri. Expected $expectedHash, got $actual."
    }
    Move-Item -LiteralPath $partial -Destination $destination -Force
}

function Expand-Portable([string]$archive, [string]$target, [string]$executable, [switch]$FlattenOneDirectory) {
    if (Test-Path -LiteralPath (Join-Path $target $executable)) { return }
    $stage = "$target.stage"
    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    try {
        Expand-Archive -LiteralPath $archive -DestinationPath $stage -Force
        $source = $stage
        if ($FlattenOneDirectory) {
            $children = @(Get-ChildItem -LiteralPath $stage -Directory)
            if ($children.Count -ne 1) { throw "Expected one top-level directory in $archive." }
            $source = $children[0].FullName
        }
        Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue
        Move-Item -LiteralPath $source -Destination $target -Force
    } finally {
        Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (-not (Test-Path -LiteralPath (Join-Path $target $executable))) {
        throw "Portable extraction did not produce $executable in $target."
    }
}

function Install-Go {
    $target = Join-Path $toolchains 'go'
    if (Test-Path -LiteralPath (Join-Path $target 'bin\go.exe')) { return }
    try {
        $release = (Invoke-RestMethod -Uri 'https://go.dev/dl/?mode=json' -UseBasicParsing | Where-Object { $_.stable } | Select-Object -First 1)
        $file = $release.files | Where-Object { $_.filename -match '^go[\d.]+\.windows-amd64\.zip$' } | Select-Object -First 1
        if (-not $file -or -not $file.sha256) { throw 'The official Go release manifest had no Windows amd64 ZIP checksum.' }
    } catch { Fail-Network 'go' $_ }
    $archive = Join-Path $toolchains $file.filename
    Get-VerifiedArchive 'go' ("https://go.dev/dl/{0}" -f $file.filename) $file.sha256 $archive
    Expand-Portable $archive $target 'bin\go.exe' -FlattenOneDirectory
}

function Install-Php {
    $target = Join-Path $toolchains 'php'
    if (Test-Path -LiteralPath (Join-Path $target 'php.exe')) { return }
    try {
        $manifest = (Invoke-WebRequest -Uri 'https://windows.php.net/downloads/releases/sha256sum.txt' -UseBasicParsing).Content
        $candidates = foreach ($line in ($manifest -split "`n")) {
            if ($line -match '^\s*([a-fA-F0-9]{64})\s+\*?(php-(\d+)\.(\d+)\.(\d+)-Win32-vs17-x64\.zip)\s*$') {
                [pscustomobject]@{ Hash = $matches[1]; File = $matches[2]; Version = [version]("$($matches[3]).$($matches[4]).$($matches[5])") }
            }
        }
        $package = $candidates | Sort-Object Version -Descending | Select-Object -First 1
        if (-not $package) { throw 'The official PHP checksum manifest had no supported x64 ZIP release.' }
    } catch { Fail-Network 'php' $_ }
    $archive = Join-Path $toolchains $package.File
    Get-VerifiedArchive 'php' ("https://windows.php.net/downloads/releases/{0}" -f $package.File) $package.Hash $archive
    Expand-Portable $archive $target 'php.exe'
}

function Install-Jdk {
    $target = Join-Path $toolchains 'jdk'
    if ((Test-Path -LiteralPath (Join-Path $target 'bin\java.exe')) -and (Test-Path -LiteralPath (Join-Path $target 'bin\javac.exe'))) { return }
    try {
        $asset = Invoke-RestMethod -Uri 'https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=x64&image_type=jdk&os=windows&vendor=eclipse' -UseBasicParsing | Select-Object -First 1
        $package = $asset.binary.package
        if (-not $package.link -or -not $package.checksum -or -not $package.name) { throw 'The Adoptium release manifest was incomplete.' }
    } catch { Fail-Network 'jdk' $_ }
    $archive = Join-Path $toolchains $package.name
    Get-VerifiedArchive 'jdk' $package.link $package.checksum $archive
    Expand-Portable $archive $target 'bin\java.exe' -FlattenOneDirectory
    if (-not (Test-Path -LiteralPath (Join-Path $target 'bin\javac.exe'))) { throw '[jdk] Portable JDK is missing javac.exe.' }
}

function Install-PythonDeps {
    if ($SkipPythonDeps) { return }
    $venv = Join-Path $runtime 'python-venv'
    $python = Join-Path $venv 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        $host = $null
        $hostArgs = @()
        if (Get-Command py -ErrorAction SilentlyContinue) { $host = 'py'; $hostArgs = @('-3') }
        elseif (Get-Command python -ErrorAction SilentlyContinue) { $host = 'python' }
        if (-not $host) { throw '[python] Python 3 is required to create runtime\python-venv. Install Python 3, then rerun start.bat.' }
        & $host @hostArgs -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw '[python] Could not create runtime\python-venv.' }
    }
    & $python -m pip install --disable-pip-version-check --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw '[python] pip bootstrap failed. Check Internet access and rerun start.bat.' }
    & $python -m pip install --disable-pip-version-check -r (Join-Path $root 'backend-python\requirements.txt') -r (Join-Path $root 'backend-python\requirements-dev.txt')
    if ($LASTEXITCODE -ne 0) { throw '[python] Dependency installation failed. Check Internet access and rerun start.bat.' }
}

Install-Go
Install-Php
Install-Jdk
Install-PythonDeps

Write-Host '[playground] Portable Go, PHP, JDK and Python dependencies are ready under runtime/.'
