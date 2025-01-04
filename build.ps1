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
$hiddenImports = $uploadFolders | ForEach-Object { "--include-module=upload.$_.gui" }

$nuitkaCommand = "python -m nuitka gui.py " + `
                 "--onefile " + `
                 "--enable-plugin=pyside6 " + `
                 "--follow-imports --include-plugin-directory=upload " + `
                 "--include-module=selenium.webdriver.chrome.service " + `
                 "--include-module=selenium.webdriver.chrome.options " + `
                 "--include-module=selenium.webdriver.firefox.service " + `
                 "--include-module=selenium.webdriver.firefox.options " + `
                 "--include-module=selenium.webdriver.edge.service " + `
                 "--include-module=selenium.webdriver.edge.options " + `
                 "--include-module=seleniumwire " + `
                 "--include-module=seleniumwire.webdriver " + `
                 "--include-module=webdriver_manager.chrome " + `
                 "--include-module=webdriver_manager.firefox " + `
                 "--include-module=webdriver_manager.microsoft " + `
                 "$($hiddenImports -join ' ') " + `
                 "--include-data-dir=.venv/Lib/site-packages/seleniumwire=seleniumwire " + `
 		 "--output-dir=.\dist\"

Write-Host "Executing command: $nuitkaCommand" -ForegroundColor Cyan
Invoke-Expression $nuitkaCommand
