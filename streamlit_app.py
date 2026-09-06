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
    "Frühdienst": (time(6), time(14), 8),
    "Spätdienst": (time(14), time(22), 8),
    "Nachtdienst": (time(22), time(6), 8),
}


def shift_window(day: date, shift: str) -> tuple[datetime, datetime]:
    start, end, _ = SHIFTS[shift]
    start_dt = datetime.combine(day, start)
    end_day = day + timedelta(days=1) if end <= start else day
    return start_dt, datetime.combine(end_day, end)


CSV_COLUMNS = ("id", "qualification", "employment", "night")
QUALIFICATIONS = {"Schichtleitung", "Azubi", "Pflegefachkraft", "Pflegehilfskraft"}


def parse_staff_csv(raw_data: bytes) -> list[dict]:
    text = raw_data.decode("utf-8-sig")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    columns = tuple(reader.fieldnames or ())
    if columns != CSV_COLUMNS:
        raise ValueError(f"Die Kopfzeile muss exakt lauten: {','.join(CSV_COLUMNS)}")
    missing = [column for column in CSV_COLUMNS if column not in columns]
    extra = [column for column in columns if column not in CSV_COLUMNS]
    if missing:
        raise ValueError(f"Fehlende Spalten: {', '.join(missing)}")
    if extra:
        raise ValueError(f"Unbekannte Spalten: {', '.join(extra)}")

    values = []
    seen_ids = set()
    for line_number, row in enumerate(reader, start=2):
        employee_id = (row.get("id") or "").strip()
        if not employee_id or employee_id in seen_ids:
            raise ValueError(f"Zeile {line_number}: ID fehlt oder ist doppelt vorhanden.")
        if not re.fullmatch(r"ma-\d{3}", employee_id):
            raise ValueError(f"Zeile {line_number}: ID muss dem Format ma-001 entsprechen.")
        qualification = (row.get("qualification") or "").strip()
        if qualification not in QUALIFICATIONS:
            raise ValueError(f"Zeile {line_number}: qualification muss eine dieser Angaben enthalten: {', '.join(sorted(QUALIFICATIONS))}.")
        employment = (row.get("employment") or "").strip()
        if employment not in {"Teilzeit", "Vollzeit"}:
            raise ValueError(f"Zeile {line_number}: employment muss Teilzeit oder Vollzeit sein.")
        night_value = (row.get("night") or "").strip().lower()
        if night_value not in {"wahr", "falsch"}:
            raise ValueError(f"Zeile {line_number}: night muss wahr oder falsch sein.")
        person = {column: (row.get(column) or "").strip() for column in CSV_COLUMNS}
        if any(not person[column] for column in CSV_COLUMNS):
            raise ValueError(f"Zeile {line_number}: Pflichtfelder dürfen nicht leer sein.")
        person["id"] = employee_id
        person["name"] = employee_id
        person["hours"] = 40 if employment == "Vollzeit" else 20
        person["night"] = night_value == "wahr"
        person["department"] = "Gesamtbereich"
        values.append(person)
        seen_ids.add(employee_id)
    if not values:
        raise ValueError("Die CSV-Datei enthält keine Mitarbeitenden.")
    return values


def csv_template() -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerow({"id": "ma-001", "qualification": "Pflegefachkraft", "employment": "Vollzeit", "night": "wahr"})
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


def build_plan(start_day: date, scenario: str, required: dict[str, int], staff: list[dict], manual_absences: set[tuple[str, str, str]] | None = None) -> tuple[list[dict], list[str]]:
    absent = absent_ids(scenario, staff)
    manual_absences = manual_absences or set()
    assignments: list[dict] = []
    last_end: dict[str, datetime] = {}
    worked: dict[str, float] = {person["id"]: 0 for person in staff}
    warnings: list[str] = []

    for offset in range(7):
        day = start_day + timedelta(days=offset)
        for shift in SHIFTS:
            start_dt, end_dt = shift_window(day, shift)
            needed = required[shift]
            for slot in range(needed):
                candidates = []
                for person in staff:
                    unavailable = person["id"] in absent or is_within_absence_lock(person["id"], start_dt, manual_absences)
                    already_assigned = person["id"] in {row["employee_id"] for row in assignments if row["date"] == day.isoformat() and row["shift"] == shift}
                    if unavailable or already_assigned:
                        continue
                    if shift == "Nachtdienst" and not person["night"]:
                        continue
                    rest_ok = person["id"] not in last_end or start_dt - last_end[person["id"]] >= timedelta(hours=11)
                    if not rest_ok:
                        continue
                    qualification_score = 0 if person["qualification"] in {"Pflegefachkraft", "Schichtleitung"} else 1
                    candidates.append((qualification_score, worked[person["id"]], person["hours"], person))
                if not candidates:
                    warnings.append(f"{day:%d.%m.}: {shift} Slot {slot + 1} konnte nicht regelkonform besetzt werden.")
                    continue
                _, _, _, person = sorted(candidates, key=lambda candidate: candidate[:3])[0]
                assignments.append({"date": day.isoformat(), "day": day.strftime("%a %d.%m."), "shift": shift, "employee_id": person["id"], "name": person["name"], "qualification": person["qualification"], "department": person["department"], "slot": slot + 1})
                worked[person["id"]] += 8
                last_end[person["id"]] = end_dt

    if absent:
        warnings.insert(0, f"Szenario aktiv: {len(absent)} Mitarbeitende sind kurzfristig abwesend. Es wurden keine Gesundheitsdaten verarbeitet.")
    if manual_absences:
        warnings.insert(0, f"Manuelle Anpassung: {len(manual_absences)} schichtbezogene Ausfalltage wurden berücksichtigt.")
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
    required = {shift: st.number_input(shift, min_value=1, max_value=6, value=3 if shift != "Nachtdienst" else 2, key=shift) for shift in SHIFTS}
    generate = st.button("Plan neu berechnen", type="primary", use_container_width=True)

