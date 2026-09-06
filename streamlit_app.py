from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import date, datetime, time, timedelta

import streamlit as st


st.set_page_config(page_title="CarePlan | Schichtplanung", page_icon="+", layout="wide")

EMPLOYEES = [
    ("MA001", "Jürgen Braun", "Pflegefachkraft", "Vollzeit", 38.5, True),
    ("MA002", "Claudia Wolf", "Auszubildender", "Vollzeit (Ausbildung)", 38.5, False),
    ("MA003", "Sven Koch", "Pflegefachkraft", "Teilzeit 75%", 28.88, True),
    ("MA004", "Birgit Carse", "Pflegehilfskraft", "Vollzeit", 38.5, False),
    ("MA005", "Thomas Hartmann", "Pflegefachkraft", "Vollzeit", 38.5, True),
    ("MA006", "Sophie Wagner", "Pflegehilfskraft", "Vollzeit", 38.5, False),
    ("MA007", "Cristina Meyer", "Stationsleitung", "Vollzeit", 38.5, False),
    ("MA008", "Nina Richter", "Pflegefachkraft", "Vollzeit", 38.5, True),
    ("MA009", "Matthias Bauer", "Pflegefachkraft", "Teilzeit 50%", 19.25, True),
    ("MA010", "Christian Schröder", "Pflegefachkraft", "Teilzeit 80%", 30.8, True),
    ("MA011", "Christian Hoffmann", "Auszubildender", "Vollzeit (Ausbildung)", 38.5, False),
    ("MA012", "Matthias Werner", "Pflegehilfskraft", "Teilzeit 80%", 30.8, True),
    ("MA013", "Kevin Huber", "Pflegefachkraft", "Teilzeit 50%", 19.25, True),
    ("MA014", "Kevin Hoffmann", "Pflegehilfskraft", "Teilzeit 50%", 19.25, False),
    ("MA015", "Martina Neumann", "Auszubildender", "Vollzeit (Ausbildung)", 38.5, False),
    ("MA016", "Melanie Meier", "Pflegehilfskraft", "Teilzeit 60%", 23.1, False),
    ("MA017", "Tobias Schmidt", "Pflegefachkraft", "Teilzeit 50%", 19.25, True),
    ("MA018", "Sarah Klein", "Auszubildender", "Vollzeit (Ausbildung)", 38.5, False),
    ("MA019", "David Zimmermann", "Pflegefachkraft", "Vollzeit", 38.5, True),
    ("MA020", "Katharina Schneider", "Pflegefachkraft", "Teilzeit 50%", 19.25, True),
    ("MA021", "Stefan Schwarz", "Pflegefachkraft", "Teilzeit 60%", 23.1, True),
    ("MA022", "Christina Lehmann", "Pflegehilfskraft", "Teilzeit 60%", 23.1, False),
    ("MA023", "Kevin Weber", "Pflegehilfskraft", "Teilzeit 50%", 19.25, False),
    ("MA024", "Claudia Schmitt", "Pflegefachkraft", "Vollzeit", 38.5, True),
    ("MA025", "Sophie Becker", "Auszubildender", "Vollzeit (Ausbildung)", 38.5, False),
    ("MA026", "Jasmin Schulz", "Pflegefachkraft", "Vollzeit", 38.5, True),
    ("MA027", "Thomas Lange", "Pflegefachkraft", "Vollzeit", 38.5, True),
    ("MA028", "Katharina Müller", "Pflegefachkraft", "Vollzeit", 38.5, True),
    ("MA029", "Lukas Fischer", "Auszubildender", "Vollzeit (Ausbildung)", 38.5, False),
    ("MA030", "Christina Krüger", "Pflegehilfskraft", "Teilzeit 50%", 19.25, True),
    ("MA031", "Peter Braun", "Pflegehilfskraft", "Vollzeit", 38.5, True),
    ("MA032", "Andreas Wolf", "Pflegefachkraft", "Vollzeit", 38.5, False),
    ("MA033", "Lena Koch", "Pflegefachkraft", "Teilzeit 80%", 30.8, True),
    ("MA034", "Katharina Krause", "Stationsleitung", "Teilzeit 50%", 19.25, True),
    ("MA035", "Jasmin Hartmann", "Pflegefachkraft", "Teilzeit 80%", 30.8, False),
    ("MA036", "Christina Wagner", "Pflegehilfskraft", "Teilzeit 60%", 23.1, True),
    ("MA037", "Anna Meyer", "Pflegefachkraft", "Vollzeit", 38.5, True),
    ("MA038", "Jasmin Richter", "Pflegefachkraft", "Teilzeit 75%", 28.88, True),
    ("MA039", "Julia Bauer", "Pflegefachkraft", "Teilzeit 80%", 30.8, True),
    ("MA040", "Nadine Schröder", "Stationsleitung", "Teilzeit 80%", 30.8, False),
]
STAFF = [dict(zip(("id", "name", "qualification", "employment", "hours", "night"), row)) for row in EMPLOYEES]
SHIFTS = {
    "Frühdienst": (time(6), time(14, 12), 7.7),
    "Spätdienst": (time(13, 30), time(21, 42), 7.7),
    "Nachtdienst": (time(21), time(6, 15), 8.25),
}


