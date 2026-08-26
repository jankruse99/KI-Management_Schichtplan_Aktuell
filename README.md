# CarePlan: KI-gestützte Schichtplanung

Ein Streamlit-Prototyp für die regelbasierte Erstellung und kurzfristige Anpassung eines Krankenhaus-Schichtplans. Der enthaltene Demo-Datensatz bildet die 40 Mitarbeitenden aus den bereitgestellten Stammdaten ab.

## Funktionen

- Wochenplanung für Früh-, Spät- und Nachtdienst
- Mindestbesetzung je Schicht konfigurierbar
- Ausfallszenarien: keine Ausfälle, zwei kurzfristige Ausfälle und Ausfallwelle
- Prüfung von 11 Stunden Ruhezeit und Qualifikation im Nachtdienst
- Prüfhinweise für offene Slots und anonymisierte Ausfälle
- CSV-Export des erzeugten Plans

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
