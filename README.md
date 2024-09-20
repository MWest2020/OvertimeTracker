# Tempo Worklog Analyzer

Dit script haalt worklog gegevens op van de Tempo API en genereert Excel-rapporten met gedetailleerde informatie over gewerkte uren, overuren, verlof en verzuim.

## Vereisten

- Python 3.7+
- pip (Python package installer)

## Installatie

1. Clone de repository of download de bronbestanden.

2. Installeer de vereiste packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Maak een `.env` bestand aan in de hoofdmap van het project en voeg je Tempo API token toe:
   ```env
   TEMPO_TOKEN=your_tempo_api_token_here
   ```

4. Maak een `account_info.json` bestand aan met de account ID's en namen:
   ```json
   {
     "61ddda5ce7637900686ae43f": "Pika Chu",
     "5f02b8549d9a120029s52b1": "Willy Wortel",
     "5db18fb0af604e0db364d45f": "Barry Baas"
   }
   ```

## Gebruik

Het script kan op verschillende manieren worden gebruikt:

1. Voor een specifiek account en de huidige maand:
   ```bash
   python main.py 61ddda5ce76379006860e43f
   ```

2. Voor een specifiek account en een specifieke maand:
   ```bash
   python main.py 61ddda5ce76379006860e43f --month 8 --year 2023
   ```

3. Voor alle accounts in `account_info.json` voor de huidige maand:
   ```bash
   python main.py
   ```

4. Voor alle accounts in `account_info.json` voor een specifieke maand:
   ```bash
   python main.py --month 8 --year 2023
   ```

Vervang `61ddda5ce76379006860e43f` door het gewenste account ID.

## Output

Het script genereert Excel-bestanden met de volgende informatie:
- Datum
- Totaal gewerkte uren
- VERLOF (gemarkeerd met 'X' indien van toepassing)
- VERZUIM (gemarkeerd met 'X' indien van toepassing)
- Overuren

Overuren worden als volgt berekend:
- Op weekdagen: uren boven 8,5 uur
- In het weekend: alle gewerkte uren

## Opmerkingen

- Zorg ervoor dat je Tempo API token geldig is en de juiste rechten heeft.
- Het script gebruikt de US-based Tempo API URL. Als je Tempo-instantie in een andere regio staat, pas dan de basis-URL aan in het script.
- De `account_info.json` moet up-to-date zijn met de juiste account ID's en namen.

## Probleemoplossing

Als je problemen ondervindt bij het uitvoeren van het script, controleer dan het volgende:
1. Is je Tempo API token geldig en correct ingesteld in het `.env` bestand?
2. Zijn de account ID's in `account_info.json` correct?
3. Heb je alle vereiste packages geïnstalleerd?

Voor verdere ondersteuning, neem contact op met de ontwikkelaar of raadpleeg de Tempo API documentatie.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

[MIT License](LICENSE)
