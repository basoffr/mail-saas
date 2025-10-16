# DNS RECORDS VERIFICATIE SCRIPT
# Checkt SPF, DKIM en DMARC records voor alle 4 domeinen

Write-Host "`n🔍 DNS RECORDS VERIFICATIE" -ForegroundColor Cyan
Write-Host "============================`n" -ForegroundColor Cyan

$domains = @(
    "punthelder-vindbaarheid.nl",
    "punthelder-marketing.nl",
    "punthelder-seo.nl",
    "punthelder-zoekmachine.nl"
)

$dkimSelector = "x"  # Vimexx gebruikt 'x' als DKIM selector

foreach ($domain in $domains) {
    Write-Host "`n📧 Domain: $domain" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    # SPF Check
    Write-Host "`n  🔐 SPF Record:" -ForegroundColor White
    try {
        $spf = Resolve-DnsName -Name $domain -Type TXT -ErrorAction Stop | 
               Where-Object { $_.Strings -match "v=spf1" } | 
               Select-Object -First 1
        
        if ($spf) {
            Write-Host "    ✅ FOUND: $($spf.Strings)" -ForegroundColor Green
            
            # Check if includes Vimexx
            if ($spf.Strings -match "vimexx") {
                Write-Host "    ✅ Includes Vimexx SMTP" -ForegroundColor Green
            } else {
                Write-Host "    ⚠️  WARNING: Does not include Vimexx" -ForegroundColor Yellow
            }
        } else {
            Write-Host "    ❌ NOT FOUND" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "    ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # DKIM Check
    Write-Host "`n  🔑 DKIM Record (${dkimSelector}._domainkey):" -ForegroundColor White
    try {
        $dkim = Resolve-DnsName -Name "${dkimSelector}._domainkey.$domain" -Type TXT -ErrorAction Stop |
                Select-Object -First 1
        
        if ($dkim) {
            Write-Host "    ✅ FOUND: $($dkim.Strings.Substring(0, [Math]::Min(80, $dkim.Strings.Length)))..." -ForegroundColor Green
        } else {
            Write-Host "    ❌ NOT FOUND" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "    ❌ NOT FOUND (may use different selector)" -ForegroundColor Red
    }
    
    # DMARC Check
    Write-Host "`n  📊 DMARC Record:" -ForegroundColor White
    try {
        $dmarc = Resolve-DnsName -Name "_dmarc.$domain" -Type TXT -ErrorAction Stop |
                 Select-Object -First 1
        
        if ($dmarc) {
            Write-Host "    ✅ FOUND: $($dmarc.Strings)" -ForegroundColor Green
            
            # Parse policy
            if ($dmarc.Strings -match "p=(\w+)") {
                $policy = $matches[1]
                Write-Host "    📋 Policy: $policy" -ForegroundColor Cyan
            }
        } else {
            Write-Host "    ❌ NOT FOUND" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "    ❌ NOT FOUND" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "`n✨ VERIFICATIE COMPLEET!" -ForegroundColor Green
Write-Host "`nℹ️  INTERPRETATIE:" -ForegroundColor Cyan
Write-Host "  ✅ = Record gevonden en correct" -ForegroundColor Green
Write-Host "  ⚠️  = Record gevonden maar mogelijk niet optimaal" -ForegroundColor Yellow
Write-Host "  ❌ = Record niet gevonden - MOET GECONFIGUREERD WORDEN!" -ForegroundColor Red
Write-Host ""
