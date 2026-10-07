<#
  crea_collegamento.ps1 - crea (o aggiorna) sul desktop il collegamento
  "Libreria PowerLanguage.lnk" che avvia avvia.bat della libreria.

  Uso:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\windows\crea_collegamento.ps1 [-Repo <cartella>]

  -Repo  cartella radice della libreria (default: la cartella che contiene
         tools\windows\, cioe' due livelli sopra questo script).

  Il desktop viene individuato con [Environment]::GetFolderPath('Desktop'),
  che segue anche un desktop spostato su OneDrive. Solo caratteri ASCII.
#>
param(
    [string]$Repo = ''
)

$ErrorActionPreference = 'Stop'

try {
    if ([string]::IsNullOrWhiteSpace($Repo)) {
        $Repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    }
    $Repo = (Resolve-Path -LiteralPath $Repo).ProviderPath
    $Repo = $Repo.TrimEnd('\')
    if ($Repo.EndsWith(':')) { $Repo += '\' }

    $launcher = Join-Path $Repo 'avvia.bat'
    if (-not (Test-Path -LiteralPath $launcher)) {
        throw "non trovo avvia.bat nella cartella '$Repo': indica la radice della libreria con -Repo."
    }

    $desktop = [Environment]::GetFolderPath('Desktop')
    if ([string]::IsNullOrWhiteSpace($desktop)) {
        $desktop = [Environment]::GetFolderPath('DesktopDirectory')
    }
    if ([string]::IsNullOrWhiteSpace($desktop) -or -not (Test-Path -LiteralPath $desktop)) {
        throw "cartella Desktop non trovata."
    }
    $lnkPath = Join-Path $desktop 'Libreria PowerLanguage.lnk'

    $icon = Join-Path $Repo 'tools\windows\libreria.ico'
    if (Test-Path -LiteralPath $icon) {
        $iconLocation = "$icon,0"
    } else {
        $iconLocation = "$env:SystemRoot\System32\shell32.dll,43"
    }

    # Il collegamento punta a cmd.exe con /c ""<repo>\avvia.bat"": le doppie
    # virgolette esterne sono tolte da cmd, quelle interne proteggono gli spazi.
    $shell = New-Object -ComObject WScript.Shell
    $lnk = $shell.CreateShortcut($lnkPath)
    $lnk.TargetPath = $env:ComSpec
    $lnk.Arguments = "/c """"$launcher"""""
    $lnk.WorkingDirectory = $Repo
    $lnk.IconLocation = $iconLocation
    $lnk.Description = 'Libreria PowerLanguage per MultiCharts: catalogo, nuove voci, sincronizzazione con GitHub'
    $lnk.WindowStyle = 1
    $lnk.Save()

    Write-Host "Collegamento creato sul desktop: $lnkPath"
    Write-Host "Avvia: $launcher"
    exit 0
}
catch {
    Write-Host "ERRORE: impossibile creare il collegamento sul desktop: $($_.Exception.Message)"
    exit 1
}
