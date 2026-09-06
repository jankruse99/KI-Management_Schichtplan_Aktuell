from __future__ import annotations

import csv
import hashlib
from html import escape
import io
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
        expected_id = f"MA-{line_number - 1:03d}"
        if employee_id != expected_id:
            raise ValueError(f"Zeile {line_number}: erwartet wird die fortlaufende ID {expected_id}.")
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
    writer.writerow({"Mitarbeiter_ID": "MA-001", "Qualifikation": "Pflegefachkraft", "Arbeitszeitmodell": "Vollzeit", "Nachtschicht_moeglich": "WAHR"})
    return output.getvalue()


def is_ill(employee_id: str, day: date, illnesses: list[dict]) -> bool:
    for illness in illnesses:
        if illness["employee_id"] != employee_id:
            continue
        start = date.fromisoformat(illness["start"])
        end = start + timedelta(days=illness["days"])
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
    return list(dict.fromkeys(warnings))


def build_plan(start_day: date, required: dict[str, int], staff: list[dict], illnesses: list[dict] | None = None, baseline_plan: list[dict] | None = None) -> tuple[list[dict], list[str]]:
    illnesses = illnesses or []
    assignments: list[dict] = []
    worked: dict[str, float] = {person["id"]: 0 for person in staff}
    night_worked: dict[str, int] = {person["id"]: 0 for person in staff}
    worked_days: dict[str, set[date]] = {person["id"]: set() for person in staff}
    warnings: list[str] = []

    if baseline_plan:
        assignments = [
            dict(row)
            for row in baseline_plan
            if not is_ill(row["employee_id"], date.fromisoformat(row["date"]), illnesses)
        ]
        for row in assignments:
            employee_id = row["employee_id"]
            worked[employee_id] += SHIFTS[row["shift"]][2]
            worked_days[employee_id].add(date.fromisoformat(row["date"]))
            if row["shift"] == "Nachtdienst":
                night_worked[employee_id] += 1

    for offset in range(28):
        day = start_day + timedelta(days=offset)
        for shift in SHIFTS:
            start_dt, end_dt = shift_window(day, shift)
            needed = required[shift]
            for slot in range(needed):
                if any(row["date"] == day.isoformat() and row["shift"] == shift and row["slot"] == slot + 1 for row in assignments):
                    continue
                candidates = []
                assigned_this_shift = [row for row in assignments if row["date"] == day.isoformat() and row["shift"] == shift]
                needs_shift_lead = not any(row["qualification"] == "Schichtleitung" for row in assigned_this_shift)
                needs_nurse = not any(row["qualification"] in {"Pflegefachkraft", "Schichtleitung"} for row in assigned_this_shift)
                for person in staff:
                    unavailable = is_ill(person["id"], day, illnesses)
                    already_assigned = person["id"] in {row["employee_id"] for row in assignments if row["date"] == day.isoformat() and row["shift"] == shift}
                    if unavailable or already_assigned:
                        continue
                    if shift == "Nachtdienst" and not person["night"]:
                        continue
                    if needs_shift_lead and person["qualification"] != "Schichtleitung":
                        continue
                    if not needs_shift_lead and needs_nurse and person["qualification"] not in {"Pflegefachkraft", "Schichtleitung"}:
                        continue
                    person_rows = sorted(
                        [row for row in assignments if row["employee_id"] == person["id"]],
                        key=lambda row: shift_window(date.fromisoformat(row["date"]), row["shift"])[0],
                    )
                    rest_ok = all(
                        start_dt - shift_window(date.fromisoformat(row["date"]), row["shift"])[1] >= timedelta(hours=11)
                        or shift_window(date.fromisoformat(row["date"]), row["shift"])[0] > start_dt
                        for row in person_rows
                    ) and all(
                        shift_window(date.fromisoformat(row["date"]), row["shift"])[0] - end_dt >= timedelta(hours=11)
                        or shift_window(date.fromisoformat(row["date"]), row["shift"])[1] < start_dt
                        for row in person_rows
                    )
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

    warnings.extend(validate_plan(assignments, staff, start_day, required))
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