def shift_window(day: date, shift: str) -> tuple[datetime, datetime]:
    start, end, _ = SHIFTS[shift]
    start_dt = datetime.combine(day, start)
    end_day = day + timedelta(days=1) if end <= start else day
    return start_dt, datetime.combine(end_day, end)


CSV_COLUMNS = ("Mitarbeiter_ID", "Qualifikation", "Arbeitszeitmodell", "Nachtschicht_moeglich")
CSV_ALIASES = {
    "id": "Mitarbeiter_ID",
    "qualification": "Qualifikation",
    "employment": "Arbeitszeitmodell",
    "night": "Nachtschicht_moeglich",
}
QUALIFICATIONS = {"Schichtleitung", "Azubi", "Pflegefachkraft", "Pflegehilfskraft"}
OPTIONAL_COLUMNS = {"Wochenstunden", "Vertragsstunden_Woche", "Alter", "Minderjaehrig", "Ausbildungsjahr", "Praxisanleiter", "Urlaub_von", "Urlaub_bis", "Wunschfrei", "Team"}


def parse_staff_csv(raw_data: bytes) -> list[dict]:
    text = raw_data.decode("utf-8-sig")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    columns = tuple(reader.fieldnames or ())
    canonical_columns = tuple(CSV_ALIASES.get(column, column) for column in columns)
    missing = [column for column in CSV_COLUMNS if column not in canonical_columns]
    extra = [column for column in canonical_columns if column not in CSV_COLUMNS and column not in OPTIONAL_COLUMNS]
    if missing:
        raise ValueError(f"Fehlende Spalten: {', '.join(missing)}")
    if extra:
        raise ValueError(f"Unbekannte Spalten: {', '.join(extra)}")

    values = []
    seen_ids = set()
    for line_number, row in enumerate(reader, start=2):
        normalized_row = {CSV_ALIASES.get(column, column): value for column, value in row.items()}
        employee_id = (normalized_row.get("Mitarbeiter_ID") or "").strip()
        if not employee_id or employee_id in seen_ids:
            raise ValueError(f"Zeile {line_number}: ID fehlt oder ist doppelt vorhanden.")
        if not re.fullmatch(r"ma-\d{3}", employee_id):
            raise ValueError(f"Zeile {line_number}: ID muss dem Format ma-001 entsprechen.")
        qualification = (normalized_row.get("Qualifikation") or "").strip()
        if qualification not in QUALIFICATIONS:
            raise ValueError(f"Zeile {line_number}: qualification muss eine dieser Angaben enthalten: {', '.join(sorted(QUALIFICATIONS))}.")
        employment = (normalized_row.get("Arbeitszeitmodell") or "").strip()
        if employment not in {"Teilzeit", "Vollzeit"}:
            raise ValueError(f"Zeile {line_number}: employment muss Teilzeit oder Vollzeit sein.")
        night_value = (normalized_row.get("Nachtschicht_moeglich") or "").strip().lower()
        if night_value not in {"wahr", "falsch", "true", "false", "1", "0"}:
            raise ValueError(f"Zeile {line_number}: Nachtschicht_moeglich muss wahr/falsch, TRUE/FALSE oder 1/0 sein.")
        person = {
            "id": employee_id,
            "qualification": qualification,
            "employment": employment,
            "night": night_value in {"wahr", "true", "1"},
        }
        person["name"] = employee_id
        person["hours"] = 38.5 if employment == "Vollzeit" else 23.1
        person["department"] = "Gesamtbereich"
        person["optional"] = {column: normalized_row.get(column, "").strip() for column in OPTIONAL_COLUMNS if normalized_row.get(column)}
        values.append(person)
        seen_ids.add(employee_id)
    if not values:
        raise ValueError("Die CSV-Datei enthält keine Mitarbeitenden.")
    if not any(person["qualification"] == "Schichtleitung" for person in values):
        raise ValueError("Die CSV benötigt mindestens eine Person mit der Qualifikation Schichtleitung.")
    if sum(person["night"] for person in values) < 2:
        raise ValueError("Die CSV benötigt mindestens zwei nachtdienstfähige Mitarbeitende.")
    return values


