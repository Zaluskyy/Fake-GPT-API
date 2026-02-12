FakeGPT na Raspberry Pi (Headless / SSH)

Kompletna instrukcja uruchomienia skryptu fake_gpt.py na Raspberry Pi (lub innym Linuxie bez interfejsu graficznego) z obejściem zabezpieczeń Cloudflare.

1. Wymagania systemowe (APT)

Zanim zaczniesz, musisz zainstalować przeglądarkę, sterowniki oraz wirtualny ekran (xvfb), który pozwoli oszukać biblioteki graficzne i umożliwi działanie myszki w trybie tekstowym.

Uruchom w terminalu:

sudo apt update
sudo apt install -y chromium-browser chromium-chromedriver xvfb python3-venv libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0


chromium-browser & chromium-chromedriver: Przeglądarka i sterownik (na architekturze ARM muszą pochodzić z repozytorium systemowego).

xvfb: X Virtual Framebuffer (udaje monitor w pamięci RAM, co jest kluczowe przy połączeniu przez SSH).

libatk, libgtk: Biblioteki pomocnicze wymagane do poprawnego renderowania okna przeglądarki.

2. Przygotowanie środowiska Python

Zaleca się używanie wirtualnego środowiska (venv), aby uniknąć konfliktów z pakietami systemowymi.

Utwórz środowisko (w folderze projektu):

python3 -m venv venv


Aktywuj środowisko:

source venv/bin/activate


(Po aktywacji zobaczysz przedrostek (venv) w terminalu).

Zainstaluj bibliotekę SeleniumBase:

pip3 install seleniumbase


3. Konfiguracja Skryptu (fake_gpt.py)

Aby ominąć Cloudflare, skrypt musi udawać, że działa w trybie okienkowym (nawet jeśli używamy Xvfb). W funkcji ask_gpt musi znaleźć się mechanizm wykrywający system operacyjny:

# Kluczowy fragment logiki w fake_gpt.py:
real_headless = headless
if sys.platform == "linux":
    # Wymuszamy tryb graficzny dla bota, aby SeleniumBase pozwoliło na użycie myszki (GUI click).
    # Dzięki xvfb-run okno i tak pozostanie niewidoczne.
    real_headless = False

with SB(uc=True, test=True, headless=real_headless, user_data_dir="gpt_profile") as sb:
    # ... reszta logiki ...


4. Uruchamianie (Kluczowy krok)

Na Raspberry Pi przez SSH zawsze używaj xvfb-run. Nie uruchamiaj skryptu bezpośrednio przez python3, ponieważ mechanizm klikania w CAPTCHA się wywali.

Komenda startowa:

xvfb-run --server-args="-screen 0 1920x1080x24" python3 programTest.py


Dlaczego to jest ważne?

Wirtualny ekran: xvfb-run tworzy środowisko graficzne w pamięci RAM.

Rozdzielczość: Flaga -screen 0 1920x1080x24 wymusza rozmiar Full HD. Bez tego ChatGPT może załadować wersję mobilną strony, co zmieni układ przycisków i uniemożliwi botowi znalezienie pola tekstowego.

5. Praca z Gitem (.gitignore)

Jeśli planujesz wrzucić projekt do sieci, stwórz plik .gitignore, aby nie udostępnić swojej sesji (ciasteczek) innym:

venv/
__pycache__/
gpt_profile/
*.png
*.log
.DS_Store


6. Rozwiązywanie problemów

Błąd "PyAutoGUI can't be used in headless mode": Oznacza, że zapomniałeś ustawić headless=False w kodzie dla Linuxa. Pamiętaj: Xvfb ukrywa okno za Ciebie, więc SeleniumBase musi myśleć, że ma monitor.

Pętla Cloudflare: Jeśli bot ciągle klika i strona się odświeża, sprawdź plik debug_error.png. Zazwyczaj pomaga nieusuwanie folderu gpt_profile, dzięki czemu bot "pamięta" poprzednie udane weryfikacje.
