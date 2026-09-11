[CmdletBinding()]
param(
    [switch]$SkipPythonDeps,
    # A single comma-separated token, not [string[]]$Runtimes: PowerShell's
    # -File CLI binder only assigns the first bare word to an array parameter
    # under [CmdletBinding()] and rejects the rest ("No positional parameter
    # found"), so a caller passing several runtimes as separate argv entries
    # always failed. Splitting one string here sidesteps that entirely.
    [string]$RuntimesCsv = ''
)

# Installs selected optional runtimes below runtime/toolchains. Python and
# Node.js are core requirements: a portable copy of each is fetched into
# runtime/toolchains when no working system installation is found. Python
# dependencies are always prepared unless -SkipPythonDeps is passed. Nothing
# in this script changes the machine PATH, registry, or a global SDK.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Runtimes = @($RuntimesCsv -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$allowedRuntimes = @('go', 'php', 'java')
$unknownRuntimes = @($Runtimes | Where-Object { $_ -notin $allowedRuntimes })
if ($unknownRuntimes.Count) {
    throw "Unsupported runtime(s): $($unknownRuntimes -join ', '). Supported: $($allowedRuntimes -join ', ')."
}

$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root 'runtime'
$toolchains = Join-Path $runtime 'toolchains'
New-Item -ItemType Directory -Force -Path $toolchains | Out-Null

$progressFile = Join-Path $toolchains '.install-progress.log'
Remove-Item -LiteralPath $progressFile -Force -ErrorAction SilentlyContinue

function Write-InstallProgress([string]$name, [string]$message) {
    $line = "{0}|{1}|{2}" -f (Get-Date -Format 'HH:mm:ss'), $name, $message
    Add-Content -LiteralPath $progressFile -Value $line -Encoding utf8
    Write-Host "[$name] $message"
}

function Fail-Network([string]$name, [object]$errorRecord) {
    throw "[$name] Download metadata or archive failed. Connect to the Internet and rerun start.bat. Details: $($errorRecord.Exception.Message)"
}

function Get-TextContent([string]$uri) {
    # -UseBasicParsing returns .Content as a raw byte[] instead of a decoded
    # string whenever the server sends a non-text Content-Type (e.g. GitHub's
    # release-asset redirects serve SHA256SUMS as application/octet-stream).
    $response = Invoke-WebRequest -Uri $uri -UseBasicParsing
    if ($response.Content -is [byte[]]) {
        return [System.Text.Encoding]::UTF8.GetString($response.Content)
    }
    return $response.Content
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
        if ($archive -match '\.tar\.gz$') {
            # Fully-qualified: a Git-for-Windows bsdtar earlier on PATH treats
            # a bare "C:\..." archive path as remote user@host:path syntax.
            $nativeTar = Join-Path $env:SystemRoot 'System32\tar.exe'
            & $nativeTar -xzf $archive -C $stage
            if ($LASTEXITCODE -ne 0) { throw "tar could not extract $archive." }
        } else {
            Expand-Archive -LiteralPath $archive -DestinationPath $stage -Force
        }
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
    if (Test-Path -LiteralPath (Join-Path $target 'bin\go.exe')) { Write-InstallProgress 'go' 'already installed.'; return }
    Write-InstallProgress 'go' 'fetching the latest stable release manifest...'
    try {
        $release = (Invoke-RestMethod -Uri 'https://go.dev/dl/?mode=json' -UseBasicParsing | Where-Object { $_.stable } | Select-Object -First 1)
        $file = $release.files | Where-Object { $_.filename -match '^go[\d.]+\.windows-amd64\.zip$' } | Select-Object -First 1
        if (-not $file -or -not $file.sha256) { throw 'The official Go release manifest had no Windows amd64 ZIP checksum.' }
    } catch { Fail-Network 'go' $_ }
    Write-InstallProgress 'go' "downloading $($file.filename)..."
    $archive = Join-Path $toolchains $file.filename
    Get-VerifiedArchive 'go' ("https://go.dev/dl/{0}" -f $file.filename) $file.sha256 $archive
    Write-InstallProgress 'go' 'verifying checksum and extracting...'
    Expand-Portable $archive $target 'bin\go.exe' -FlattenOneDirectory
    Write-InstallProgress 'go' 'ready under runtime/toolchains/go.'
}

