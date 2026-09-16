param([string]$InputPath,[string]$OutputPath,[string]$PidPath)
$ErrorActionPreference='Stop'
$existingWordIds=@(Get-Process WINWORD -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$word=$null
$document=$null
try {
 $word=New-Object -ComObject Word.Application
 $word.Visible=$false
 $word.DisplayAlerts=0
 $word.AutomationSecurity=3
 $newWordProcesses=@(Get-Process WINWORD -ErrorAction SilentlyContinue | Where-Object { $_.Id -notin $existingWordIds })
 if ($newWordProcesses.Count -eq 1) { [System.IO.File]::WriteAllText($PidPath,[string]$newWordProcesses[0].Id) }
 $document=$word.Documents.Open($InputPath,$false,$true)
 $document.ExportAsFixedFormat($OutputPath,17)
} finally {
 if ($null -ne $document) { $document.Close(0) }
 if ($null -ne $word) { $word.Quit() }
}