def csv_template() -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerow({"Mitarbeiter_ID": "ma-001", "Qualifikation": "Pflegefachkraft", "Arbeitszeitmodell": "Vollzeit", "Nachtschicht_moeglich": "WAHR"})
    return output.getvalue()


def absent_ids(scenario: str, staff: list[dict]) -> set[str]:
    count = 2 if scenario == "Zwei kurzfristige Ausfälle" else (5 if scenario == "Ausfallwelle" else 0)
    return {person["id"] for person in staff[:count]}


def is_within_absence_lock(employee_id: str, start_dt: datetime, manual_absences: set[tuple[str, str, str]]) -> bool:
    for absent_employee_id, absent_date, absent_shift in manual_absences:
        if absent_employee_id != employee_id:
            continue
        absent_start, _ = shift_window(date.fromisoformat(absent_date), absent_shift)
        if absent_start <= start_dt < absent_start + timedelta(hours=24):
            return True
    return False


def is_ill(employee_id: str, day: date, illnesses: list[dict]) -> bool:
    for illness in illnesses:
        if illness["employee_id"] != employee_id:
            continue
        start = date.fromisoformat(illness["start"])
        end = start + timedelta(days=illness["days"] + 1)
        if start <= day < end:
            return True
    return False


def validate_plan(assignments: list[dict], staff: list[dict], start_day: date, required: dict[str, int]) -> list[str]:
    """Prüft harte Regeln am fertigen Plan und meldet nicht abbildbare Regeln transparent."""
    warnings = []
    staff_by_id = {person["id"]: person for person in staff}
    rows_by_employee: dict[str, list[dict]] = {person["id"]: [] for person in staff}
    for row in assignments:
        rows_by_employee[row["employee_id"]].append(row)

    for employee_id, rows in rows_by_employee.items():
        rows.sort(key=lambda row: shift_window(date.fromisoformat(row["date"]), row["shift"])[0])
        person = staff_by_id[employee_id]
        worked_hours = sum(SHIFTS[row["shift"]][2] for row in rows)
        maximum = min(48 * 4, person["hours"] * 4 * 1.10)
        if worked_hours > maximum + 0.01:
            warnings.append(f"H-02/H-21: {employee_id} überschreitet die zulässige Arbeitszeit im Planungszeitraum.")
        for previous, current in zip(rows, rows[1:]):
            previous_end = shift_window(date.fromisoformat(previous["date"]), previous["shift"])[1]
            current_start = shift_window(date.fromisoformat(current["date"]), current["shift"])[0]
            if current_start - previous_end < timedelta(hours=11):
                warnings.append(f"H-03: {employee_id} hat weniger als 11 Stunden Ruhezeit zwischen Diensten.")
        work_dates = {date.fromisoformat(row["date"]) for row in rows}
        for offset in range(22):
            window = {start_day + timedelta(days=offset + index) for index in range(8)}
            if len(work_dates & window) > 7:
                warnings.append(f"H-19: {employee_id} überschreitet sieben Arbeitstage in Folge.")
                break

    for offset in range(28):
        day = start_day + timedelta(days=offset)
        for shift, needed in required.items():
            rows = [row for row in assignments if row["date"] == day.isoformat() and row["shift"] == shift]
            qualified = [row for row in rows if row["qualification"] in {"Pflegefachkraft", "Schichtleitung"}]
            azubis = [row for row in rows if row["qualification"] == "Azubi"]
            if len([row for row in rows if row["qualification"] != "Azubi"]) < needed:
                warnings.append(f"H-09: {day:%d.%m.} {shift} erreicht die Mindestbesetzung ohne Azubis nicht.")
            if not any(row["qualification"] == "Schichtleitung" for row in rows):
                warnings.append(f"H-10: {day:%d.%m.} {shift} hat keine Schichtleitung.")
            if not qualified:
                warnings.append(f"H-13: {day:%d.%m.} {shift} hat keine examinierte Pflegefachkraft.")
            if len(azubis) * 2 > len(qualified):
                warnings.append(f"H-14: {day:%d.%m.} {shift} überschreitet den zulässigen Azubi-Anteil.")
            if shift == "Nachtdienst" and any(not staff_by_id[row["employee_id"]]["night"] for row in rows):
                warnings.append(f"H-15: {day:%d.%m.} enthält eine nicht nachtdienstfähige Person.")
            if shift == "Nachtdienst":
                warnings.append(f"H-05: {day:%d.%m.} Nachtdienst umfasst 8,25 Nettoarbeitsstunden; ein gesetzlicher Ausgleich muss dokumentiert werden.")
    warnings.append("Nicht im 28-Tage-Fenster prüfbar: Jahreskontingent von 15 freien Sonntagen und Feiertagsausgleich.")
    warnings.append("Nicht aus der CSV ableitbar: PpUGV-Quote nach Stationsart, Bettenzahl, Springerpool und Ersatzruhetage.")
    return list(dict.fromkeys(warnings))


