# ROOT DIRECTORY CLEANUP SCRIPT
# Verplaatst alle non-essential bestanden naar _archive/
# SAFE: Doet alleen Move, geen Delete!

Write-Host "`n🧹 ROOT DIRECTORY CLEANUP SCRIPT" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

$rootPath = $PSScriptRoot
$archivePath = Join-Path $rootPath "_archive"

# Counters
$moved = 0
$skipped = 0

# Function to move files safely
function Move-ToArchive {
    param(
        [string]$Pattern,
        [string]$Destination,
        [string]$Description
    )
    
    Write-Host "`n📁 Moving $Description..." -ForegroundColor Yellow
    
    $files = Get-ChildItem -Path $rootPath -Filter $Pattern -File -ErrorAction SilentlyContinue
    
    if ($files) {
        foreach ($file in $files) {
            try {
                $destPath = Join-Path $Destination $file.Name
                Move-Item -Path $file.FullName -Destination $destPath -Force
                Write-Host "  ✅ Moved: $($file.Name)" -ForegroundColor Green
                $script:moved++
            }
            catch {
                Write-Host "  ❌ Failed: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
                $script:skipped++
            }
        }
    }
    else {
        Write-Host "  ℹ️  No files found matching: $Pattern" -ForegroundColor Gray
    }
}

# 1. Move all .md files to docs/
Move-ToArchive "*.md" (Join-Path $archivePath "docs") "Markdown Documentation"

# 2. Move all .txt files to logs/
Move-ToArchive "*.txt" (Join-Path $archivePath "logs") "Log Files"

# 3. Move all .png files to images/
Move-ToArchive "*.png" (Join-Path $archivePath "images") "Image Files"

# 4. Move all .sql files to migrations/
Move-ToArchive "*.sql" (Join-Path $archivePath "migrations") "SQL Migrations"

# 5. Move all .py files (root only) to import-scripts/
Move-ToArchive "*.py" (Join-Path $archivePath "import-scripts") "Python Scripts"

# 6. Move data files to data/
Move-ToArchive "*.xlsx" (Join-Path $archivePath "data") "Excel Files"
Move-ToArchive "*.json" (Join-Path $archivePath "data") "JSON Files"
Move-ToArchive "*.csv" (Join-Path $archivePath "data") "CSV Files"
Move-ToArchive "*.html" (Join-Path $archivePath "data") "HTML Files"

# 7. Move old directories
Write-Host "`n📁 Moving old directories..." -ForegroundColor Yellow

$oldDirs = @(
    "Implementatieplannen en prompts",
    "Importable data",
    "Summarys"
)

foreach ($dir in $oldDirs) {
    $dirPath = Join-Path $rootPath $dir
    if (Test-Path $dirPath) {
        try {
            $destPath = Join-Path (Join-Path $archivePath "old-folders") $dir
            Move-Item -Path $dirPath -Destination $destPath -Force
            Write-Host "  ✅ Moved: $dir" -ForegroundColor Green
            $script:moved++
        }
        catch {
            Write-Host "  ❌ Failed: $dir - $($_.Exception.Message)" -ForegroundColor Red
            $script:skipped++
        }
    }
}

# Summary
Write-Host "`n📊 CLEANUP SUMMARY" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host "✅ Files/folders moved: $moved" -ForegroundColor Green
Write-Host "❌ Items skipped: $skipped" -ForegroundColor Red

Write-Host "`n✨ Root directory is now clean!" -ForegroundColor Green
Write-Host "   All items archived to: _archive/`n" -ForegroundColor Gray

# Show what's left in root
Write-Host "📋 Remaining items in root:" -ForegroundColor Cyan
Get-ChildItem -Path $rootPath -Exclude "_archive" | Select-Object Name, @{Name='Type';Expression={if($_.PSIsContainer){'Directory'}else{'File'}}} | Format-Table -AutoSize
