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
$hiddenImports = $uploadFolders | ForEach-Object { "--nofollow-import-to=upload.$_.gui" }

$nuitkaCommand = "python -m nuitka gui.py " + `
                 "--standalone " + `
                 "--enable-plugin=pyside6 " + `
                 "--nofollow-import-to=selenium.webdriver.chrome.service " + `
                 "--nofollow-import-to=selenium.webdriver.chrome.options " + `
                 "--nofollow-import-to=selenium.webdriver.firefox.service " + `
                 "--nofollow-import-to=selenium.webdriver.firefox.options " + `
                 "--nofollow-import-to=selenium.webdriver.edge.service " + `
                 "--nofollow-import-to=selenium.webdriver.edge.options " + `
                 "--nofollow-import-to=seleniumwire " + `
                 "--nofollow-import-to=seleniumwire.webdriver " + `
                 "--nofollow-import-to=webdriver_manager.chrome " + `
                 "--nofollow-import-to=webdriver_manager.firefox " + `
                 "--nofollow-import-to=webdriver_manager.microsoft " + `
                 "$($hiddenImports -join ' ') " + `
                 "--include-data-dir=.venv/Lib/site-packages/seleniumwire=seleniumwire "

Write-Host "Executing command: $nuitkaCommand" -ForegroundColor Cyan
Invoke-Expression $nuitkaCommand