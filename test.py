import csv
import os

# Dane do zapisania
dane = [
    {
        'drawing_number': '600.100.009',
        'name': 'Poprzeczka',
        'height_before_bending': 1287.0,
        'width_before_bending': 150.1,
        'model': 11,
        'pattern': 11,
        'drawing': 12,
        'nums_of_corr': 1,
        'material': 'DX51D',
        'thickness': 1.5,
        'bending_radius': 1.5,
        'mass': 2.2,
        'additional_note': 'Niewymiarowana geometria wg dokumentacji DXF. Detal symetryczny.',
        'number_of_bends': 2
    }
]

# Nazwa pliku
nazwa_pliku = "dane.csv"

# Sprawdzenie, czy plik istnieje
plik_istnieje = os.path.isfile(nazwa_pliku)

# Zestaw do przechowywania unikalnych kombinacji "drawing_number", "pattern", "drawing"
unikalne_dane = set()

# Odczyt istniejących danych, jeśli plik istnieje
if plik_istnieje:
    with open(nazwa_pliku, mode='r', newline='') as plik:
        reader = csv.DictReader(plik)
        for wiersz in reader:
            unikalne_dane.add((wiersz['drawing_number'], int(wiersz['pattern']), int(wiersz['drawing'])))

# Otwarcie pliku w trybie dopisywania, jeśli istnieje, lub zapisu, jeśli nie istnieje
with open(nazwa_pliku, mode='a' if plik_istnieje else 'w', newline='') as plik:
    fieldnames = ['drawing_number', 'name', 'height_before_bending', 'width_before_bending', 'model', 
                  'pattern', 'drawing', 'nums_of_corr', 'material', 'thickness', 
                  'bending_radius', 'mass', 'additional_note', 'number_of_bends']
    writer = csv.DictWriter(plik, fieldnames=fieldnames)
    
    # Jeśli plik nie istnieje, zapisz nagłówki
    if not plik_istnieje:
        writer.writeheader()
    
    # Zapis danych do pliku CSV z kontrolą duplikatów
    for wiersz in dane:
        klucz = (wiersz['drawing_number'], wiersz['pattern'], wiersz['drawing'])
        if klucz in unikalne_dane:
            print(f"Duplikat znaleziony: {wiersz}")
        else:
            writer.writerow(wiersz)
            unikalne_dane.add(klucz)

print(f"Dane zostały zapisane do pliku {nazwa_pliku}")