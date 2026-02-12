from seleniumbase import SB
import sys
import time
import random

def ask_gpt(prompt, headless=True):
    """
    Funkcja wchodzi na ChatGPT, wpisuje prompt i zwraca odpowiedź.
    Przystosowana do działania na Raspberry Pi z agresywnym obejściem Cloudflare.
    """
    
    # Używamy adresu z robots.txt
    url = "https://chatgpt.com/?ref=dotcom"
    
    textarea_sel = "#prompt-textarea"
    send_btn_sel = 'button[data-testid="send-button"]'
    stop_btn_sel = 'button[data-testid="stop-button"]'
    response_sel = 'div[data-message-author-role="assistant"]' 

    try:
        # --- FIX DLA RASPBERRY PI ---
        # Jeśli jesteśmy na Linuxie, MUSIMY ustawić headless=False.
        # Dlaczego? Bo SeleniumBase blokuje klikanie myszką (PyAutoGUI) w trybie headless.
        # Ponieważ używasz xvfb-run, okno i tak będzie ukryte w wirtualnym ekranie,
        # więc dla Ciebie to nadal wygląda jak headless, ale dla bota jest to "normalny" tryb.
        
        real_headless = headless
        if sys.platform == "linux":
            print("🐧 Wykryto Linux (RPi). Wymuszam tryb graficzny dla Xvfb (headless=False)...")
            real_headless = False

        with SB(uc=True, test=True, headless=real_headless, user_data_dir="gpt_profile") as sb:
            sb.set_window_size(1920, 1080)
            
            print(f"🌐 Otwieram stronę (metoda reconnect): {url} ...")
            # ZMIANA: Używamy open_with_reconnect - to "resetuje" flagi bota
            sb.driver.uc_open_with_reconnect(url, reconnect_time=random.uniform(5, 7))
            
            # --- SEKCJA WALK Z CLOUDFLARE (PĘTLA) ---
            print("🛡️ Rozpoczynam procedurę weryfikacji (pętla 120s)...")
            
            start_time = time.time()
            max_duration = 120 # Dajemy więcej czasu na walkę
            click_attempts = 0
            
            while time.time() - start_time < max_duration:
                # 1. SPRAWDZENIE SUKCESU: Czy pole tekstowe już jest?
                if sb.is_element_visible(textarea_sel):
                    print("✅ Pole tekstowe wykryte! Jesteśmy w środku.")
                    break
                
                page_title = sb.get_title()
                
                # 2. SPRAWDZENIE BLOKADY
                if any(x in page_title for x in ["Just a moment", "Cierpliwości", "Challenge", "Verify"]):
                    print(f"⚠️ Cloudflare (Próba {click_attempts+1})...")
                    
                    try:
                        # Ruch myszką na środek (udawanie człowieka)
                        # To zadziała tylko jeśli headless=False (co wymusiliśmy wyżej na Linuxie)
                        sb.driver.uc_gui_click_captcha()
                        print("🖱️ Kliknięto myszką. Czekam 10-15s na weryfikację...")
                        
                        time.sleep(random.uniform(10, 15))
                        click_attempts += 1
                        
                        # Odświeżenie co 3 próby
                        if click_attempts % 3 == 0:
                            print("🔄 Zbyt wiele nieudanych prób. Odświeżam stronę...")
                            sb.refresh()
                            time.sleep(5)
                            
                    except Exception as e:
                        print(f"⚠️ Błąd klikania (GUI): {e}.")
                        # Fallback: Jeśli myszka zawiedzie, spróbujmy zwykłego kliknięcia JS (może zadziała)
                        try:
                             print("🔧 Próbuję kliknięcia alternatywnego (CDP)...")
                             # Szukamy iframe lub checkboxa
                             sb.driver.uc_click("input[type='checkbox']")
                        except:
                             pass
                        time.sleep(3)
                
                # 3. Jeśli nie ma Cloudflare ani pola tekstowego
                else:
                    print(f"⏳ Oczekiwanie... (Tytuł: {page_title})")
                    if "403" in page_title or "Access denied" in sb.get_page_source():
                        print("⛔ Błąd 403 (Ban IP/UserAgent). Czekam 30s...")
                        time.sleep(30)
                        sb.refresh()
                    time.sleep(2)
            
            # --- KONIEC PĘTLI ---

            print("📝 Sprawdzam ostatecznie dostępność pola tekstowego...")
            
            try:
                # Zwiększam czas oczekiwania na finałowe załadowanie
                sb.wait_for_element(textarea_sel, timeout=30)
            except Exception:
                print("⚠️ Nie udało się wejść. Robię zrzut...")
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
