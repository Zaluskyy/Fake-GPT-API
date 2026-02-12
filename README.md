#!/bin/bash

# ==========================================
# FakeGPT Installer dla Raspberry Pi (Headless)
# ==========================================

echo "🚀 Rozpoczynam instalację FakeGPT..."

# 1. Instalacja pakietów systemowych
echo "📦 [1/5] Aktualizacja i instalacja pakietów systemowych..."
sudo apt update
sudo apt install -y chromium-browser chromium-chromedriver xvfb python3-venv libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0

# 2. Tworzenie środowiska wirtualnego
echo "🐍 [2/5] Konfiguracja środowiska Python (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   Utworzono nowy folder venv."
else
    echo "   Folder venv już istnieje."
fi

# Aktywacja środowiska w kontekście skryptu
source venv/bin/activate

# 3. Instalacja bibliotek
echo "📥 [3/5] Instalacja SeleniumBase..."
pip3 install seleniumbase

# 4. Generowanie pliku biblioteki fake_gpt.py
echo "📝 [4/5] Tworzenie pliku fake_gpt.py (z fixem na Cloudflare)..."
cat << 'EOF' > fake_gpt.py
from seleniumbase import SB
import sys
import time
import random

def ask_gpt(prompt, headless=True):
    """
    Funkcja wchodzi na ChatGPT, wpisuje prompt i zwraca odpowiedź.
    Przystosowana do działania na Raspberry Pi z agresywnym obejściem Cloudflare.
    """
    
    url = "https://chatgpt.com/?ref=dotcom"
    textarea_sel = "#prompt-textarea"
    send_btn_sel = 'button[data-testid="send-button"]'
    stop_btn_sel = 'button[data-testid="stop-button"]'
    response_sel = 'div[data-message-author-role="assistant"]' 

    try:
        real_headless = headless
        if sys.platform == "linux":
            print("🐧 Wykryto Linux (RPi). Wymuszam tryb graficzny dla Xvfb (headless=False)...")
            real_headless = False

        with SB(uc=True, test=True, headless=real_headless, user_data_dir="gpt_profile") as sb:
            sb.set_window_size(1920, 1080)
            
            print(f"🌐 Otwieram stronę (metoda reconnect): {url} ...")
            sb.driver.uc_open_with_reconnect(url, reconnect_time=random.uniform(5, 7))
            
            print("🛡️ Rozpoczynam procedurę weryfikacji (pętla 120s)...")
            start_time = time.time()
            max_duration = 120
            click_attempts = 0
            
            while time.time() - start_time < max_duration:
                if sb.is_element_visible(textarea_sel):
                    print("✅ Pole tekstowe wykryte! Jesteśmy w środku.")
                    break
                
                page_title = sb.get_title()
                if any(x in page_title for x in ["Just a moment", "Cierpliwości", "Challenge", "Verify"]):
                    print(f"⚠️ Cloudflare (Próba {click_attempts+1})...")
                    try:
                        sb.driver.uc_gui_click_captcha()
                        print("🖱️ Kliknięto myszką. Czekam 10-15s na weryfikację...")
                        time.sleep(random.uniform(10, 15))
                        click_attempts += 1
                        if click_attempts % 3 == 0:
                            print("🔄 Zbyt wiele nieudanych prób. Odświeżam stronę...")
                            sb.refresh()
                            time.sleep(5)
                    except Exception as e:
                        print(f"⚠️ Błąd klikania (GUI): {e}. Próbuję fallback...")
                        try:
                             sb.driver.uc_click("input[type='checkbox']")
                        except:
                             pass
                        time.sleep(3)
                else:
                    print(f"⏳ Oczekiwanie... (Tytuł: {page_title})")
                    if "403" in page_title or "Access denied" in sb.get_page_source():
                        print("⛔ Błąd 403 (Ban IP/UserAgent). Czekam 30s...")
                        time.sleep(30)
                        sb.refresh()
                    time.sleep(2)

            print("📝 Sprawdzam ostatecznie dostępność pola tekstowego...")
            try:
                sb.wait_for_element(textarea_sel, timeout=30)
            except Exception:
                sb.save_screenshot("debug_error.png")
                page_title = sb.get_title()
                raise Exception(f"Nie znaleziono pola input. Tytuł strony: '{page_title}'. Sprawdź debug_error.png")

            print("📝 Wpisuję prompt...")
            sb.wait_for_element_clickable(textarea_sel, timeout=10)
            sb.click(textarea_sel)
            sb.type(textarea_sel, prompt)

            print("🚀 Wysyłam...")
            try:
                sb.wait_for_element_clickable(send_btn_sel, timeout=10)
                sb.click(send_btn_sel)
            except Exception:
                sb.save_screenshot("debug_button_error.png")
                raise Exception("Przycisk 'Wyślij' nie był klikalny. Sprawdź debug_button_error.png")

            print("🤖 Czekam na odpowiedź od bota...")
            try:
                sb.wait_for_element(stop_btn_sel, timeout=10) 
                sb.wait_for_element_not_visible(stop_btn_sel, timeout=180)
            except Exception:
                pass

            print("📥 Pobieram odpowiedź...")
            responses = sb.find_elements(response_sel)
            if responses:
                return responses[-1].text
            else:
                sb.save_screenshot("debug_no_response.png")
                return "❌ BŁĄD: Nie znaleziono dymka z odpowiedzią. Sprawdź debug_no_response.png"

    except Exception as e:
        return f"❌ BŁĄD KRYTYCZNY: {str(e)}"
EOF

# 5. Generowanie pliku testowego
echo "📝 [5/5] Tworzenie pliku programTest.py..."
cat << 'EOF' > programTest.py
from fake_gpt import ask_gpt
import sys

prompt = "Opowiedz krótki żart o programistach."
if len(sys.argv) > 1:
    prompt = " ".join(sys.argv[1:])

print(f"--- Pytanie: {prompt} ---")
odpowiedz = ask_gpt(prompt, headless=False)

print("\n" + "="*40)
print("ODPOWIEDŹ CHATGPT:")
print("="*40)
print(odpowiedz)
print("="*40)
EOF

echo ""
echo "✅ INSTALACJA ZAKOŃCZONA!"
echo "Aby uruchomić bota, wpisz poniższą komendę:"
echo ""
echo "source venv/bin/activate && xvfb-run --server-args=\"-screen 0 1920x1080x24\" python3 programTest.py"
echo ""

