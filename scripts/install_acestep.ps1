param(
    [string]$Version = "v0.1.8",
    [string]$InstallRoot = ""
)

$ErrorActionPreference = "Stop"
$skillRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $InstallRoot) {
    $InstallRoot = Join-Path $skillRoot ".runtime"
}
$runtimeRoot = [System.IO.Path]::GetFullPath($InstallRoot)
$target = Join-Path $runtimeRoot "ace-step-1.5"
$repository = "https://github.com/ace-step/ACE-Step-1.5.git"
$env:UV_CACHE_DIR = Join-Path $runtimeRoot ".uv-cache"
$env:HF_HOME = Join-Path $runtimeRoot "huggingface"
$env:HF_HUB_CACHE = Join-Path $env:HF_HOME "hub"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required. Install Git for Windows and run this installer again."
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id astral-sh.uv -e --accept-package-agreements --accept-source-agreements
    }
    else {
        throw "The uv package manager is required. Install it from https://docs.astral.sh/uv/"
    }
}

New-Item -ItemType Directory -Force $runtimeRoot | Out-Null
New-Item -ItemType Directory -Force $env:UV_CACHE_DIR,$env:HF_HOME | Out-Null
if (-not (Test-Path -LiteralPath $target)) {
    git clone --depth 1 --branch $Version $repository $target
}
else {
    $remote = git -C $target remote get-url origin
    if ($remote -ne $repository) {
        throw "Existing ACE-Step directory has an unexpected remote: $remote"
    }
    git -C $target fetch --depth 1 origin "refs/tags/$Version`:refs/tags/$Version"
    git -C $target checkout --detach $Version
}

uv sync --project $target
[System.IO.File]::WriteAllText((Join-Path $skillRoot ".runtime-location"), $target, [System.Text.Encoding]::UTF8)
Write-Output "ACE-Step $Version is installed at $target"
Write-Output "Model files will be downloaded by ACE-Step when the server first starts."
