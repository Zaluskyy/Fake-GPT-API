from fake_gpt import ask_gpt

print("--- Start programu ---")
print("Zadaję pytanie w tle...")

# Pytanie testowe
pytanie_linux = "Czy papież wiedział o kremówkach?"

# Uruchamiamy - na Malinie headless=True musi być połączone z xvfb-run
odpowiedz = ask_gpt(pytanie_linux, headless=True)

print("\n" + "=" * 40)
print("ODPOWIEDŹ CHATGPT:")
print("=" * 40)
print(odpowiedz)
print("=" * 40)
