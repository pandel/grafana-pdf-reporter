# Lokale Entwicklungsumgebung ohne Docker

Diese Anleitung beschreibt, wie du die Grafana PDF Reporter Anwendung auch ohne Docker lokal in Betrieb nehmen kannst. Diese Vorgehensweise ist besonders nützlich für Entwicklungszwecke oder wenn du die Anwendung in einer Umgebung ohne Docker ausführen möchtest.

## Backend (Python/FastAPI)

### Voraussetzungen

- Python 3.9
- pip (Python Package Manager)
- Playwright mit Browser-Unterstützung
- Grafana-Instanz, auf die zugegriffen werden kann

### Installation

1. Navigiere in das Backend-Verzeichnis:
   ```bash
   cd grafana-pdf-reporter/backend
   ```

2. Erstelle eine virtuelle Python-Umgebung und aktiviere sie:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   ```

3. Installiere die erforderlichen Abhängigkeiten:
   ```bash
   pip install -r requirements.txt
   ```

4. Installiere Playwright und die benötigten Browser:
   ```bash
   playwright install-deps
   playwright install chromium
   ```
   
5. Erstelle die notwendigen Verzeichnisse, falls diese nicht existieren:
   ```bash
   mkdir -p templates layouts schedules config
   ```

### Konfiguration

1. Erstelle eine `.env`-Datei im Backend-Verzeichnis mit den folgenden Umgebungsvariablen:
   ```
   LOGLEVEL=debug
   HOST=0.0.0.0
   PORT=8000
   TZ=Europe/Berlin
   SECRET_KEY='77oYKYadaKkYGsbvr6sWGRczQ1Xu8T6bGl4TW5kIfD8='
   ```

### Starten des Backends

1. Führe den folgenden Befehl aus, um das Backend zu starten:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Das Backend ist nun unter `http://localhost:8000` verfügbar. Die API-Dokumentation kann unter `http://localhost:8000/api/docs` eingesehen werden.

## Frontend (Vue.js)

### Voraussetzungen

- Node.js 16 oder höher
- npm (Node Package Manager)

### Installation

1. Navigiere in das Frontend-Verzeichnis:
   ```bash
   cd grafana-pdf-reporter/frontend
   ```

2. Installiere die erforderlichen Abhängigkeiten:
   ```bash
   npm install
   ```
   
### Konfiguration

1. Erstelle oder aktualisiere die Datei `public/env-config.js` mit den folgenden Inhalten:
   ```javascript
   window.VITE_API_URL = "http://localhost:8000/api"
   ```

2. Alternativ kannst du eine `.env.local`-Datei erstellen:
   ```
   VITE_API_URL=http://localhost:8000/api
   ```

### Starten des Frontends

1. Führe den folgenden Befehl aus, um das Frontend im Entwicklungsmodus zu starten:
   ```bash
   npm run dev
   ```

2. Das Frontend ist nun unter `http://localhost:5173` verfügbar.

## Verbindung zu Grafana

Bei der lokalen Entwicklung müssen die Einstellungen zur Verbindung mit deiner Grafana-Instanz manuell konfiguriert werden:

1. Rufe die Anwendung auf und navigiere zu "Einstellungen"
2. Gib die Grafana-URL, Benutzername und Passwort ein
3. Teste die Verbindung mit der Schaltfläche "Verbindung testen"

## Bekannte Einschränkungen bei der lokalen Entwicklung

1. **CORS-Einstellungen**: Bei der lokalen Entwicklung könnten CORS-Probleme auftreten. Falls nötig, aktiviere CORS in der Grafana-Konfiguration oder verwende einen Browser mit deaktivierten CORS-Einschränkungen für Entwicklungszwecke.

Bspw. Chrome mit deaktivierter Web Security unter Mac OS starten:

`open -n -a /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --args --user-data-dir="/tmp/chrome_dev_test" --disable-web-security`

2. **SSL/TLS**: Die lokale Entwicklungsumgebung verwendet standardmäßig HTTP. Wenn deine Grafana-Instanz HTTPS erfordert, müsstest du möglicherweise zusätzliche Konfigurationen vornehmen.

3. **Zeitpläne**: Die Zeitpläne für Berichte funktionieren nur, wenn das Backend kontinuierlich läuft. Bei der lokalen Entwicklung werden geplante Berichte möglicherweise nicht wie erwartet ausgeführt, wenn das Backend neu gestartet wird.

## Produktionsbereitstellung ohne Docker

Für eine Produktionsbereitstellung ohne Docker musst du:

1. **Backend**: Das Backend als Dienst einrichten, z.B. mit systemd, supervisor oder einem ähnlichen Dienst-Manager.
   ```bash
   # Beispiel für ein systemd-Service-File
   gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
   ```

2. **Frontend**: Das Frontend für die Produktion bauen und mit einem Webserver wie Nginx oder Apache bereitstellen:
   ```bash
   # Frontend bauen
   cd frontend
   npm run build
   
   # Die erzeugten Dateien im Verzeichnis dist/ müssen dann auf den Webserver kopiert werden
   ```

3. **Reverse Proxy**: Einen Reverse-Proxy wie Nginx konfigurieren, um Frontend und Backend unter einer einheitlichen Domain bereitzustellen. Die Konfiguration kannst du aus der bestehenden Nginx-Konfiguration im `nginx/conf/default.prod.conf` übernehmen.

Beachte, dass diese Konfiguration für eine vollständige Produktionsumgebung weitere Anpassungen und Sicherheitsüberlegungen erfordert.

# API-Nutzung mit curl

Um mit dem Backend über die REST-API zu interagieren, musst du ein Authentifizierungstoken erhalten. Hier ist ein Beispiel, wie du mit `curl` ein Bearer-Token erhältst und die API abfragst:

> **Hinweis**: Wenn du die Anwendung mit der vorhandenen `docker-compose.yml` Datei gestartet hast, wird der folgende Ansatz nicht funktionieren, da der Port 8000 des Backend-Containers nicht nach außen freigegeben ist. Für direkten API-Zugriff müsstest du die `docker-compose.yml` anpassen, um den Port zu exponieren:
> ```yaml
> services:
>   backend:
>     # ... andere Einstellungen ...
>     ports:
>       - "8000:8000"  # Füge diese Zeile hinzu
> ```
> Alternativ entfernst du einfach die Portangabe `:8000` aus den nachfolgenden `curl` Befehlen.

### Authentifizierungs-Token erhalten

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -d "username=admin&password=admin123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Die Antwort sollte ein JSON-Objekt mit einem Zugriffstoken sein, etwa so:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### API-Endpunkte mit dem Token aufrufen

Verwende das erhaltene Token, um auf geschützte API-Endpunkte zuzugreifen. Hier ist ein Beispiel zum Abrufen aller Organisationen:

```bash
curl -X GET http://localhost:8000/api/organizations \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Die Antwort sollte eine Liste der verfügbaren Grafana-Organisationen sein:

```json
[
  {
    "id": 1,
    "name": "Main Org."
  },
  {
    "id": 2,
    "name": "Test Org"
  }
]
```

Du kannst dieses Authentifizierungsmuster für alle API-Endpunkte verwenden, die in der API-Dokumentation unter `http://localhost:8000/api/docs` aufgeführt sind.
