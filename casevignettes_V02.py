import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime
import os
import re
from streamlit_autorefresh import st_autorefresh

# Must be the first Streamlit call
st.set_page_config(page_title="Hypotension Endotyp Tool", layout="centered")

# Constants
REPEATED_IDS = [6, 11, 17, 20, 14]
TIME_LIMIT = 90  # seconds
ALLOWED_IDS_FILE = "zugelassene_ids.csv"

# Load allowed user IDs
if os.path.exists(ALLOWED_IDS_FILE):
    allowed_ids = pd.read_csv(ALLOWED_IDS_FILE)['code'].tolist()
else:
    allowed_ids = []

# User input for identification
user_id = st.text_input("Bitte gib deinen persönlichen Zugangscode ein (z.B. *A1b2!):")
if not user_id:
    st.warning("Bitte Zugangscode eingeben, um zu starten.")
    st.stop()

# Check format (e.g. at least one special character, two digits, two letters, length 5+)
pattern = r"^(?=.*[!@#$%^&*()_+\-=[\]{};':\"\\|,.<>/?])(?=(.*\d){2,})(?=(.*[A-Za-z]){2,}).{5,}$"
if not re.match(pattern, user_id):
    st.error("Ungültiges Format: Bitte verwende mindestens 5 Zeichen, mit Sonderzeichen, 2 Ziffern und 2 Buchstaben.")
    st.stop()

# Check if code is in allowed list
if user_id not in allowed_ids:
    st.error("Dieser Zugangscode ist nicht gültig oder nicht freigeschaltet.")
    st.stop()

# Check if user already participated
if os.path.exists("antworten_gesamt.csv"):
    existing = pd.read_csv("antworten_gesamt.csv")
    if user_id in existing.get("teilnehmer_id", []).values:
        st.error("Du hast bereits an dieser Umfrage teilgenommen.")
        st.stop()

# Session state init
def init_session():
    if 'vignettes' not in st.session_state:
        df = pd.read_csv('vignetten.csv')  # Your source CSV

        # Mark original rows
        df['duplicate'] = False

        # Step 1: shuffle the base vignettes; # random_state=42
        originals = df.sample(frac=1).reset_index(drop=True)

        # Step 2: prepare repeated rows
        repeats = df[df['ID'].isin(REPEATED_IDS)].copy()
        repeats['duplicate'] = True
        repeat_rows = repeats.to_dict('records')
        full_list = originals.to_dict('records')

        # Step 3: insert each repeated row at a safe, random non-adjacent position
        inserted = 0
        max_attempts = 100
        while inserted < len(repeat_rows) and max_attempts > 0:
            max_attempts -= 1
            idx = random.randint(1, len(full_list) - 1)
            prev_id = full_list[idx - 1]['ID']
            next_id = full_list[idx]['ID']
            repeat_id = repeat_rows[inserted]['ID']

            if repeat_id != prev_id and repeat_id != next_id:
                full_list.insert(idx, repeat_rows[inserted])
                inserted += 1

        if inserted < len(repeat_rows):
            st.error("Konnte nicht alle Wiederholungen einfügen. Bitte prüfen Sie die Wiederholungs-Logik.")

        st.session_state.vignettes = pd.DataFrame(full_list).reset_index(drop=True)
        st.session_state.current_index = 0
        st.session_state.responses = []
        st.session_state.start_time = time.time()

# Display vignette and get input
def show_vignette(row):
    st_autorefresh(interval=5000, limit=TIME_LIMIT, key=f"autorefresh_{st.session_state.current_index}")
    total = len(st.session_state.vignettes)
    current = st.session_state.current_index + 1

    st.write(f"### Fall {current} von {total}")
    st.progress(current / total)

    st.write("**Vitalparameter:**")
    st.write(f"- Stroke Volume (SV): {row['SV']}")
    st.write(f"- Heart Rate (HR): {row['HR']}")
    st.write(f"- Systemic Vascular Resistance (SVR): {row['SVR']}")
    st.write(f"- Pulse Pressure Variation (PPV): {row['PPV']}")

    options = st.session_state.vignettes['Endotyp'].unique().tolist()
    answer = st.radio("Welcher hämodynamische Endotyp trifft zu?", options, key=f"answer_{st.session_state.current_index}")

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = TIME_LIMIT - elapsed
    auto_submitted = False

    if remaining <= 0:
        st.warning("Zeit abgelaufen. Ihre Antwort wurde automatisch gespeichert. Sie können das Fenster jetzt schließen. Vielen Dank für Ihre Teilnahme.")
        submit = True
        auto_submitted = True
    else:
        st.write(f"Verbleibende Zeit: {remaining} Sekunden")
        submit = st.button("Antwort speichern und weiter")

    if submit:
        st.session_state.responses.append({
            'timestamp': datetime.now().isoformat(),
            'teilnehmer_id': user_id,
            'fall_nummer': current,
            'frage_position': st.session_state.current_index,
            'original_id': row['ID'],
            'duplicate': row['duplicate'],
            'SV': row['SV'],
            'HR': row['HR'],
            'SVR': row['SVR'],
            'PPV': row['PPV'],
            'richtiger_endotyp': row['Endotyp'],
            'antwort': answer,
            'dauer_sekunden': elapsed,
            'auto_submitted': auto_submitted
        })
        st.session_state.current_index += 1
        st.session_state.start_time = time.time()
        st.rerun()

# Export responses
def save_results():
    df = pd.DataFrame(st.session_state.responses)
    st.success("Vielen Dank! Deine Antworten wurden gespeichert.")

    # Save to server file (append if exists)
    df.to_csv("antworten_gesamt.csv", mode='a', header=not os.path.exists("antworten_gesamt.csv"), index=False)

    # User download
    st.download_button("Antworten als CSV herunterladen", df.to_csv(index=False), file_name="antworten.csv")

# Main App
st.title("Hypotension Fallvignetten")

init_session()

if st.session_state.current_index < len(st.session_state.vignettes):
    current_row = st.session_state.vignettes.iloc[st.session_state.current_index]
    show_vignette(current_row)
else:
    save_results()