def build_plan(start_day: date, scenario: str, required: dict[str, int], staff: list[dict], manual_absences: set[tuple[str, str, str]] | None = None, illnesses: list[dict] | None = None) -> tuple[list[dict], list[str]]:
    absent = absent_ids(scenario, staff)
    manual_absences = manual_absences or set()
    illnesses = illnesses or []
    assignments: list[dict] = []
    last_end: dict[str, datetime] = {}
    worked: dict[str, float] = {person["id"]: 0 for person in staff}
    night_worked: dict[str, int] = {person["id"]: 0 for person in staff}
    worked_days: dict[str, set[date]] = {person["id"]: set() for person in staff}
    warnings: list[str] = []

    for offset in range(28):
        day = start_day + timedelta(days=offset)
        for shift in SHIFTS:
            start_dt, end_dt = shift_window(day, shift)
            needed = required[shift]
            for slot in range(needed):
                candidates = []
                assigned_this_shift = [row for row in assignments if row["date"] == day.isoformat() and row["shift"] == shift]
                needs_shift_lead = not any(row["qualification"] == "Schichtleitung" for row in assigned_this_shift)
                needs_nurse = not any(row["qualification"] in {"Pflegefachkraft", "Schichtleitung"} for row in assigned_this_shift)
                for person in staff:
                    unavailable = person["id"] in absent or is_within_absence_lock(person["id"], start_dt, manual_absences) or is_ill(person["id"], day, illnesses)
                    already_assigned = person["id"] in {row["employee_id"] for row in assignments if row["date"] == day.isoformat() and row["shift"] == shift}
                    if unavailable or already_assigned:
                        continue
                    if shift == "Nachtdienst" and not person["night"]:
                        continue
                    if needs_shift_lead and person["qualification"] != "Schichtleitung":
                        continue
                    if not needs_shift_lead and needs_nurse and person["qualification"] not in {"Pflegefachkraft", "Schichtleitung"}:
                        continue
                    rest_ok = person["id"] not in last_end or start_dt - last_end[person["id"]] >= timedelta(hours=11)
                    if not rest_ok:
                        continue
                    if worked[person["id"]] + SHIFTS[shift][2] > min(48 * 4, person["hours"] * 4 * 1.10):
                        continue
                    if all(day - timedelta(days=step) in worked_days[person["id"]] for step in range(1, 8)):
                        continue
                    if shift == "Nachtdienst" and all(day - timedelta(days=step) in worked_days[person["id"]] and any(row["employee_id"] == person["id"] and row["date"] == (day - timedelta(days=step)).isoformat() and row["shift"] == "Nachtdienst" for row in assignments) for step in range(1, 6)):
                        continue
                    assigned_qualified = sum(row["qualification"] in {"Pflegefachkraft", "Schichtleitung"} for row in assigned_this_shift)
                    assigned_azubis = sum(row["qualification"] == "Azubi" for row in assigned_this_shift)
                    if person["qualification"] == "Azubi" and assigned_azubis * 2 >= assigned_qualified:
                        continue
                    qualification_score = 0 if person["qualification"] in {"Pflegefachkraft", "Schichtleitung"} else 1
                    night_score = night_worked[person["id"]] if shift == "Nachtdienst" else 0
                    candidates.append((qualification_score, night_score, worked[person["id"]], person["hours"], person))
                if not candidates:
                    warnings.append(f"{day:%d.%m.}: {shift} Slot {slot + 1} konnte nicht regelkonform besetzt werden.")
                    continue
                _, _, _, _, person = sorted(candidates, key=lambda candidate: candidate[:4])[0]
                assignments.append({"date": day.isoformat(), "day": day.strftime("%a %d.%m."), "shift": shift, "employee_id": person["id"], "name": person["name"], "qualification": person["qualification"], "department": person["department"], "slot": slot + 1})
                worked[person["id"]] += SHIFTS[shift][2]
                worked_days[person["id"]].add(day)
                if shift == "Nachtdienst":
                    night_worked[person["id"]] += 1
                last_end[person["id"]] = end_dt

    warnings.extend(validate_plan(assignments, staff, start_day, required))
    if absent:
        warnings.insert(0, f"Szenario aktiv: {len(absent)} Mitarbeitende sind kurzfristig abwesend. Es wurden keine Gesundheitsdaten verarbeitet.")
    if manual_absences:
        warnings.insert(0, f"Manuelle Anpassung: {len(manual_absences)} schichtbezogene Ausfalltage wurden berücksichtigt.")
    if illnesses:
        warnings.insert(0, f"Krankheitsfälle berücksichtigt: {len(illnesses)} Meldung(en). Der Plan wurde für 28 Tage neu berechnet.")
    return assignments, warnings

