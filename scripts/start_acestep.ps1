param(
    [ValidateSet("auto", "cpu", "cuda", "xpu")][string]$Device = "auto",
    [ValidateSet("true", "false", "auto")][string]$InitLlm = "false",
    [int]$Port = 8001
)

$ErrorActionPreference = "Stop"
$skillRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$locationFile = Join-Path $skillRoot ".runtime-location"
if (Test-Path -LiteralPath $locationFile) {
    $target = [System.IO.File]::ReadAllText($locationFile, [System.Text.Encoding]::UTF8).Trim()
}
else {
    $target = Join-Path $skillRoot ".runtime\ace-step-1.5"
}
if (-not (Test-Path -LiteralPath $target)) {
    throw "ACE-Step is not installed. Run scripts/install_acestep.ps1 first."
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "The uv package manager is not available in PATH."
}

$runtimeRoot = Split-Path -Parent $target
$env:UV_CACHE_DIR = Join-Path $runtimeRoot ".uv-cache"
$env:HF_HOME = Join-Path $runtimeRoot "huggingface"
$env:HF_HUB_CACHE = Join-Path $env:HF_HOME "hub"
$env:ACESTEP_CHECKPOINTS_DIR = Join-Path $runtimeRoot "checkpoints"

$env:ACESTEP_API_HOST = "127.0.0.1"
$env:ACESTEP_API_PORT = "$Port"
$env:ACESTEP_DEVICE = $Device
$env:ACESTEP_INIT_LLM = $InitLlm
if ($Device -eq "cpu") {
    $env:ACESTEP_OFFLOAD_TO_CPU = "true"
    $env:ACESTEP_OFFLOAD_DIT_TO_CPU = "true"
}

Write-Output "Starting ACE-Step at http://127.0.0.1:$Port (device=$Device, LM=$InitLlm)"
uv run --project $target acestep-api