dataset_key = hashlib.sha256(uploaded_file.getvalue() + selected_department.encode()).hexdigest()
if st.session_state.get("dataset_key") != dataset_key:
    st.session_state.manual_absences = set()
    st.session_state.pop("plan", None)
    st.session_state.dataset_key = dataset_key
if "manual_absences" not in st.session_state:
    st.session_state.manual_absences = set()
if generate or st.session_state.get("rebuild", False) or "plan" not in st.session_state:
    st.session_state.plan, st.session_state.warnings = build_plan(start_day, scenario, required, staff, st.session_state.manual_absences)
    st.session_state.plan_meta = (start_day, scenario, selected_department)
    st.session_state.rebuild = False

plan = st.session_state.plan
warnings = st.session_state.warnings
absent = absent_ids(scenario, staff)
filled = len(plan)
expected = sum(required.values()) * 7
coverage = round(filled / expected * 100) if expected else 0
qualified_nights = sum(row["shift"] == "Nachtdienst" and row["qualification"] in {"Pflegefachkraft", "Schichtleitung"} for row in plan)

with st.sidebar.expander("Person manuell als Ausfall markieren", expanded=True):
    st.caption("Wähle eine bereits eingeplante Person. Die Abwesenheit gilt für diesen Dienst und bis zu 5 Folgetage.")
    absence_day = st.selectbox("Tag", [start_day + timedelta(days=offset) for offset in range(7)], format_func=lambda selected: selected.strftime("%A, %d.%m."))
    absence_shift = st.selectbox("Schicht", list(SHIFTS), key="absence_shift")
    scheduled = [row for row in plan if row["date"] == absence_day.isoformat() and row["shift"] == absence_shift]
    scheduled_people = {row["employee_id"]: row["name"] for row in scheduled}
    if scheduled_people:
        selected_id = st.selectbox("Eingeplante Person", list(scheduled_people), format_func=lambda employee_id: f"{scheduled_people[employee_id]} ({employee_id})")
        max_duration = min(5, 7 - (absence_day - start_day).days)
        duration = st.slider("Dauer in Tagen", 1, max_duration, 1)
        if st.button("Ausfall anwenden", use_container_width=True):
            for offset in range(duration):
                affected_day = absence_day + timedelta(days=offset)
                st.session_state.manual_absences.add((selected_id, affected_day.isoformat(), absence_shift))
            st.session_state.rebuild = True
            st.rerun()
    else:
        st.info("Für diese Schicht ist aktuell niemand eingetragen.")
    if st.session_state.manual_absences:
        st.caption(f"Aktive manuelle Ausfalltage: {len(st.session_state.manual_absences)}")
        if st.button("Letzte manuelle Anpassung entfernen", use_container_width=True):
            st.session_state.manual_absences.pop()
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
    shown = plan if view == "Alle Schichten" else ([row for row in plan if row["shift"] == "Nachtdienst"] if view == "Nur Nachtdienste" else [])
    if view == "Nur offene Slots":
        st.info("Offene Slots werden in den Prüfhinweisen ausgewiesen.")
    else:
        st.dataframe(shown, column_config={"date": None, "employee_id": "ID", "day": "Tag", "shift": "Dienst", "slot": "Slot", "name": "Name", "qualification": "Qualifikation", "department": "Abteilung"}, hide_index=True, use_container_width=True)
    st.caption(f"Nachtdienste mit Pflegefachkraft/Schichtleitung: {qualified_nights} von {required['Nachtdienst'] * 7} angeforderten Slots.")

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
