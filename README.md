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

## Aufbau der Stammdaten-CSV

Die Datei muss UTF-8-kodiert sein und diese vier Pflichtspalten enthalten. Ihre Reihenfolge ist frei wählbar. Komma, Semikolon oder Tabulator werden als Trennzeichen erkannt:

```csv
Mitarbeiter_ID,Qualifikation,Arbeitszeitmodell,Nachtschicht_moeglich
ma-001,Pflegefachkraft,Vollzeit,WAHR
ma-002,Pflegehilfskraft,Teilzeit,FALSCH
```

| Spalte | Pflicht | Inhalt |
| --- | --- | --- |
| `Mitarbeiter_ID` | ja | Eindeutige Personal-ID, z. B. `ma-001` |
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
