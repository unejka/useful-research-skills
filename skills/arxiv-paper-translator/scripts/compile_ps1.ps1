param(
    [string]$WorkDir = ".",
    [string]$MainTex,
    [switch]$SkipPdfTextCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-Tool {
    param([Parameter(Mandatory = $true)][string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Find-MainTex {
    $candidates = @(Get-ChildItem -Recurse -File -Filter *.tex | Where-Object {
        Select-String -Path $_.FullName -Pattern '\\documentclass' -Quiet
    })
    if ($candidates.Count -eq 0) {
        throw "Could not find a main .tex file containing \documentclass."
    }
    if ($candidates.Count -gt 1) {
        Write-Host "Multiple main .tex candidates found. Using the first one:" -ForegroundColor Yellow
        $candidates | ForEach-Object { Write-Host "  $($_.FullName)" -ForegroundColor Yellow }
    }
    return $candidates[0].FullName
}

function Infer-Backend {
    $texFiles = Get-ChildItem -Recurse -File -Filter *.tex | Select-Object -ExpandProperty FullName
    foreach ($file in $texFiles) {
        if (Select-String -Path $file -Pattern 'backend\s*=\s*biber|\\addbibresource|\\printbibliography' -Quiet) {
            return "biber"
        }
    }
    foreach ($file in $texFiles) {
        if (Select-String -Path $file -Pattern '\\bibliography\{|\\bibliographystyle\{|natbib' -Quiet) {
            return "bibtex"
        }
    }
    return "auto"
}

function Throw-IfLogHasIssues {
    param(
        [string]$BaseName,
        [string]$LogPath
    )

    if (-not (Test-Path $LogPath)) {
        throw "Missing log file: $LogPath"
    }

    $log = Get-Content $LogPath -Raw
    $issues = New-Object System.Collections.Generic.List[string]

    if ($log -match '(?m)^! LaTeX Error:') {
        $issues.Add("fatal LaTeX error present in final log")
    }
    if ($log -match 'undefined citations|There were undefined citations|Citation `[^'']+'' on page .* undefined') {
        $issues.Add("undefined citations remain in final log")
    }
    if ($log -match 'LaTeX Warning: There were undefined references|Reference `[^'']+'' on page .* undefined') {
        $issues.Add("undefined references remain in final log")
    }
    if ($log -match 'LaTeX Warning: There were multiply-defined labels|Label `[^'']+'' multiply defined') {
        $issues.Add("multiply-defined labels remain in final log")
    }

    if ($issues.Count -gt 0) {
        $bblPath = "$BaseName.bbl"
        $bblExists = Test-Path $bblPath
        $bblRead = $log -match [regex]::Escape("(./$BaseName.bbl") -or $log -match [regex]::Escape("($BaseName.bbl")
        $structuralHint = $log -match 'File ended while scanning|ended by \\end\{document\}|Runaway argument|Missing \\begin\{document\}|Emergency stop'

        Write-Host "Compile diagnostics:" -ForegroundColor Red
        $issues | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }

        if ($bblExists -and $bblRead) {
            Write-Host "  - .bbl exists and was read in the log." -ForegroundColor Yellow
            Write-Host "    Unresolved citations may be caused by a later structural LaTeX error interrupting the final pass." -ForegroundColor Yellow
        }

        if ($structuralHint) {
            Write-Host "  - Structural-error patterns were detected. Check unmatched environments, braces, or truncated content." -ForegroundColor Yellow
        }
        if ($issues -contains "multiply-defined labels remain in final log") {
            Write-Host "  - Duplicate \\label keys were detected. Search all .tex files and keep one canonical label per object." -ForegroundColor Yellow
        }

        throw "Compilation finished with unresolved log issues. Inspect $LogPath."
    }
}

function Throw-IfPdfHasMarkers {
    param([string]$PdfPath)

    if ($SkipPdfTextCheck) {
        return
    }
    if (-not (Test-Tool -Name "pdftotext")) {
        Write-Host "pdftotext not found; skipping PDF text sanity check." -ForegroundColor Yellow
        return
    }
    if (-not (Test-Path $PdfPath)) {
        throw "Missing PDF file: $PdfPath"
    }

    $pdfText = & pdftotext $PdfPath - 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "pdftotext failed; skipping PDF text sanity check." -ForegroundColor Yellow
        return
    }

    if ($pdfText -match '\?\?|\(\?\)|\(\?\?\)|（\?）|（\?\?）') {
        throw "Potential unresolved markers found in PDF text. Inspect $PdfPath."
    }
}

if (-not (Test-Tool -Name "latexmk")) {
    throw "latexmk is required but was not found in PATH."
}

Push-Location $WorkDir
try {
    if (-not $MainTex) {
        $MainTex = Find-MainTex
    }

    $MainTexPath = Resolve-Path $MainTex
    $MainTexFile = Split-Path $MainTexPath -Leaf
    $BaseName = [System.IO.Path]::GetFileNameWithoutExtension($MainTexFile)

    $ResolvedBackend = Infer-Backend
    Write-Host "Main file: $MainTexFile"
    Write-Host "Bibliography backend: $ResolvedBackend"

    $latexmkArgs = @(
        "-xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        $MainTexFile
    )

    & latexmk @latexmkArgs
    if ($LASTEXITCODE -ne 0) {
        throw "latexmk failed. Resolve the first fatal LaTeX error before applying bibliography workarounds."
    }

    Throw-IfLogHasIssues -BaseName $BaseName -LogPath "$BaseName.log"
    Throw-IfPdfHasMarkers -PdfPath "$BaseName.pdf"

    Write-Host "Compilation succeeded with clean log/PDF checks." -ForegroundColor Green
}
finally {
    Pop-Location
}
