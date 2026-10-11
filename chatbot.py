from ollama import chat
from pathlib import Path
import json

PLIK_historia = Path(__file__).parent / "historia.json"

PLIK_preferencje = Path(__file__).parent / "preferencje.json"

thinking = False

def wczytaj():
	if PLIK_historia.exists():
		return json.loads(PLIK_historia.read_text(encoding="utf-8"))
	return []

def zaladuj():
	if PLIK_preferencje.exists():
		dane = json.loads(PLIK_preferencje.read_text(encoding="utf-8"))

		if isinstance(dane, dict):
			return dane
		else:
			return {}

	return {}


def scal(stare, nowe):
	for klucz, wartosc in nowe.items():
		obecna = stare.get(klucz)
		if isinstance(wartosc, list):
			if not isinstance(obecna, list):
				obecna = [] if obecna in (None, "") else [obecna]
				stare[klucz] = obecna
			for el in wartosc:
				if el not in obecna:
					obecna.append(el)
		elif isinstance(wartosc, dict):
			if not isinstance(obecna, dict):
				obecna = {}
				stare[klucz] = obecna
			scal(obecna, wartosc)
		elif wartosc not in (None, "", []):
			stare[klucz] = wartosc
	return stare



def zapisz(pamiec):
	PLIK_historia.write_text(json.dumps(pamiec, ensure_ascii=False, indent=4), encoding="utf-8")

def nadpisz(preferencje):
	PLIK_preferencje.write_text(json.dumps(preferencje, ensure_ascii=False, indent=4), encoding="utf-8")

def myslenie(current): #current to parametr ktory prenosi zmienna jako obecną wartość
	print("on - włącz\noff - wyłącz")
	mode = input("Wybierz: ")
	if mode == "on":
		return True
	elif mode == "off":
		return False
	print("Nieprawidłowa opcja. Tryb myślenia pozostał bez zmian.")
	return current

print("Wpisz /help aby uzyskac pomoc")

pamiec = wczytaj()

preferencje = zaladuj()

while True:
	try:
		ask = input("Zadaj pytanie: ")
		if ask == "/exit":
			zapisz(pamiec)
			break
		elif ask == "/help":
			print(
				f"/clear - czysci czat\n"
				f"/save - zapisuje rozmowe\n"
				f"/exit - zamyka program\n"
				f"/thinking - wł. lub wył myślenie, "
				f"obecnie {'on' if thinking else 'off'}"
			)
			continue
		elif ask == "/clear":
			pamiec.clear()
			zapisz(pamiec)
			continue
		elif ask == "/save":
			zapisz(pamiec)
			print("Zapisano.")
			continue
		elif ask == "/thinking":
			thinking = myslenie(thinking)
			continue
	
		pamiec.append({"role": "user", "content": ask})
		
		wiadomosci = [
		{
			"role": "system",
			"content": (
				"Odpowiadaj po polsku. Preferencje użytkownika:. Nie dodawaj ich do odpowiedzi"
				"uzyj ich dla siebie przy szukaniu danych powiazanych z nimi\n"
				+ json.dumps(preferencje, ensure_ascii=False, indent=2)
			),
		},
	]

		
		response = chat(model="qwen3.5:4b", messages=wiadomosci + pamiec[-10:], think=thinking, stream=True)

		answer = ""
		
		for sylaba in response:
			fragment = sylaba["message"]["content"]
			print(fragment, end='', flush=True)
			answer += fragment
			
		print()
		
		tresc_charakter = [
		{"role": "system", "content": (
			"Wyciągasz trwałe fakty o użytkowniku z jego wiadomości. "
			"Zapisuj tylko to, co użytkownik mówi o sobie "
			"(hobby, zawód, nawyki, upodobania). "
			"NIE zapisuj próśb, poleceń, pytań, planów na jeden dzień "
			"ani komentarzy. Jeśli nie ma trwałego faktu, zwróć puste listy. "
			"Zwróć krótkie hasła, nie cytaty."
		)},
		{"role": "user", "content": "Opowiedz mi żart"},
		{"role": "assistant", "content": '{"zainteresowania": [], "cechy": [], "rutyny": []}'},
		{"role": "user", "content": "Lubię latać dronem FPV i codziennie rano biegam"},
		{"role": "assistant", "content": '{"zainteresowania": ["drony FPV"], "cechy": [], "rutyny": ["bieganie rano"]}'},
		{"role": "user", "content": "na podstawie tego wyciagnij te fakty" + ask},
	]


		SCHEMA_PREF = {
		"type": "object",
		"properties": {
			"zainteresowania": {"type": "array", "items": {"type": "string"}},
			"cechy": {"type": "array", "items": {"type": "string"}},
			"rutyny": {"type": "array", "items": {"type": "string"}},
		},
	}


		charakter = chat(model="qwen3.5:4b", messages=tresc_charakter, format=SCHEMA_PREF, options={"temperature": 0}, think=False,)


		nowe = json.loads(charakter["message"]["content"])
		scal(preferencje, nowe)

		nadpisz(preferencje)

		pamiec.append({"role": "assistant", "content": answer})

		zapisz(pamiec)
		
	except KeyboardInterrupt:
		pamiec.clear()
		zapisz(pamiec)
		print(" Wychodzneie z programu")
		break
	
		