def render_schedule_grid(rows: list[dict], start_day: date, changed_slot_keys: set[tuple[str, str, int]] | None = None) -> None:
    changed_slot_keys = changed_slot_keys or set()
    rows_by_slot = {}
    for row in rows:
        rows_by_slot.setdefault((row["date"], row["shift"]), []).append(row)
    week_tabs = st.tabs([f"Woche {week + 1}" for week in range(4)])
    shift_classes = {"Frühdienst": "", "Spätdienst": "late", "Nachtdienst": "night"}
    for week, week_tab in enumerate(week_tabs):
        with week_tab:
            week_start = start_day + timedelta(days=week * 7)
            week_end = week_start + timedelta(days=6)
            st.markdown(f'<div class="week-label">{week_start:%d.%m.%Y} bis {week_end:%d.%m.%Y}</div>', unsafe_allow_html=True)
            day_columns = st.columns(7)
            for offset, column in enumerate(day_columns):
                day = week_start + timedelta(days=offset)
                with column:
                    cards = [f'<div class="schedule-day"><h4>{escape(day.strftime("%a %d.%m."))}</h4>']
                    for shift in SHIFTS:
                        slot_rows = rows_by_slot.get((day.isoformat(), shift), [])
                        slot_key = (day.isoformat(), shift, 0)
                        changed_slot = any(key[:2] == slot_key[:2] for key in changed_slot_keys)
                        card_class = shift_classes[shift] if slot_rows else ("changed-open" if changed_slot else "open")
                        entries = []
                        for row in slot_rows:
                            changed = " changed" if row.get("status") == "Ersatzbesetzung" else ""
                            label = f'{escape(row["employee_id"])} · {escape(row["qualification"])}'
                            if row.get("status") == "Ersatzbesetzung":
                                label += " · Ersatz"
                            entries.append(f'<div class="assignment{changed}">{label}</div>')
                        if not entries:
                            entries.append('<div class="assignment">Ausfall / neu zu besetzen</div>' if changed_slot else '<div class="assignment">Offener Slot</div>')
                        cards.append(f'<div class="shift-card {card_class}"><div class="shift-name">{escape(shift)}</div>{"".join(entries)}</div>')
                    cards.append("</div>")
                    st.markdown("".join(cards), unsafe_allow_html=True)


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
.schedule-day { background:#f7faf9; border:1px solid var(--line); min-height:310px; padding:.55rem; }
.schedule-day h4 { font-family:'Space Grotesk'; font-size:.88rem; margin:0 0 .55rem; }
.shift-card { border-left:3px solid var(--teal); background:#fff; padding:.45rem .5rem; margin:.42rem 0; min-height:55px; }
.shift-card.late { border-left-color:#e6a23c; }
.shift-card.night { border-left-color:#5367a8; }
.shift-card.open { border-left-color:var(--coral); background:#fff5ed; }
.shift-card.changed-open { border-left-color:#c6533c; background:#fff0eb; }
.shift-name { color:var(--muted); font-size:.68rem; text-transform:uppercase; letter-spacing:.05em; }
.assignment { font-size:.76rem; line-height:1.35; margin-top:.2rem; }
.assignment.changed { color:#a94f37; font-weight:700; }
.week-label { color:var(--teal); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; font-weight:700; margin:.5rem 0 .35rem; }
</style>""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="eyebrow">CarePlan / Prototyp 01</div><h1>Schichtplanung, die mitdenkt.</h1><p>Regelkonforme Planung für Früh-, Spät- und Nachtdienste mit schneller Ausfallanpassung.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Aktuelle Stammdaten")
    uploaded_file = st.file_uploader("Mitarbeitenden-CSV hochladen", type="csv", help="CSV mit den im Tab Regeln & Annahmen beschriebenen Spalten.")
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
    st.markdown("**Mindestbesetzung je Schicht**")
    required = {shift: st.number_input(shift, min_value=1, max_value=6, value={"Frühdienst": 5, "Spätdienst": 4, "Nachtdienst": 2}[shift], key=shift) for shift in SHIFTS}
    generate = st.button("Plan neu berechnen", type="primary", use_container_width=True)

config_fingerprint = f"{start_day.isoformat()}|{required}"
dataset_key = hashlib.sha256(uploaded_file.getvalue() + config_fingerprint.encode()).hexdigest()
if st.session_state.get("dataset_key") != dataset_key:
    st.session_state.illnesses = []
    st.session_state.pop("plan", None)
    st.session_state.pop("baseline_plan", None)
    st.session_state.dataset_key = dataset_key
if "illnesses" not in st.session_state:
    st.session_state.illnesses = []
if "baseline_plan" not in st.session_state:
    st.session_state.baseline_plan, _ = build_plan(start_day, required, staff)
if generate or st.session_state.get("rebuild", False) or "plan" not in st.session_state:
    st.session_state.plan, st.session_state.warnings = build_plan(start_day, required, staff, st.session_state.illnesses, st.session_state.baseline_plan)
    st.session_state.plan_meta = (start_day, selected_department)
    st.session_state.rebuild = False

plan = st.session_state.plan
warnings = st.session_state.warnings
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
baseline_slot_keys = set(baseline_by_slot)
current_slot_keys = set(current_by_slot)
changed_slot_keys = {
    slot_key for slot_key in baseline_slot_keys | current_slot_keys
    if baseline_by_slot.get(slot_key, {}).get("employee_id") != current_by_slot.get(slot_key, {}).get("employee_id")
}
hours_by_employee = {person["id"]: {"Mitarbeiter-ID": person["id"], "Arbeitszeitmodell": person["employment"], "Sollstunden (4 Wochen)": person["hours"] * 4, "Geplante Stunden": 0.0, "Abweichung": 0.0, "Nachtdienste": 0, "Ersatzeinsätze": 0} for person in staff}
for row in plan:
    summary = hours_by_employee[row["employee_id"]]
    row_key = (row["date"], row["shift"], row["slot"])
    summary["Geplante Stunden"] += SHIFTS[row["shift"]][2]
    summary["Nachtdienste"] += row["shift"] == "Nachtdienst"
    summary["Ersatzeinsätze"] += row_key in changed_slot_keys and baseline_by_slot.get(row_key, {}).get("employee_id") != row["employee_id"]
for summary in hours_by_employee.values():
    summary["Abweichung"] = round(summary["Geplante Stunden"] - summary["Sollstunden (4 Wochen)"], 2)
hours_table = list(hours_by_employee.values())

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
for column, value, label in zip(metric_cols, [f"{coverage}%", filled, len(staff), len(warnings)], ["Besetzungsgrad", "Dienste geplant", "Verfügbar", "Prüfhinweise"]):
    column.markdown(f'<div class="metric"><strong>{value}</strong><span>{label}</span></div>', unsafe_allow_html=True)

st.write("")
if warnings:
    with st.expander(f"Prüfhinweise ({len(warnings)})", expanded=True):
        for warning in warnings:
            st.markdown(f'<div class="notice">{warning}</div>', unsafe_allow_html=True)
else:
    st.success("Alle angeforderten Dienste konnten unter den hinterlegten Regeln besetzt werden.")

tab_plan, tab_hours, tab_absences, tab_staff, tab_rules = st.tabs(["Wochenplan", "Arbeitszeit", "Ausfälle & Änderungen", "Mitarbeitende", "Regeln & Annahmen"])
with tab_plan:
    st.markdown("#### Grafischer Einsatzplan")
    st.caption("Teal = Frühdienst, Gold = Spätdienst, Blau = Nachtdienst, Rot = offener Slot. Orange markierte Einträge sind Ersatzbesetzungen.")
    render_schedule_grid(display_plan, start_day, changed_slot_keys)
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

with tab_hours:
    st.markdown("#### Arbeitszeitübersicht für 28 Tage")
    st.caption("Die Sollstunden werden aus dem Arbeitszeitmodell abgeleitet: Vollzeit 38,5 und Teilzeit 23,1 Wochenstunden.")
    st.dataframe(hours_table, column_config={"Mitarbeiter-ID": "Mitarbeiter-ID", "Arbeitszeitmodell": "Arbeitszeitmodell", "Sollstunden (4 Wochen)": st.column_config.NumberColumn("Sollstunden (4 Wochen)", format="%.2f"), "Geplante Stunden": st.column_config.NumberColumn("Geplante Stunden", format="%.2f"), "Abweichung": st.column_config.NumberColumn("Abweichung", format="%.2f"), "Nachtdienste": "Nachtdienste", "Ersatzeinsätze": "Ersatzeinsätze"}, hide_index=True, use_container_width=True)

with tab_absences:
    st.markdown("#### Aktive Ausfälle und Planänderungen")
    if st.session_state.illnesses:
        illness_rows = [{"Mitarbeiter-ID": item["employee_id"], "Krank ab": item["start"], "Ausfalltage": item["days"]} for item in st.session_state.illnesses]
        st.dataframe(illness_rows, hide_index=True, use_container_width=True)
    else:
        st.info("Aktuell sind keine Krankmeldungen erfasst.")
    if changes:
        st.markdown(f"**Geänderte Besetzungen: {len(changes)}**")
        st.dataframe(changes, column_config={"date": "Datum", "shift": "Dienst", "slot": "Slot", "employee_id": "Neue ID", "status": "Status"}, hide_index=True, use_container_width=True)
    else:
        st.success("Seit dem Ausgangsplan wurden keine Besetzungen geändert.")

with tab_staff:
    st.dataframe(staff, column_config={"id": "ID", "name": "Mitarbeiter-ID", "qualification": "Qualifikation", "employment": "Arbeitszeitmodell", "hours": st.column_config.NumberColumn("Planstunden", format="%.0f"), "night": "Nachtdienst geeignet"}, hide_index=True, use_container_width=True)

with tab_rules:
    st.markdown("""#### Zweck und Planungszeitraum
Der Planer erzeugt einen zusammenhängenden Dienstplan für **28 Tage bzw. vier Wochen**. Alle Dienste werden mit Zeitstempeln berechnet; insbesondere endet der Nachtdienst am Folgetag. Bei einer Krankmeldung bleibt der ursprüngliche Plan möglichst unverändert. Nur die dadurch frei gewordenen Slots werden neu besetzt.

#### Schichtmodell
- **Frühdienst:** 06:00 bis 14:12 Uhr, 7,7 Nettoarbeitsstunden.
- **Spätdienst:** 13:30 bis 21:42 Uhr, 7,7 Nettoarbeitsstunden.
- **Nachtdienst:** 21:00 bis 06:15 Uhr am Folgetag, 8,25 Nettoarbeitsstunden.
- Jeder Dienst wird als ein vollständiger Schichtblock geplant. Pausen, Übergaben und gesetzliche Ausgleichszeiträume werden nicht separat modelliert.

#### Harte Einsatzregeln
- **Ruhezeit H-03:** Zwischen dem Ende eines Dienstes und dem Beginn des nächsten Dienstes müssen mindestens 11 Stunden liegen. Früh-, Spät- und Nachtdienste werden anhand ihrer tatsächlichen Uhrzeiten verglichen, nicht anhand des Datums allein.
- **Nachtdienst H-15:** Nachtdienste werden ausschließlich an Personen mit `Nachtschicht_moeglich = wahr` vergeben. `falsch`, `FALSE`, `0` oder `nein` sperren die Person für Nachtdienste.
- **Schichtleitung H-10:** Jede Schicht benötigt mindestens eine Person mit der Qualifikation `Schichtleitung`.
- **Fachkraft H-13:** Jede Schicht benötigt mindestens eine `Pflegefachkraft` oder `Schichtleitung`.
- **Mindestbesetzung H-09:** Standardmäßig werden pro Tag fünf Personen im Frühdienst, vier im Spätdienst und zwei im Nachtdienst angefordert. Die Werte können in der Seitenleiste geändert werden. Nicht besetzbare Slots werden als Prüfhinweis ausgegeben.
- **Azubi-Regel H-14:** `Azubi` werden nicht als examinierte Fachkräfte gezählt und dürfen nicht die Mehrheit bilden. Pro Schicht wird höchstens ein Azubi je zwei qualifizierte Fachkräfte zugelassen. Die aktuelle CSV enthält kein Feld für Praxisanleitung; eine separate Praxisanleitungsprüfung findet daher nicht statt.
- **Arbeitszeit H-02/H-21:** Pro Person gilt für die vier Wochen höchstens das kleinere Limit aus 192 Stunden und 110 Prozent der abgeleiteten Vertragsstunden. `Vollzeit` wird mit 38,5 Wochenstunden, `Teilzeit` mit 23,1 Wochenstunden angesetzt.
- **Arbeitstage H-19:** Eine Person darf nicht an mehr als sieben aufeinanderfolgenden Kalendertagen eingeplant werden.
- **Nachtdienstserie H-17:** Eine Person darf nicht mehr als fünf Nachtdienste in Folge erhalten.

#### Auswahl und Verteilung
- Pflegefachkräfte und Schichtleitungen werden bei der Besetzung bevorzugt, damit die Qualifikationsregeln zuerst erfüllt werden.
- Nachtdienste werden bevorzugt an Personen mit bisher weniger Nachtdiensten vergeben.
- Danach werden Personen mit bisher weniger Arbeitsstunden bevorzugt.
- Bei gleicher Eignung werden die hinterlegten Vertragsstunden als Kapazitätspriorität berücksichtigt.
- Der Planer verwendet eine transparente Heuristik und kein mathematisches Optimierungsmodell.

#### Krankmeldungen und Ausfälle
- Eine Krankmeldung benötigt Mitarbeiter-ID, Startdatum und voraussichtliche Dauer in Tagen.
- Eine Krankmeldung über zwei Tage sperrt genau den Starttag und den folgenden Kalendertag.
- Die erkrankte Person wird aus diesen Tagen und allen betroffenen Schichten entfernt.
- Der Ausgangsplan bleibt für alle nicht betroffenen Personen und Slots erhalten.
- Nur die frei gewordenen Slots werden neu besetzt. Ersatzpersonen müssen dieselben Ruhezeit-, Arbeitszeit-, Qualifikations-, Nachtdienst- und Serienregeln erfüllen.
- Ersatzbesetzungen werden im grafischen und tabellarischen Plan als `Ersatzbesetzung` markiert.
- Die anonymisierten Ausfallszenarien entfernen je nach Auswahl die ersten zwei oder fünf Datensätze aus der Verfügbarkeit. Das ist eine Demo-Funktion und keine reale Krankheitsverwaltung.
- Manuelle schichtbezogene Ausfälle sperren die ausgewählte Person für den betreffenden Dienst und ein Zeitfenster von bis zu 24 Stunden.

#### CSV-Stammdaten
Die hochgeladene UTF-8-CSV benötigt die vier Spalten `Mitarbeiter_ID`, `Qualifikation`, `Arbeitszeitmodell` und `Nachtschicht_moeglich`. Die IDs müssen ab Zeile 2 fortlaufend `MA-001`, `MA-002`, `MA-003` usw. lauten. Erlaubte Qualifikationen sind `Schichtleitung`, `Azubi`, `Pflegefachkraft` und `Pflegehilfskraft`. Beim Arbeitszeitmodell sind `Teilzeit` und `Vollzeit` erlaubt. Für `Nachtschicht_moeglich` werden `wahr`/`falsch`, `TRUE`/`FALSE` oder `1`/`0` akzeptiert. Komma, Semikolon und Tabulator werden als Trennzeichen erkannt.

Beim Import wird außerdem geprüft, dass mindestens eine Schichtleitung, mindestens zwei nachtdienstfähige Personen, eindeutige IDs und gültige Enum-Werte vorhanden sind.

#### Nicht Bestandteil der aktuellen Berechnung
Nicht separat berechnet werden Pausenblöcke, Sonn- und Feiertagskontingente, Ersatzruhetage, Urlaub, Fortbildung, Wunschfrei, Teamzugehörigkeit, PpUGV-Quoten nach Stationsart und Bettenzahl, Springerpool, Leihpersonal, Mutterschutz- oder Minderjährigen-Sonderregeln sowie eine historische Jahresarbeitszeit. Diese Informationen sind im aktuellen Vier-Spalten-CSV nicht vollständig vorhanden.

Die Planung ist eine transparente technische Empfehlung. Sie ersetzt keine arbeitsrechtliche, tarifliche oder pflegefachliche Prüfung und Freigabe.""")
