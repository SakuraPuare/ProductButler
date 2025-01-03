if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
} elseif ((Get-Command python).Source -notmatch "\.venv") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
}

$uploadFolders = Get-ChildItem -Path "upload" -Directory | Where-Object { $_.Name -notmatch "__pycache__" } | Select-Object -ExpandProperty Name
$hiddenImports = $uploadFolders | ForEach-Object { "--hiddenimport upload.$_.gui" }

$pyinstallerCommand = "pyinstaller gui.py " + `
                      "--hiddenimport selenium.webdriver.chrome.service " + `
                      "--hiddenimport selenium.webdriver.chrome.options " + `
                      "--hiddenimport selenium.webdriver.firefox.service " + `
                      "--hiddenimport selenium.webdriver.firefox.options " + `
                      "--hiddenimport selenium.webdriver.edge.service " + `
                      "--hiddenimport selenium.webdriver.edge.options " + `
                      "--hiddenimport seleniumwire " + `
                      "--hiddenimport seleniumwire.webdriver " + `
                      "--hiddenimport webdriver_manager.chrome " + `
                      "--hiddenimport webdriver_manager.firefox " + `
                      "--hiddenimport webdriver_manager.microsoft " + `
                      "$($hiddenImports -join ' ') " + `
                      "--add-data '.venv\Lib\site-packages\seleniumwire\ca.crt;seleniumwire' " + `
                      "--add-data '.venv\Lib\site-packages\seleniumwire\ca.key;seleniumwire' " + `
                      "--noconfirm"

Write-Host "Executing command: $pyinstallerCommand" -ForegroundColor Cyan
Invoke-Expression $pyinstallerCommand

# Remove previous dated zip files but keep version-numbered releases
Get-ChildItem -Path "dist" -Filter "gui_*.zip" | Where-Object { $_.Name -match "gui_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}\.zip" } | ForEach-Object {
    Remove-Item $_.FullName
    Write-Host "Removed previous archive: $($_.Name)" -ForegroundColor Yellow
}


$timestamp = Get-Date -Format "yyyy_MM_dd_HH_mm_ss"
$zipPath = "dist/gui_$timestamp.zip"
Compress-Archive -Path "dist/gui" -DestinationPath $zipPath
Write-Host "Created archive: $zipPath" -ForegroundColor Green
