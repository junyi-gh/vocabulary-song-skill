param(
    [Parameter(Mandatory = $true)][string]$TextFile,
    [Parameter(Mandatory = $true)][string]$OutputFile,
    [ValidateRange(-10, 10)][int]$Rate = 0,
    [string]$VoiceName = ""
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech

$textPath = [System.IO.Path]::GetFullPath($TextFile)
$outputPath = [System.IO.Path]::GetFullPath($OutputFile)
$parent = [System.IO.Path]::GetDirectoryName($outputPath)
if ($parent) {
    [System.IO.Directory]::CreateDirectory($parent) | Out-Null
}

$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $voices = @($speaker.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo })
    if ($VoiceName) {
        $speaker.SelectVoice($VoiceName)
    }
    else {
        $english = $voices | Where-Object { $_.Culture.Name -like "en-*" } | Select-Object -First 1
        if ($english) {
            $speaker.SelectVoice($english.Name)
        }
    }
    $speaker.Rate = $Rate
    $speaker.SetOutputToWaveFile($outputPath)
    $speaker.Speak([System.IO.File]::ReadAllText($textPath, [System.Text.Encoding]::UTF8))
}
finally {
    $speaker.Dispose()
}
