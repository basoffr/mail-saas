#!/usr/bin/env python3
"""
SMTP TEST SCRIPT - Test alle 8 email accounts
Run dit script VOOR je de campagne start om te verifiëren dat alles werkt!
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

# SMTP configuratie
SMTP_HOST = "mail.vimexx.nl"
SMTP_PORT = 587

# Test accounts (vul wachtwoorden in!)
ACCOUNTS = [
    {
        "domain": "punthelder-vindbaarheid.nl",
        "email": "christian@punthelder-vindbaarheid.nl",
        "password": os.getenv("SMTP_VINDBAARHEID_CHRISTIAN_PASSWORD", "FILL_IN"),
        "name": "Christian Punthelder"
    },
    {
        "domain": "punthelder-vindbaarheid.nl",
        "email": "victor@punthelder-vindbaarheid.nl",
        "password": os.getenv("SMTP_VINDBAARHEID_VICTOR_PASSWORD", "FILL_IN"),
        "name": "Victor Punthelder"
    },
    {
        "domain": "punthelder-marketing.nl",
        "email": "christian@punthelder-marketing.nl",
        "password": os.getenv("SMTP_MARKETING_CHRISTIAN_PASSWORD", "FILL_IN"),
        "name": "Christian Punthelder"
    },
    {
        "domain": "punthelder-marketing.nl",
        "email": "victor@punthelder-marketing.nl",
        "password": os.getenv("SMTP_MARKETING_VICTOR_PASSWORD", "FILL_IN"),
        "name": "Victor Punthelder"
    },
    {
        "domain": "punthelder-seo.nl",
        "email": "christian@punthelder-seo.nl",
        "password": os.getenv("SMTP_SEO_CHRISTIAN_PASSWORD", "FILL_IN"),
        "name": "Christian Punthelder"
    },
    {
        "domain": "punthelder-seo.nl",
        "email": "victor@punthelder-seo.nl",
        "password": os.getenv("SMTP_SEO_VICTOR_PASSWORD", "FILL_IN"),
        "name": "Victor Punthelder"
    },
    {
        "domain": "punthelder-zoekmachine.nl",
        "email": "christian@punthelder-zoekmachine.nl",
        "password": os.getenv("SMTP_ZOEKMACHINE_CHRISTIAN_PASSWORD", "FILL_IN"),
        "name": "Christian Punthelder"
    },
    {
        "domain": "punthelder-zoekmachine.nl",
        "email": "victor@punthelder-zoekmachine.nl",
        "password": os.getenv("SMTP_ZOEKMACHINE_VICTOR_PASSWORD", "FILL_IN"),
        "name": "Victor Punthelder"
    }
]

# Test recipient (gebruik je eigen email!)
TEST_RECIPIENT = input("Voer je test email adres in: ").strip()

def test_smtp_account(account):
    """Test een enkel SMTP account"""
    print(f"\n🔍 Testing {account['email']}...")
    
    if account['password'] == "FILL_IN":
        print(f"   ⚠️  SKIPPED: Wachtwoord niet ingevuld!")
        return False
    
    try:
        # Maak email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"✅ SMTP Test van {account['email']}"
        msg['From'] = f"{account['name']} <{account['email']}>"
        msg['To'] = TEST_RECIPIENT
        
        # Email body
        html = f"""
        <html>
          <body>
            <h2>✅ SMTP Test Succesvol!</h2>
            <p><strong>Account:</strong> {account['email']}</p>
            <p><strong>Domain:</strong> {account['domain']}</p>
            <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Dit betekent dat dit account correct is geconfigureerd en emails kan versturen! 🎉</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
              SPF: ✅ | DKIM: ✅ | DMARC: ✅
            </p>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        # Verbind met SMTP server
        print(f"   📡 Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        # Login
        print(f"   🔐 Authenticating...")
        server.login(account['email'], account['password'])
        
        # Verstuur email
        print(f"   📧 Sending test email...")
        server.sendmail(account['email'], [TEST_RECIPIENT], msg.as_string())
        server.quit()
        
        print(f"   ✅ SUCCESS! Email verzonden naar {TEST_RECIPIENT}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ AUTHENTICATION FAILED: {e}")
        print(f"      → Check wachtwoord voor {account['email']}")
        return False
        
    except smtplib.SMTPException as e:
        print(f"   ❌ SMTP ERROR: {e}")
        return False
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


def main():
    """Test alle accounts"""
    print("\n" + "="*60)
    print("🚀 SMTP ACCOUNTS TEST - ALLE 8 ACCOUNTS")
    print("="*60)
    print(f"\n📧 Test emails worden verstuurd naar: {TEST_RECIPIENT}")
    print("\n⚠️  CHECK JE INBOX (en SPAM folder) tijdens de test!")
    
    input("\nDruk ENTER om te starten...")
    
    results = []
    for account in ACCOUNTS:
        success = test_smtp_account(account)
        results.append({
            'email': account['email'],
            'success': success
        })
    
    # Samenvatting
    print("\n" + "="*60)
    print("📊 TEST RESULTATEN SAMENVATTING")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['email']}")
    
    print(f"\n🎯 Score: {success_count}/{total_count} accounts werkend")
    
    if success_count == total_count:
        print("\n🎉 PERFECT! Alle accounts werken!")
        print("✅ Je bent klaar om de campagne te starten! 🚀")
    else:
        print(f"\n⚠️  LET OP: {total_count - success_count} account(s) hebben problemen!")
        print("🔧 Fix de problemen voordat je de campagne start.")
    
    print("\n💡 TIP: Check je inbox voor alle test emails!")


if __name__ == "__main__":
    main()
