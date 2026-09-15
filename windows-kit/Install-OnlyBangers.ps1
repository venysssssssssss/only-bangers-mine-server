[CmdletBinding()]
param(
    [string]$Target = "",
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$MinecraftVersion = "1.20.1"
$FabricLoaderVersion = "0.19.5"
$ServerAddress = "schmidt-flowers.tun.ply.gg:60986"
$KitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $KitRoot "onlybangers-client-manifest.json"
$SourceMods = Join-Path $KitRoot "client-mods"

function Get-Sha512([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA512).Hash.ToLowerInvariant()
}

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Manifesto ausente: $ManifestPath"
}
if (-not (Test-Path -LiteralPath $SourceMods -PathType Container)) {
    throw "Pasta client-mods ausente: $SourceMods"
}

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
if ($Manifest.minecraft -ne $MinecraftVersion) {
    throw "Minecraft incompatível: $($Manifest.minecraft). Esperado: $MinecraftVersion"
}
if ($Manifest.fabric_loader -ne $FabricLoaderVersion) {
    throw "Fabric Loader incompatível: $($Manifest.fabric_loader). Esperado: $FabricLoaderVersion"
}

$Mods = @($Manifest.mods)
if ($Mods.Count -lt 40) {
    throw "Manifesto incompleto: $($Mods.Count) mods"
}

$Forbidden = @(Get-ChildItem -LiteralPath $SourceMods -Filter "*.jar" -File |
    Where-Object { $_.Name -match "(?i)jei|easyauth" })
if ($Forbidden.Count -gt 0) {
    throw "Mods proibidos no kit: $($Forbidden.Name -join ', ')"
}

foreach ($Mod in $Mods) {
    $Source = Join-Path $SourceMods $Mod.file
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Jar ausente: $($Mod.file)"
    }
    $Actual = Get-Sha512 $Source
    if ($Actual -ne $Mod.sha512.ToLowerInvariant()) {
        throw "SHA-512 inválido: $($Mod.file)"
    }
}

$Java = Get-Command java -ErrorAction SilentlyContinue
if ($null -eq $Java) {
    throw "Java 21 não encontrado. Instale Temurin 21 x64 e selecione-o no TLauncher."
}
$JavaVersion = (& $Java.Source -version 2>&1 | Select-Object -First 1)
if ($JavaVersion -notmatch '"21(?:\.|")') {
    throw "Java 21 obrigatório. Encontrado: $JavaVersion"
}

if ([string]::IsNullOrWhiteSpace($Target)) {
    $Target = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "OnlyBangers-1.20.1"
}
$Target = [IO.Path]::GetFullPath($Target)
$TargetMods = Join-Path $Target "mods"

if (-not $CheckOnly) {
    New-Item -ItemType Directory -Path $TargetMods -Force | Out-Null

    $OldJars = @(Get-ChildItem -LiteralPath $TargetMods -Filter "*.jar" -File -ErrorAction SilentlyContinue)
    if ($OldJars.Count -gt 0) {
        $Backup = "$TargetMods.backup-$((Get-Date).ToString('yyyyMMdd-HHmmss'))"
        New-Item -ItemType Directory -Path $Backup -Force | Out-Null
        $OldJars | Move-Item -Destination $Backup
        Write-Host "Mods antigos movidos para: $Backup"
    }

    foreach ($Mod in $Mods) {
        Copy-Item -LiteralPath (Join-Path $SourceMods $Mod.file) -Destination $TargetMods -Force
    }
}

Write-Host "OK: $($Mods.Count) mods verificados"
Write-Host "Minecraft: $MinecraftVersion | Fabric Loader: $FabricLoaderVersion"
Write-Host "Servidor: $ServerAddress"
if ($CheckOnly) {
    Write-Host "Check-only: nenhum arquivo copiado"
} else {
    Write-Host "Pasta do jogo: $Target"
    Write-Host "JEI ausente; use EMI"
}
