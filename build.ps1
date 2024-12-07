if ((Get-Command python).Source -notmatch "\.venv") {
    Write-Host "Activating virtual environment..."
    .\.venv\Scripts\Activate.ps1
}

$uploadFolders = Get-ChildItem -Path "upload" -Directory | Where-Object { $_.Name -notmatch "__pycache__" } | Select-Object -ExpandProperty Name
$hiddenImports = $uploadFolders | ForEach-Object { "--hiddenimport upload.$_.gui" }

pyinstaller gui.py `
    --hiddenimport "selenium.webdriver.chrome.service" `
    --hiddenimport "selenium.webdriver.chrome.options" `
    --hiddenimport "webdriver_manager.chrome" `
    --hiddenimport "selenium.webdriver.firefox.service" `
    --hiddenimport "selenium.webdriver.firefox.options" `
    --hiddenimport "webdriver_manager.firefox" `
    --hiddenimport "selenium.webdriver.edge.service" `
    --hiddenimport "selenium.webdriver.edge.options" `
    --hiddenimport "webdriver_manager.microsoft" `
    --hiddenimport seleniumwire `
    --hiddenimport seleniumwire.webdriver `
    $($hiddenImports -join " `\n    ") `
    --add-data '.venv\Lib\site-packages\seleniumwire\ca.crt;seleniumwire' `
    --add-data '.venv\Lib\site-packages\seleniumwire\ca.key;seleniumwire' `
    --noconfirm