import random
import string
import pandas as pd

def generate_code():
    letters = random.choices(string.ascii_letters, k=2)
    digits = random.choices(string.digits, k=2)
    special = random.choice("!@#$%&*()-_=+?")
    others = random.choices(string.ascii_letters + string.digits, k=2)
    parts = letters + digits + [special] + others
    random.shuffle(parts)
    return ''.join(parts)

# Anzahl der Codes definieren
num_codes = 50

codes = [generate_code() for _ in range(num_codes)]
df = pd.DataFrame({'code': codes})
df.to_csv(r"C:\Users\D.Müller\Documents\UKE\AG-Saugel\Studienkonzeption\Endotypes_validation\zugelassene_ids.csv", index=False)

print(f"{num_codes} Zugangscodes erfolgreich in 'zugelassene_ids.csv' gespeichert.")