function Install-Php {
    $target = Join-Path $toolchains 'php'
    if (Test-Path -LiteralPath (Join-Path $target 'php.exe')) { Write-InstallProgress 'php' 'already installed.'; return }
    Write-InstallProgress 'php' 'fetching the latest release checksum manifest...'
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
    Write-InstallProgress 'php' "downloading $($package.File)..."
    $archive = Join-Path $toolchains $package.File
    Get-VerifiedArchive 'php' ("https://windows.php.net/downloads/releases/{0}" -f $package.File) $package.Hash $archive
    Write-InstallProgress 'php' 'verifying checksum and extracting...'
    Expand-Portable $archive $target 'php.exe'
    Write-InstallProgress 'php' 'ready under runtime/toolchains/php.'
}

function Install-Jdk {
    $target = Join-Path $toolchains 'jdk'
    if ((Test-Path -LiteralPath (Join-Path $target 'bin\java.exe')) -and (Test-Path -LiteralPath (Join-Path $target 'bin\javac.exe'))) { Write-InstallProgress 'java' 'already installed.'; return }
    Write-InstallProgress 'java' 'fetching the latest Temurin 21 release manifest...'
    try {
        $asset = Invoke-RestMethod -Uri 'https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=x64&image_type=jdk&os=windows&vendor=eclipse' -UseBasicParsing | Select-Object -First 1
        $package = $asset.binary.package
        if (-not $package.link -or -not $package.checksum -or -not $package.name) { throw 'The Adoptium release manifest was incomplete.' }
    } catch { Fail-Network 'jdk' $_ }
    Write-InstallProgress 'java' "downloading $($package.name)..."
    $archive = Join-Path $toolchains $package.name
    Get-VerifiedArchive 'jdk' $package.link $package.checksum $archive
    Write-InstallProgress 'java' 'verifying checksum and extracting...'
    Expand-Portable $archive $target 'bin\java.exe' -FlattenOneDirectory
    if (-not (Test-Path -LiteralPath (Join-Path $target 'bin\javac.exe'))) { throw '[jdk] Portable JDK is missing javac.exe.' }
    Write-InstallProgress 'java' 'ready under runtime/toolchains/jdk.'
}

function Install-Node {
    $target = Join-Path $toolchains 'node'
    if (Test-Path -LiteralPath (Join-Path $target 'node.exe')) { return }
    if (Get-Command node -ErrorAction SilentlyContinue) { return }
    try {
        $releases = Invoke-RestMethod -Uri 'https://nodejs.org/dist/index.json' -UseBasicParsing
        $release = $releases | Where-Object { $_.lts } | Select-Object -First 1
        if (-not $release) { throw 'The official Node.js release index had no LTS entry.' }
        $fileName = "node-$($release.version)-win-x64.zip"
        $manifest = Get-TextContent "https://nodejs.org/dist/$($release.version)/SHASUMS256.txt"
        $line = ($manifest -split "`n") | Where-Object { $_ -match ('\s' + [regex]::Escape($fileName) + '\s*$') } | Select-Object -First 1
        if (-not $line) { throw "The Node.js checksum manifest for $($release.version) had no entry for $fileName." }
        $hash = ($line -split '\s+')[0]
    } catch { Fail-Network 'node' $_ }
    $archive = Join-Path $toolchains $fileName
    Get-VerifiedArchive 'node' ("https://nodejs.org/dist/{0}/{1}" -f $release.version, $fileName) $hash $archive
    Expand-Portable $archive $target 'node.exe' -FlattenOneDirectory
}

