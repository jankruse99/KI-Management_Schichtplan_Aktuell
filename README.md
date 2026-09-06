# CarePlan: KI-gestützte Schichtplanung

Ein Streamlit-Prototyp für die regelbasierte Erstellung und kurzfristige Anpassung eines Krankenhaus-Schichtplans. Die aktuellen Mitarbeitenden werden bei jedem Start bzw. bei jeder Änderung als CSV-Datei hochgeladen.

## Funktionen

- Wochenplanung für Früh-, Spät- und Nachtdienst
- Mindestbesetzung je Schicht konfigurierbar
- Ausfallszenarien: keine Ausfälle, zwei kurzfristige Ausfälle und Ausfallwelle
- Prüfung von 11 Stunden Ruhezeit und Qualifikation im Nachtdienst
- Prüfhinweise für offene Slots und anonymisierte Ausfälle
- Upload aktueller Stammdaten als CSV mit festem Vier-Spalten-Schema
- Manuelle, schichtbezogene Ausfalleingabe mit mehrtägiger Dauer
- CSV-Export des erzeugten Plans

## Aufbau der Stammdaten-CSV

Die Datei muss UTF-8-kodiert sein und genau diese Kopfzeile enthalten. Komma, Semikolon oder Tabulator werden als Trennzeichen erkannt:

```csv
id,qualification,employment,night
ma-001,Pflegefachkraft,Vollzeit,wahr
ma-002,Pflegehilfskraft,Teilzeit,falsch
```

| Spalte | Pflicht | Inhalt |
| --- | --- | --- |
| `id` | ja | Eindeutige Personal-ID exakt im Format `ma-001` |
| `qualification` | ja | `Schichtleitung`, `Azubi`, `Pflegefachkraft` oder `Pflegehilfskraft` |
| `employment` | ja | Arbeitszeitmodell: `Teilzeit` oder `Vollzeit` |
| `night` | ja | Nachtdienst-Eignung: `wahr` oder `falsch` |

Leere Pflichtfelder, doppelte IDs oder ungültige Werte werden beim Upload abgewiesen. Da das reduzierte Schema keine Namen und Abteilungen enthält, verwendet die App die Mitarbeiter-ID als Anzeige und plant den hochgeladenen Gesamtbereich. Eine passende Beispieldatei kann direkt in der Seitenleiste heruntergeladen werden.

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