def as_csv(rows: list[dict]) -> str:
    output = io.StringIO()
    fields = ["date", "day", "shift", "slot", "employee_id", "name", "qualification", "department"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --ink:#16202a; --muted:#60707c; --teal:#087f7b; --mint:#dff4ed; --coral:#e76f51; --line:#dce5e5; }
html, body, [class*="css"] { font-family:'DM Sans', sans-serif; color:var(--ink); }
h1, h2, h3 { font-family:'Space Grotesk', sans-serif; letter-spacing:0; }
.hero { padding:1.5rem 0 .8rem; border-bottom:1px solid var(--line); margin-bottom:1.2rem; }
.eyebrow { color:var(--teal); text-transform:uppercase; font-size:.72rem; font-weight:700; letter-spacing:.12em; }
.hero h1 { font-size:2.25rem; margin:.25rem 0 .3rem; }
.hero p { color:var(--muted); margin:0; font-size:1rem; }
.metric { background:#f3f8f6; border-left:4px solid var(--teal); padding:.8rem 1rem; min-height:90px; }
.metric strong { display:block; font-family:'Space Grotesk'; font-size:1.75rem; }
.metric span { color:var(--muted); font-size:.8rem; }
.notice { background:#fff5ed; border-left:4px solid var(--coral); padding:.7rem .9rem; margin:.35rem 0; color:#713b2b; }
</style>""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="eyebrow">CarePlan / Prototyp 01</div><h1>Schichtplanung, die mitdenkt.</h1><p>Regelkonforme Planung für Früh-, Spät- und Nachtdienste mit schneller Ausfallanpassung.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Aktuelle Stammdaten")
    uploaded_file = st.file_uploader("Mitarbeitenden-CSV hochladen", type="csv", help="Die Datei muss die im Tab Regeln & Annahmen beschriebenen Spalten enthalten.")
    st.download_button("CSV-Vorlage herunterladen", csv_template(), "mitarbeitende_vorlage.csv", "text/csv", use_container_width=True)
    if uploaded_file is None:
        st.info("Bitte zuerst die aktuelle CSV-Datei hochladen.")
        st.stop()
    try:
        uploaded_staff = parse_staff_csv(uploaded_file.getvalue())
    except (UnicodeDecodeError, ValueError) as error:
        st.error(f"CSV konnte nicht verarbeitet werden: {error}")
        st.stop()
    selected_department = "Gesamtbereich"
    staff = uploaded_staff
    st.caption(f"{len(uploaded_staff)} Mitarbeitende geladen.")

    st.markdown("### Plan konfigurieren")
    start_day = st.date_input("Planwoche ab", date.today() - timedelta(days=date.today().weekday()))
    scenario = st.selectbox("Ausfallszenario", ["Keine Ausfälle", "Zwei kurzfristige Ausfälle", "Ausfallwelle"], help="Nur anonymisierte Ausfall-Slots, keine Diagnosen oder Gesundheitsdaten.")
    st.markdown("**Mindestbesetzung je Schicht**")
    required = {shift: st.number_input(shift, min_value=1, max_value=6, value={"Frühdienst": 5, "Spätdienst": 4, "Nachtdienst": 2}[shift], key=shift) for shift in SHIFTS}
    generate = st.button("Plan neu berechnen", type="primary", use_container_width=True)

config_fingerprint = f"{start_day.isoformat()}|{scenario}|{required}"
dataset_key = hashlib.sha256(uploaded_file.getvalue() + config_fingerprint.encode()).hexdigest()
if st.session_state.get("dataset_key") != dataset_key:
    st.session_state.manual_absences = set()
    st.session_state.illnesses = []
    st.session_state.pop("plan", None)
    st.session_state.pop("baseline_plan", None)
    st.session_state.dataset_key = dataset_key
if "manual_absences" not in st.session_state:
    st.session_state.manual_absences = set()
if "illnesses" not in st.session_state:
    st.session_state.illnesses = []
if "baseline_plan" not in st.session_state:
    st.session_state.baseline_plan, _ = build_plan(start_day, scenario, required, staff)
if generate or st.session_state.get("rebuild", False) or "plan" not in st.session_state:
    st.session_state.plan, st.session_state.warnings = build_plan(start_day, scenario, required, staff, st.session_state.manual_absences, st.session_state.illnesses)
    st.session_state.plan_meta = (start_day, scenario, selected_department)
    st.session_state.rebuild = False

plan = st.session_state.plan
warnings = st.session_state.warnings
absent = absent_ids(scenario, staff)
filled = len(plan)
expected = sum(required.values()) * 28
coverage = round(filled / expected * 100) if expected else 0
qualified_nights = sum(row["shift"] == "Nachtdienst" and row["qualification"] in {"Pflegefachkraft", "Schichtleitung"} for row in plan)

baseline_by_slot = {(row["date"], row["shift"], row["slot"]): row for row in st.session_state.baseline_plan}
current_by_slot = {(row["date"], row["shift"], row["slot"]): row for row in plan}
display_plan = []
for row in plan:
    slot_key = (row["date"], row["shift"], row["slot"])
    baseline_row = baseline_by_slot.get(slot_key)
    status = "Unverändert" if baseline_row and baseline_row["employee_id"] == row["employee_id"] else ("Ersatzbesetzung" if baseline_row else "Neu")
    display_plan.append({**row, "status": status})
changes = [row for row in display_plan if row["status"] != "Unverändert"]

with st.sidebar.expander("Spontane Krankmeldung", expanded=True):
    st.caption("Die Person wird für die erwartete Ausfallzeit aus allen Schichten genommen. Danach wird der 28-Tage-Plan neu berechnet.")
    illness_id = st.selectbox("Mitarbeiter-ID", [person["id"] for person in staff], key="illness_id")
    illness_start = st.date_input("Krank ab", start_day, min_value=start_day, max_value=start_day + timedelta(days=27), key="illness_start")
    illness_days = st.number_input("Voraussichtliche Ausfallzeit (Tage)", min_value=1, max_value=28, value=1, step=1, key="illness_days")
    if st.button("Krankmeldung anwenden", use_container_width=True):
        new_illness = {"employee_id": illness_id, "start": illness_start.isoformat(), "days": int(illness_days)}
        st.session_state.illnesses = [item for item in st.session_state.illnesses if item["employee_id"] != illness_id]
        st.session_state.illnesses.append(new_illness)
        st.session_state.rebuild = True
        st.rerun()
    if st.session_state.illnesses:
        st.caption("Aktive Krankmeldungen")
        for illness in st.session_state.illnesses:
            st.write(f"{illness['employee_id']}: ab {illness['start']} für {illness['days']} Tag(e)")
        if st.button("Krankmeldungen zurücksetzen", use_container_width=True):
            st.session_state.illnesses = []
            st.session_state.rebuild = True
            st.rerun()

metric_cols = st.columns(4)
for column, value, label in zip(metric_cols, [f"{coverage}%", filled, len(staff) - len(absent), len(warnings)], ["Besetzungsgrad", "Dienste geplant", "Verfügbar", "Prüfhinweise"]):
    column.markdown(f'<div class="metric"><strong>{value}</strong><span>{label}</span></div>', unsafe_allow_html=True)

st.write("")
if warnings:
    with st.expander(f"Prüfhinweise ({len(warnings)})", expanded=True):
        for warning in warnings:
            st.markdown(f'<div class="notice">{warning}</div>', unsafe_allow_html=True)
else:
    st.success("Alle angeforderten Dienste konnten unter den hinterlegten Regeln besetzt werden.")

tab_plan, tab_staff, tab_rules = st.tabs(["Wochenplan", "Mitarbeitende", "Regeln & Annahmen"])
with tab_plan:
    left, right = st.columns([4, 1])
    with left:
        view = st.selectbox("Ansicht", ["Alle Schichten", "Nur Nachtdienste", "Nur offene Slots"], label_visibility="collapsed")
    with right:
        st.download_button("CSV exportieren", as_csv(plan), "schichtplan.csv", "text/csv", use_container_width=True)
    shown = display_plan if view == "Alle Schichten" else ([row for row in display_plan if row["shift"] == "Nachtdienst"] if view == "Nur Nachtdienste" else [])
    if view == "Nur offene Slots":
        st.info("Offene Slots werden in den Prüfhinweisen ausgewiesen.")
    else:
        st.dataframe(shown, column_config={"date": None, "employee_id": "ID", "day": "Tag", "shift": "Dienst", "slot": "Slot", "name": "Name", "qualification": "Qualifikation", "department": "Abteilung", "status": "Status"}, hide_index=True, use_container_width=True)
    st.caption(f"Nachtdienste mit Pflegefachkraft/Schichtleitung: {qualified_nights} von {required['Nachtdienst'] * 28} angeforderten Slots.")
    if changes:
        st.markdown(f"**Änderungen gegenüber dem ursprünglichen Plan: {len(changes)}**")
        st.dataframe(changes, column_config={"date": "Datum", "day": "Tag", "shift": "Dienst", "slot": "Slot", "employee_id": "Neue ID", "name": "Neue Besetzung", "qualification": "Qualifikation", "status": "Status"}, hide_index=True, use_container_width=True)

with tab_staff:
    available = [person for person in staff if person["id"] not in absent]
    st.dataframe(available, column_config={"id": "ID", "name": "Mitarbeiter-ID", "qualification": "Qualifikation", "employment": "Arbeitszeitmodell", "hours": st.column_config.NumberColumn("Planstunden", format="%.0f"), "night": "Nachtdienst geeignet"}, hide_index=True, use_container_width=True)
    if absent:
        st.caption("Abwesend in diesem Szenario: " + ", ".join(sorted(absent)))

with tab_rules:
    st.markdown("""#### Verbindliche Prüfregeln
- **Ruhezeit:** Zwischen zwei Diensten liegen mindestens 11 Stunden.
- **Qualifikation:** Nachtwachen werden nur Pflegefachkräften oder Schichtleitungen zugewiesen.
- **Arbeitszeit:** Jeder Dienst umfasst 8 Stunden; die Wochenstunden aus den Stammdaten dienen als Kapazitätspriorität.
- **Mindestbesetzung:** Früh-, Spät- und Nachtdienst werden pro Tag separat geprüft.
- **Ausfälle:** Szenarien sind anonymisierte Verfügbarkeitsänderungen. Es werden keine individuellen Gesundheitsdaten gespeichert oder verarbeitet.

#### CSV-Stammdaten
Die hochgeladene UTF-8-Datei benötigt exakt die Spalten `id`, `qualification`, `employment` und `night`. Die ID muss dem Muster `ma-001` entsprechen. Erlaubte Qualifikationen sind `Schichtleitung`, `Azubi`, `Pflegefachkraft` und `Pflegehilfskraft`; beim Arbeitszeitmodell sind `Teilzeit` und `Vollzeit` erlaubt. Für `night` werden nur `wahr` und `falsch` akzeptiert. Komma, Semikolon und Tabulator werden als Trennzeichen erkannt.

Die Empfehlung verteilt zuerst qualifizierte Personen und priorisiert danach die geringste bisher geplante Arbeitszeit. Das ist eine transparente Heuristik für den Prototyp und ersetzt keine arbeitsrechtliche oder pflegefachliche Freigabe.""")