function Install-PortablePython {
    $target = Join-Path $toolchains 'python'
    if (Test-Path -LiteralPath (Join-Path $target 'python.exe')) { return }
    try {
        $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/astral-sh/python-build-standalone/releases/latest' -UseBasicParsing
        $manifest = Get-TextContent ("https://github.com/astral-sh/python-build-standalone/releases/download/{0}/SHA256SUMS" -f $release.tag_name)
        $candidates = foreach ($line in ($manifest -split "`n")) {
            if ($line -match '^\s*([a-fA-F0-9]{64})\s+(cpython-3\.12\.(\d+)\+\d+-x86_64-pc-windows-msvc-install_only\.tar\.gz)\s*$') {
                [pscustomobject]@{ Hash = $matches[1]; File = $matches[2]; Patch = [int]$matches[3] }
            }
        }
        $package = $candidates | Sort-Object Patch -Descending | Select-Object -First 1
        if (-not $package) { throw 'The python-build-standalone release had no supported Windows x86_64 CPython 3.12 build.' }
    } catch { Fail-Network 'python' $_ }
    $archive = Join-Path $toolchains $package.File
    Get-VerifiedArchive 'python' ("https://github.com/astral-sh/python-build-standalone/releases/download/{0}/{1}" -f $release.tag_name, $package.File) $package.Hash $archive
    Expand-Portable $archive $target 'python.exe' -FlattenOneDirectory
}

function Test-RealPython([string]$launcherCmd, [string[]]$launcherArgs) {
    # Windows ships a PATH stub at that name that only opens the Microsoft
    # Store and exits 0 without printing a version - Get-Command alone can't
    # tell it apart from a real interpreter.
    try {
        $output = & $launcherCmd @launcherArgs --version 2>&1
        return ($LASTEXITCODE -eq 0) -and ($output -match '^Python 3')
    } catch {
        return $false
    }
}

function Install-PythonDeps {
    if ($SkipPythonDeps) { return }
    $venv = Join-Path $runtime 'python-venv'
    $python = Join-Path $venv 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        $pyLauncher = $null
        $pyLauncherArgs = @()
        if ((Get-Command py -ErrorAction SilentlyContinue) -and (Test-RealPython 'py' @('-3'))) {
            $pyLauncher = 'py'; $pyLauncherArgs = @('-3')
        } elseif ((Get-Command python -ErrorAction SilentlyContinue) -and (Test-RealPython 'python' @())) {
            $pyLauncher = 'python'
        } else {
            Install-PortablePython
            $pyLauncher = Join-Path $toolchains 'python\python.exe'
        }
        & $pyLauncher @pyLauncherArgs -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw '[python] Could not create runtime\python-venv.' }
    }
    & $python -m pip install --disable-pip-version-check --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw '[python] pip bootstrap failed. Check Internet access and rerun start.bat.' }
    & $python -m pip install --disable-pip-version-check -r (Join-Path $root 'backend-python\requirements.txt') -r (Join-Path $root 'backend-python\requirements-dev.txt')
    if ($LASTEXITCODE -ne 0) { throw '[python] Dependency installation failed. Check Internet access and rerun start.bat.' }
}

try {
    Install-Node
    Install-PythonDeps
    foreach ($runtimeName in ($Runtimes | Select-Object -Unique)) {
        switch ($runtimeName) {
            'go' { Install-Go }
            'php' { Install-Php }
            'java' { Install-Jdk }
        }
    }
} catch {
    Write-InstallProgress 'all' "failed: $($_.Exception.Message)"
    throw
}

if ($Runtimes.Count) {
    Write-InstallProgress 'all' 'done.'
    Write-Host ("[playground] Python dependencies and selected portable runtimes ({0}) are ready under runtime/." -f ($Runtimes -join ', '))
} else {
    Write-Host '[playground] Python dependencies are ready. Optional Go, PHP and Java install only when enabled in Settings.'
}
