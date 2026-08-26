from __future__ import annotations

import csv
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
    "Frühdienst": (time(6), time(14), 8),
    "Spätdienst": (time(14), time(22), 8),
    "Nachtdienst": (time(22), time(6), 8),
}


def shift_window(day: date, shift: str) -> tuple[datetime, datetime]:
    start, end, _ = SHIFTS[shift]
    start_dt = datetime.combine(day, start)
    end_day = day + timedelta(days=1) if end <= start else day
    return start_dt, datetime.combine(end_day, end)


def absent_ids(scenario: str) -> set[str]:
    return {"MA002", "MA018"} if scenario == "Zwei kurzfristige Ausfälle" else ({"MA002", "MA018", "MA025", "MA029", "MA040"} if scenario == "Ausfallwelle" else set())


def is_within_absence_lock(employee_id: str, start_dt: datetime, manual_absences: set[tuple[str, str, str]]) -> bool:
    for absent_employee_id, absent_date, absent_shift in manual_absences:
        if absent_employee_id != employee_id:
            continue
        absent_start, _ = shift_window(date.fromisoformat(absent_date), absent_shift)
        if absent_start <= start_dt < absent_start + timedelta(hours=24):
            return True
    return False


def build_plan(start_day: date, scenario: str, required: dict[str, int], manual_absences: set[tuple[str, str, str]] | None = None) -> tuple[list[dict], list[str]]:
    absent = absent_ids(scenario)
    manual_absences = manual_absences or set()
    assignments: list[dict] = []
    last_end: dict[str, datetime] = {}
    worked: dict[str, float] = {person["id"]: 0 for person in STAFF}
    warnings: list[str] = []

    for offset in range(7):
        day = start_day + timedelta(days=offset)
        for shift in SHIFTS:
            start_dt, end_dt = shift_window(day, shift)
            needed = required[shift]
            for slot in range(needed):
                candidates = []
                for person in STAFF:
                    unavailable = person["id"] in absent or is_within_absence_lock(person["id"], start_dt, manual_absences)
                    already_assigned = person["id"] in {row["employee_id"] for row in assignments if row["date"] == day.isoformat() and row["shift"] == shift}
                    if unavailable or already_assigned:
                        continue
                    if shift == "Nachtdienst" and not person["night"]:
                        continue
                    rest_ok = person["id"] not in last_end or start_dt - last_end[person["id"]] >= timedelta(hours=11)
                    if not rest_ok:
                        continue
                    qualification_score = 0 if person["qualification"] in {"Pflegefachkraft", "Stationsleitung"} else 1
                    candidates.append((qualification_score, worked[person["id"]], person["hours"], person))
                if not candidates:
                    warnings.append(f"{day:%d.%m.}: {shift} Slot {slot + 1} konnte nicht regelkonform besetzt werden.")
                    continue
                _, _, _, person = sorted(candidates, key=lambda candidate: candidate[:3])[0]
                assignments.append({"date": day.isoformat(), "day": day.strftime("%a %d.%m."), "shift": shift, "employee_id": person["id"], "name": person["name"], "qualification": person["qualification"], "slot": slot + 1})
                worked[person["id"]] += 8
                last_end[person["id"]] = end_dt

    if absent:
        warnings.insert(0, f"Szenario aktiv: {len(absent)} Mitarbeitende sind kurzfristig abwesend. Es wurden keine Gesundheitsdaten verarbeitet.")
    if manual_absences:
        warnings.insert(0, f"Manuelle Anpassung: {len(manual_absences)} schichtbezogene Ausfalltage wurden berücksichtigt.")
    return assignments, warnings


def as_csv(rows: list[dict]) -> str:
    output = io.StringIO()
    fields = ["date", "day", "shift", "slot", "employee_id", "name", "qualification"]
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
    st.markdown("### Plan konfigurieren")
    start_day = st.date_input("Planwoche ab", date.today() - timedelta(days=date.today().weekday()))
    scenario = st.selectbox("Ausfallszenario", ["Keine Ausfälle", "Zwei kurzfristige Ausfälle", "Ausfallwelle"], help="Nur anonymisierte Ausfall-Slots, keine Diagnosen oder Gesundheitsdaten.")
    st.markdown("**Mindestbesetzung je Schicht**")
    required = {shift: st.number_input(shift, min_value=1, max_value=6, value=3 if shift != "Nachtdienst" else 2, key=shift) for shift in SHIFTS}
    generate = st.button("Plan neu berechnen", type="primary", use_container_width=True)

if "manual_absences" not in st.session_state:
    st.session_state.manual_absences = set()
if generate or st.session_state.get("rebuild", False) or "plan" not in st.session_state:
    st.session_state.plan, st.session_state.warnings = build_plan(start_day, scenario, required, st.session_state.manual_absences)
    st.session_state.plan_meta = (start_day, scenario)
    st.session_state.rebuild = False

plan = st.session_state.plan
warnings = st.session_state.warnings
absent = absent_ids(scenario)
filled = len(plan)
expected = sum(required.values()) * 7
coverage = round(filled / expected * 100) if expected else 0
qualified_nights = sum(row["shift"] == "Nachtdienst" and row["qualification"] in {"Pflegefachkraft", "Stationsleitung"} for row in plan)

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
for column, value, label in zip(metric_cols, [f"{coverage}%", filled, len(STAFF) - len(absent), len(warnings)], ["Besetzungsgrad", "Dienste geplant", "Verfügbar", "Prüfhinweise"]):
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
        st.dataframe(shown, column_config={"date": None, "employee_id": "ID", "day": "Tag", "shift": "Dienst", "slot": "Slot", "name": "Name", "qualification": "Qualifikation"}, hide_index=True, use_container_width=True)
    st.caption(f"Nachtdienste mit Pflegefachkraft/Stationsleitung: {qualified_nights} von {required['Nachtdienst'] * 7} angeforderten Slots.")

with tab_staff:
    available = [person for person in STAFF if person["id"] not in absent]
    st.dataframe(available, column_config={"id": "ID", "name": "Name", "qualification": "Qualifikation", "employment": "Beschäftigungsumfang", "hours": st.column_config.NumberColumn("Wochenstunden", format="%.2f"), "night": "Nachtdienst geeignet"}, hide_index=True, use_container_width=True)
    if absent:
        st.caption("Abwesend in diesem Szenario: " + ", ".join(sorted(absent)))

with tab_rules:
    st.markdown("""#### Verbindliche Prüfregeln
- **Ruhezeit:** Zwischen zwei Diensten liegen mindestens 11 Stunden.
- **Qualifikation:** Nachtwachen werden nur Pflegefachkräften oder Stationsleitungen zugewiesen.
- **Arbeitszeit:** Jeder Dienst umfasst 8 Stunden; die Wochenstunden aus den Stammdaten dienen als Kapazitätspriorität.
- **Mindestbesetzung:** Früh-, Spät- und Nachtdienst werden pro Tag separat geprüft.
- **Ausfälle:** Szenarien sind anonymisierte Verfügbarkeitsänderungen. Es werden keine individuellen Gesundheitsdaten gespeichert oder verarbeitet.

Die Empfehlung verteilt zuerst qualifizierte Personen und priorisiert danach die geringste bisher geplante Arbeitszeit. Das ist eine transparente Heuristik für den Prototyp und ersetzt keine arbeitsrechtliche oder pflegefachliche Freigabe.""")
