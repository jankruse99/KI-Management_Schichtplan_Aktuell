# CarePlan: KI-gestützte Schichtplanung

Ein Streamlit-Prototyp für die regelbasierte Erstellung und kurzfristige Anpassung eines Krankenhaus-Schichtplans. Die aktuellen Mitarbeitenden werden bei jedem Start bzw. bei jeder Änderung als CSV-Datei hochgeladen und nach Abteilung gefiltert.

## Funktionen

- Wochenplanung für Früh-, Spät- und Nachtdienst
- Mindestbesetzung je Schicht konfigurierbar
- Ausfallszenarien: keine Ausfälle, zwei kurzfristige Ausfälle und Ausfallwelle
- Prüfung von 11 Stunden Ruhezeit und Qualifikation im Nachtdienst
- Prüfhinweise für offene Slots und anonymisierte Ausfälle
- Upload aktueller Stammdaten als CSV für beliebige Abteilungen
- Manuelle, schichtbezogene Ausfalleingabe mit mehrtägiger Dauer
- CSV-Export des erzeugten Plans

## Aufbau der Stammdaten-CSV

Die Datei muss UTF-8-kodiert sein und genau diese Kopfzeile enthalten. Komma, Semikolon oder Tabulator werden als Trennzeichen erkannt:

```csv
id,name,qualification,employment,hours,night,department
MA001,Max Mustermann,Pflegefachkraft,Vollzeit,38.5,true,Chirurgie
MA002,Erika Beispiel,Pflegehilfskraft,Teilzeit 50%,19.25,false,Chirurgie
```

| Spalte | Pflicht | Inhalt |
| --- | --- | --- |
| `id` | ja | Eindeutige Personal-ID, z. B. `MA001` |
| `name` | ja | Name der Person |
| `qualification` | ja | Qualifikation; `Pflegefachkraft` und `Stationsleitung` gelten für den Nachtdienst als qualifiziert |
| `employment` | ja | Beschäftigungsumfang, z. B. `Vollzeit` oder `Teilzeit 50%` |
| `hours` | ja | Wochenstunden als Zahl, z. B. `38.5` oder `38,5` |
| `night` | ja | Nachtdienst-Eignung: `true`/`false` oder `ja`/`nein` |
| `department` | ja | Abteilung, z. B. `Chirurgie`, `Innere Medizin` oder `Intensivstation` |

Leere Pflichtfelder, doppelte IDs oder ungültige Werte werden beim Upload abgewiesen. Die App erstellt jeweils einen Plan für die ausgewählte Abteilung. Eine passende Beispieldatei kann direkt in der Seitenleiste heruntergeladen werden.

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
