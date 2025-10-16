# DMARC UPDATE VERIFICATIE SCRIPT
# Checkt of DMARC records correct zijn geüpdatet

Write-Host "`n🔍 DMARC RECORDS VERIFICATIE" -ForegroundColor Cyan
Write-Host "==============================`n" -ForegroundColor Cyan

$domains = @(
    "punthelder-marketing.nl",
    "punthelder-seo.nl",
    "punthelder-vindbaarheid.nl",
    "punthelder-zoekmachine.nl"
)

$expectedPolicy = "quarantine"
$expectedRua = "dmarc-reports@punthelder-marketing.nl"

foreach ($domain in $domains) {
    Write-Host "`n📧 Checking: $domain" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    try {
        $dmarc = Resolve-DnsName -Name "_dmarc.$domain" -Type TXT -ErrorAction Stop |
                 Select-Object -First 1
        
        if ($dmarc) {
            $record = $dmarc.Strings
            Write-Host "  ✅ DMARC record found" -ForegroundColor Green
            Write-Host "     $record" -ForegroundColor White
            
            # Check policy
            if ($record -match "p=quarantine") {
                Write-Host "  ✅ Policy: quarantine (CORRECT)" -ForegroundColor Green
            } elseif ($record -match "p=none") {
                Write-Host "  ⚠️  Policy: none (NOT YET UPDATED)" -ForegroundColor Yellow
            } else {
                Write-Host "  ❌ Policy: unknown" -ForegroundColor Red
            }
            
            # Check rua
            if ($record -match "rua=mailto:$expectedRua") {
                Write-Host "  ✅ Reports email: $expectedRua (CORRECT)" -ForegroundColor Green
            } else {
                Write-Host "  ℹ️  Reports email not configured" -ForegroundColor Gray
            }
            
            # Check strict alignment
            if ($record -match "adkim=s") {
                Write-Host "  ✅ DKIM alignment: strict" -ForegroundColor Green
            }
            if ($record -match "aspf=s") {
                Write-Host "  ✅ SPF alignment: strict" -ForegroundColor Green
            }
            
        } else {
            Write-Host "  ❌ NO DMARC RECORD FOUND" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "  ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n`n📊 SUMMARY:" -ForegroundColor Cyan
Write-Host "============" -ForegroundColor Cyan
Write-Host "If you see ⚠️  'p=none' → DNS update not propagated yet (wait 5-10 min)" -ForegroundColor Yellow
Write-Host "If you see ✅ 'p=quarantine' → Update successful!" -ForegroundColor Green
Write-Host ""
