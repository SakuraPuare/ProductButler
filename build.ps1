if ((Get-Command python).Source -notmatch "\.venv") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
}

$uploadFolders = Get-ChildItem -Path "upload" -Directory | Where-Object { $_.Name -notmatch "__pycache__" } | Select-Object -ExpandProperty Name
$hiddenImports = $uploadFolders | ForEach-Object { "--hiddenimport upload.$_.gui" }

$pyinstallerCommand = "pyinstaller gui.py " + `
                      "--hiddenimport `"selenium.webdriver.chrome.service`" " + `
                      "--hiddenimport `"selenium.webdriver.chrome.options`" " + `
                      "--hiddenimport `"webdriver_manager.chrome`" " + `
                      "--hiddenimport `"selenium.webdriver.firefox.service`" " + `
                      "--hiddenimport `"selenium.webdriver.firefox.options`" " + `
                      "--hiddenimport `"webdriver_manager.firefox`" " + `
                      "--hiddenimport `"selenium.webdriver.edge.service`" " + `
                      "--hiddenimport `"selenium.webdriver.edge.options`" " + `
                      "--hiddenimport `"webdriver_manager.microsoft`" " + `
                      "--hiddenimport seleniumwire " + `
                      "--hiddenimport seleniumwire.webdriver " + `
                      "$($hiddenImports -join ' ') " + `
                      "--add-data '.venv\Lib\site-packages\seleniumwire\ca.crt;seleniumwire' " + `
                      "--add-data '.venv\Lib\site-packages\seleniumwire\ca.key;seleniumwire' " + `
                      "--noconfirm"

Write-Host "Executing command: $pyinstallerCommand" -ForegroundColor Cyan
Invoke-Expression $pyinstallerCommand

$timestamp = Get-Date -Format "yyyy_MM_dd_HH_mm_ss"
$zipPath = "dist/gui_$timestamp.zip"
Compress-Archive -Path "dist/gui" -DestinationPath $zipPath
Write-Host "Created archive: $zipPath" -ForegroundColor Green
