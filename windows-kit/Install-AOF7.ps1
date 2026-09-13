[CmdletBinding()]
param(
    [string]$KitRoot = '',
    [string]$OutputRoot = '',
    [string]$ManifestPath = '',
    [switch]$CheckOnly,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $PSCommandPath
if ([string]::IsNullOrWhiteSpace($KitRoot)) { $KitRoot = $scriptRoot }
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'AOF7-2.5.3'
}
if ($RemainingArguments -contains '--CheckOnly' -or $RemainingArguments -contains '--check-only') {
    $CheckOnly = $true
}

$PythonAssets = @{
    'amd64' = @{ Url = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip'; Sha256 = '4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3' }
    'arm64' = @{ Url = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-arm64.zip'; Sha256 = '3065efc3d382d1cda66757ac71ade11904fa6e350f5a97eb74811acd71ba5532' }
    'x86'   = @{ Url = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-win32.zip'; Sha256 = '084b9eb24cb848605c895d05b738fbc2572efc8b4c18c415a824065864a2b853' }
}
$FabricInstallerUrl = 'https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.0.0/fabric-installer-1.0.0.jar'
$FabricInstallerSha256 = '7d7e5b1d3a7f8e2081069898e95dc71d84bb3a5c79cb235c034895173cfd347b'

function Get-NativeArchitecture {
    $raw = $env:PROCESSOR_ARCHITEW6432
    if ([string]::IsNullOrWhiteSpace($raw)) { $raw = $env:PROCESSOR_ARCHITECTURE }
    switch ($raw.ToUpperInvariant()) {
        'AMD64' { return 'amd64' }
        'ARM64' { return 'arm64' }
        'X86'   { return 'x86' }
        default { throw "Unsupported Windows architecture: $raw" }
    }
}

function Get-PythonAsset {
    $architecture = Get-NativeArchitecture
    $asset = $PythonAssets[$architecture]
    return [pscustomobject]@{ Url = $asset.Url; Sha256 = $asset.Sha256; Architecture = $architecture }
}

function Download-VerifiedFile {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$Sha256,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    $temporary = "$Destination.download"
    if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    Invoke-WebRequest -Uri $Url -OutFile $temporary -UseBasicParsing
    $actual = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Sha256.ToLowerInvariant()) {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        throw "SHA-256 mismatch for downloaded file"
    }
    if (Test-Path -LiteralPath $Destination) { Remove-Item -LiteralPath $Destination -Force }
    Move-Item -LiteralPath $temporary -Destination $Destination -Force | Out-Null
}

function Install-EmbeddedPython {
    param(
        [Parameter(Mandatory = $true)][string]$KitRoot,
        [Parameter(Mandatory = $true)][string]$OutputRoot
    )
    $asset = Get-PythonAsset
    $pythonRoot = Join-Path $OutputRoot 'tools\python'
    $python = Join-Path $pythonRoot 'python.exe'
    New-Item -ItemType Directory -Path $pythonRoot -Force | Out-Null
    if (-not (Test-Path -LiteralPath $python)) {
        $archive = Join-Path $pythonRoot "python-3.12.10-$($asset.Architecture).zip"
        Download-VerifiedFile -Url $asset.Url -Sha256 $asset.Sha256 -Destination $archive
        Expand-Archive -LiteralPath $archive -DestinationPath $pythonRoot -Force
        Remove-Item -LiteralPath $archive -Force
    }
    $version = & $python --version 2>&1
    if ($LASTEXITCODE -ne 0 -or $version -notmatch 'Python 3\.12\.10') {
        throw "Embedded Python validation failed"
    }
    return $python
}

function Test-InstallEnvironment {
    $version = [Environment]::OSVersion.Version
    if ($version.Major -lt 10) { throw 'Windows 10 or newer is required' }
    $documents = [Environment]::GetFolderPath('MyDocuments')
    if ([string]::IsNullOrWhiteSpace($documents) -or -not (Test-Path -LiteralPath $documents)) {
        throw 'The current user Documents folder was not found'
    }
    $probe = Join-Path $documents ".aof7-write-test-$PID"
    try {
        New-Item -ItemType File -Path $probe -Force | Out-Null
    } finally {
        Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
    }
    $root = [IO.Path]::GetPathRoot((Resolve-Path -LiteralPath $documents).Path)
    $driveName = $root.Substring(0, 1)
    $drive = Get-PSDrive -Name $driveName -ErrorAction Stop
    if ($drive.Free -lt 8GB) { throw 'At least 8 GB of free space is required' }
}

function Test-ManifestOnly {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Manifest not found: $Path" }
    $data = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($data.minecraft.version -ne '1.20.1') { throw 'Manifest must target Minecraft 1.20.1' }
    if (@($data.minecraft.modLoaders).Count -ne 1 -or $data.minecraft.modLoaders[0].id -ne 'fabric-0.16.0') {
        throw 'Manifest must use Fabric Loader 0.16.0'
    }
    foreach ($file in @($data.files)) {
        $url = [string]$file.downloadUrl
        try { $uri = [Uri]$url } catch { throw 'Manifest contains an invalid URL' }
        if ($uri.Scheme -ne 'https' -or [string]::IsNullOrWhiteSpace($uri.Host) -or -not [string]::IsNullOrEmpty($uri.UserInfo)) {
            throw 'Manifest contains a non-HTTPS URL or credentials'
        }
        $filenameProperty = $file.PSObject.Properties['filename']
        $name = if ($null -ne $filenameProperty) { [string]$filenameProperty.Value } else { '' }
        if ([string]::IsNullOrWhiteSpace($name)) {
            $name = 'mods/' + [IO.Path]::GetFileName($uri.AbsolutePath)
        }
        $name = [Uri]::UnescapeDataString($name).Replace('\', '/')
        if ($name -notmatch '^mods/[^/]+(/[^/]+)*$' -or $name -match '(^|/)\.\.?(/|$)') {
            throw "Manifest contains an unsafe path: $name"
        }
    }
    [ordered]@{ minecraft = $data.minecraft.version; loader = '0.16.0'; entries = @($data.files).Count } | ConvertTo-Json -Compress
}

function Find-MinecraftJava {
    param([Parameter(Mandatory = $true)][string]$MinecraftRoot)
    $runtimeRoot = Join-Path $MinecraftRoot 'runtime'
    if (Test-Path -LiteralPath $runtimeRoot) {
        $candidate = Get-ChildItem -LiteralPath $runtimeRoot -Recurse -Filter 'java.exe' -File -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $candidate) { return $candidate.FullName }
    }
    $command = Get-Command java.exe -ErrorAction SilentlyContinue
    if ($null -ne $command) { return $command.Source }
    throw 'Java was not found in the official launcher runtime or PATH'
}

function Install-FabricClient {
    param(
        [Parameter(Mandatory = $true)][string]$MinecraftRoot,
        [Parameter(Mandatory = $true)][string]$OutputRoot,
        [Parameter(Mandatory = $true)][string]$JavaPath
    )
    if (-not (Test-Path -LiteralPath $MinecraftRoot -PathType Container)) { throw 'Official Minecraft launcher root was not found' }
    $launcherProfiles = Join-Path $MinecraftRoot 'launcher_profiles.json'
    if (-not (Test-Path -LiteralPath $launcherProfiles -PathType Leaf)) {
        $emptyProfiles = '{"profiles":{}}'
        $temporaryProfiles = "$launcherProfiles.aof7-new"
        $utf8NoBom = New-Object System.Text.UTF8Encoding -ArgumentList $false
        [IO.File]::WriteAllText($temporaryProfiles, $emptyProfiles, $utf8NoBom)
        Move-Item -LiteralPath $temporaryProfiles -Destination $launcherProfiles -Force
    }
    $fabricInstaller = Join-Path $OutputRoot 'tools\fabric-installer-1.0.0.jar'
    New-Item -ItemType Directory -Path (Split-Path -Parent $fabricInstaller) -Force | Out-Null
    Download-VerifiedFile -Url $FabricInstallerUrl -Sha256 $FabricInstallerSha256 -Destination $fabricInstaller
    & $JavaPath -jar $fabricInstaller client -dir $MinecraftRoot -mcversion 1.20.1 -loader 0.16.0 -launcher win32
    if ($LASTEXITCODE -ne 0) { throw "Fabric installer failed with exit code $LASTEXITCODE" }
    $versionDir = Join-Path $MinecraftRoot 'versions\fabric-loader-0.16.0-1.20.1'
    if (-not (Test-Path -LiteralPath $versionDir -PathType Container)) { throw 'Fabric version directory was not created' }
}

function Write-LaunchCommand {
    param([Parameter(Mandatory = $true)][string]$OutputRoot)
    $launch = Join-Path $OutputRoot 'AOF7-2.5.3-launch.cmd'
    $content = '@echo off' + [Environment]::NewLine + 'start "" "minecraft:"' + [Environment]::NewLine
    $content | Set-Content -LiteralPath $launch -Encoding ASCII
    return $launch
}

$LogPath = Join-Path $OutputRoot 'logs\install.log'
$TranscriptStarted = $false
try {
    New-Item -ItemType Directory -Path (Split-Path -Parent $LogPath) -Force | Out-Null
    try {
        Start-Transcript -Path $LogPath -Append -Force | Out-Null
        $TranscriptStarted = $true
        Write-Host "Log de diagnóstico: $LogPath"
    } catch {
        Write-Warning "Não foi possível iniciar o log: $($_.Exception.Message)"
    }

    if ([string]::IsNullOrWhiteSpace($ManifestPath)) { $ManifestPath = Join-Path $KitRoot 'manifest.json' }
    if ($CheckOnly) {
        try { Test-ManifestOnly -Path $ManifestPath; exit 0 }
        catch { Write-Error $_; exit 1 }
    }

    Test-InstallEnvironment
    $mutex = New-Object System.Threading.Mutex($false, 'OnlyBangers.AOF7.2.5.3.Installer')
    $ownsMutex = $false
    try {
        $ownsMutex = $mutex.WaitOne(0)
        if (-not $ownsMutex) { throw 'Another AOF7 installer is already running' }
        $python = Install-EmbeddedPython -KitRoot $KitRoot -OutputRoot $OutputRoot
        $pythonScript = Join-Path $KitRoot 'aof7_installer.py'
        & $python $pythonScript --manifest $ManifestPath --kit-root $KitRoot --output-root $OutputRoot --workers 8
        if ($LASTEXITCODE -ne 0) { throw "AOF7 file installation failed with exit code $LASTEXITCODE" }
        $minecraftRoot = Join-Path $env:APPDATA '.minecraft'
        $java = Find-MinecraftJava -MinecraftRoot $minecraftRoot
        Install-FabricClient -MinecraftRoot $minecraftRoot -OutputRoot $OutputRoot -JavaPath $java
        $profilePath = Join-Path $minecraftRoot 'launcher_profiles.json'
        & $python $pythonScript --merge-profile --profile-path $profilePath --output-root $OutputRoot
        if ($LASTEXITCODE -ne 0) { throw "Launcher profile creation failed with exit code $LASTEXITCODE" }
        $launch = Write-LaunchCommand -OutputRoot $OutputRoot
        Write-Host "AOF7 2.5.3 instalado em $OutputRoot"
        Write-Host "Abra o perfil AOF7 2.5.3 no launcher oficial ou execute $launch"
    } finally {
        if ($ownsMutex) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
} catch {
    Write-Host "AOF7 installer error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ($_ | Out-String)
    exit 1
} finally {
    if ($TranscriptStarted) { Stop-Transcript | Out-Null }
}
