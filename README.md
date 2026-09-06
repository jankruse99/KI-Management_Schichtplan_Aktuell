# CarePlan: KI-gestützte Schichtplanung

Ein Streamlit-Prototyp für die regelbasierte Erstellung und kurzfristige Anpassung eines Krankenhaus-Schichtplans. Die aktuellen Mitarbeitenden werden bei jedem Start bzw. bei jeder Änderung als CSV-Datei hochgeladen.

## Funktionen

- 28-Tage-Planung für Früh-, Spät- und Nachtdienst
- Mindestbesetzung je Schicht konfigurierbar
- Ausfallszenarien und spontane Krankmeldungen mit ID, Startdatum und Dauer
- Prüfung von 11 Stunden Ruhezeit und Qualifikation im Nachtdienst
- Prüfhinweise für offene Slots und anonymisierte Ausfälle
- Upload aktueller Stammdaten als CSV mit festem Vier-Spalten-Schema
- Manuelle, schichtbezogene Ausfalleingabe mit mehrtägiger Dauer
- CSV-Export des erzeugten Plans

## Regelwerk

Die Planung berücksichtigt im 28-Tage-Fenster insbesondere Mindestbesetzung ohne Azubis, Schichtleitung und examinierte Pflegefachkraft je Schicht, Nachtdienstfreigabe, mindestens 11 Stunden Ruhezeit, Vertragsstunden mit 10-Prozent-Toleranz, maximal sieben Arbeitstage in Folge, maximal fünf Nächte in Folge, den Azubi-Anteil sowie eine gleichmäßigere Verteilung der Nachtdienste. Krankmeldungen sperren die Person am Krankheitstag und am Folgetag für die Planung.

Regeln mit Jahresbezug, Feiertagsausgleich, Stationsart und Bettenzahl, PpUGV-Quoten, Springerpool oder bereits geleisteter Vorjahresarbeit werden als nicht prüfbar ausgewiesen, wenn die dafür benötigten Angaben nicht in der CSV oder im 28-Tage-Fenster vorhanden sind. Die Anwendung ersetzt keine arbeitsrechtliche oder pflegefachliche Freigabe.

## Aufbau der Stammdaten-CSV

Die CSV-Datei muss UTF-8-kodiert sein und diese vier Pflichtspalten enthalten. Ihre Reihenfolge ist frei wählbar. Komma, Semikolon oder Tabulator werden als Trennzeichen erkannt:

```csv
Mitarbeiter_ID,Qualifikation,Arbeitszeitmodell,Nachtschicht_moeglich
MA-001,Pflegefachkraft,Vollzeit,WAHR
MA-002,Pflegehilfskraft,Teilzeit,FALSCH
```

| Spalte | Pflicht | Inhalt |
| --- | --- | --- |
| `Mitarbeiter_ID` | ja | Eindeutige Personal-ID im Format `MA-001`, fortlaufend nummeriert |
| `Qualifikation` | ja | `Schichtleitung`, `Azubi`, `Pflegefachkraft` oder `Pflegehilfskraft` |
| `Arbeitszeitmodell` | ja | `Teilzeit` oder `Vollzeit` |
| `Nachtschicht_moeglich` | ja | `TRUE`/`FALSE`, `true`/`false`, `1`/`0` oder `WAHR`/`FALSCH` |

Leere Pflichtfelder, doppelte IDs oder ungültige Werte werden beim Upload abgewiesen. Optional akzeptiert die App `Wochenstunden`, `Vertragsstunden_Woche`, `Alter`, `Minderjaehrig`, `Ausbildungsjahr`, `Praxisanleiter`, `Urlaub_von`, `Urlaub_bis`, `Wunschfrei` und `Team`. Nach dem Upload wird ein 28-Tage-Plan erzeugt. Krankmeldungen können anschließend über Mitarbeiter-ID, Startdatum und voraussichtliche Dauer eingetragen werden; Ersatzbesetzungen werden im Plan als solche markiert.

Die Planempfehlung ist eine transparente Heuristik und ersetzt keine arbeitsrechtliche oder pflegefachliche Freigabe. Es werden keine individuellen Gesundheitsdaten oder Diagnosen verarbeitet.

## Lokal starten

Prerequisite: install `uv` if you don't already have it.

```
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. Abhängigkeiten synchronisieren

   ```
   $ uv sync
   ```

2. App starten

   ```
   $ uv run streamlit run streamlit_app.py
   ```
