# Grafana PDF Reporter

## Übersicht

Grafana PDF Reporter ist eine Webanwendung zur Erstellung und Verwaltung von PDF-Berichten aus Grafana-Dashboards. Die Anwendung ermöglicht es, ausgewählte Panels aus Grafana-Dashboards in anpassbaren Layouts zu arrangieren, diese mit benutzerdefinierten Vorlagen zu formatieren und als PDF-Berichte zu exportieren. Zusätzlich können wiederkehrende Berichtsaufträge geplant und per E-Mail versendet werden.

WICHTIG: Es ist keine `grafana-image-renderer` Plugin nötig und auch keine Grafana Enterprise Lizenz!

Einführungsvideo dazu: https://www.youtube.com/watch?v=X6ssfjGbemc

### Verwendete Technologie zur Entwicklung

Die Anwendung wurde komplett in Interaktion mit Anthropic Claude 3.7 Sonnet erstellt. Es kann daher mit Sicherheit sein, dass dem ein oder anderen altgedienten Entwickler Codesequenzen auffallen, die anders oder besser oder optimaler hätten gestaltet und umgesetzt werden können. Mir reicht aber die Tatsache, dass es mit Hilfe der KI überhaupt möglich war, diese Anwendung in einem akzeptablen Zeitrahmen zu entwickeln, frei nach dem Motto: if it works, it works!

## Hauptfunktionen

- **Report Designer**: Erstellung von Berichten durch Auswahl und Anordnung von Panels aus Grafana-Dashboards
- **Layouts**: Speichern und Wiederverwenden von Berichtslayouts
- **Vorlagen**: Anpassbare Header, Footer und Seitenformatierung für konsistentes Erscheinungsbild
- **Zeitpläne**: Automatisierte Erstellung und Versand von Berichten nach Zeitplan
- **Mehrsprachig**: Unterstützung für Deutsch und Englisch
- **Themen**: Helles und dunkles Erscheinungsbild

## Technologie-Stack

- **Frontend**: Vue.js 3, Vuetify, Axios, Pinia, mitt
- **Backend**: Python, FastAPI, Playwright
- **Datenbankintegration**: Grafana API
- **Container**: Docker, Nginx
- **Sicherheit**: JWT-Authentifizierung, HTTPS

## Vorbereitende Arbeiten für NGINX

### SSL-Zertifikate generieren

Für den Produktionsbetrieb wird HTTPS mit SSL-Zertifikaten benötigt. Sie können selbstsignierte Zertifikate mit dem bereitgestellten Skript erstellen:

```bash
./generate-ssl-cert.sh
```

Dieses Skript erstellt die Dateien `cert.pem` und `key.pem` im Verzeichnis `nginx/ssl/`.

### Diffie-Hellman-Parameter generieren

Für zusätzliche Sicherheit bei SSL-Verbindungen werden Diffie-Hellman-Parameter benötigt:

```bash
./generate-dhparam.sh
```

Dieses Skript erstellt die Datei `dhparam.pem` im Verzeichnis `nginx/ssl/`.

### Secret Key generieren

Um einen sicheren, zufälligen Secret Key für die `.env` Datei zu generieren, führen Sie den folgenden Befehl aus:

```bash
docker run --rm -t grafana-pdf-reporter-v3/backend:1.1.1 python /app/generate_secret_key.py
```

### NGINX-Konfiguration anpassen

Die Standard-NGINX-Konfiguration ist für die meisten Anwendungsfälle geeignet. Bei Bedarf können Sie folgende Dateien anpassen:

- `nginx/conf/default.prod.conf`: Haupt-NGINX-Konfiguration
- `nginx/security/security.conf`: Sicherheitseinstellungen für HTTPS

Falls Sie explizit einen benutzerdefinierten Domainnamen verwenden möchten, können sie die `server_name` Direktive in `default.prod.conf` anpassen.

## Grafana Selektoren-Einstellungen

Die Anwendung erfasst Panels von Grafana-Dashboards mithilfe von CSS-Selektoren, die je nach Grafana-Version unterschiedlich sein können. Im Einstellungsdialog unter "Grafana Selektoren" können diese Selektoren für verschiedene Grafana-Versionen konfiguriert werden.

### Wann sollten die Selektoren angepasst werden?

- Wenn eine neue Grafana-Version verwendet wird und die Panel-Erfassung nicht richtig funktioniert
- Wenn Custom panels eingesetzt werden, die mit Hilfe spezieller Selektoren gekennzeichnet sind und nicht die Standardselektoren verwenden

### Informationen zu Grafana e2e Selektoren

Grafana verwendet für seine Benutzeroberfläche das Attribut `data-testid` als Markierung für Elemente, die in End-to-End (e2e) Tests verwendet werden. Diese Selektoren sind relativ stabil zwischen verschiedenen Versionen, können sich aber bei größeren Updates ändern.

Beispielsweise funktionierende Selektoren wären:
- In Grafana 9.x: `data-testid Panel header` für den Panel-Header
- In Grafana 11.x: `data-testid panel content` für den Panel-Inhalt

Diese Selektoren werden als Beginn des Wertes im `data-testid` Attributs identifiziert, was bedeutet, wenn beispielsweise der Inhalt den kompletten Wert `data-testid Panel header ${title}` hat, also inklusive des individuellen und veränderlichen Panelbezeichners, so wird der Selektor trotzdem korrekt identifiziert.

Falls unklar sein sollte, welcher Selektor verwendet werden kann, einfach die Browser-Entwicklertools öffnen, während ein Grafana-Dashboard angezeigt wird, und nach Elementen mit dem Attribut `data-testid` suchen.

Eine aktuelle Übersicht der in Grafana verwendeten Selektoren (versioniert) findet sich hier:
https://github.com/grafana/grafana/tree/main/packages/grafana-e2e-selectors/src/selectors

### Konfiguration der Selektoren

1. Navigieren Sie zu "Einstellungen" → "Grafana Selektoren"
2. Klicken Sie auf "Selektor hinzufügen"
3. Geben Sie das Versionspräfix ein (z.B. "9." für alle Versionen, die mit 9 beginnen, man beachte den `.` (Punkt)!)
4. Geben Sie den entsprechenden Selektor ein (z.B. "header-container")
5. Klicken Sie auf "Speichern"

Es wird dann automatisch der passende Selektor basierend auf der erkannten Grafana-Version verwendet, ALLERDINGS wird nur ein reiner Textvergleich durchgeführt, d. h. beginnt die erkannte Grafana Version mit dem hinterlegte Versionspräfix, gilt der Selektor für alle zugehörigen Versionen.

## Docker Inbetriebnahme

### Voraussetzungen

- Docker und Docker Compose installiert
- Git zum Klonen des Repositories
- Grafana-Server mit API-Zugriff

### Umgebungsvariablen konfigurieren

1. Kopieren Sie die Beispieldatei als Grundlage für Ihre Konfiguration:

```bash
cp env-example .env
```

2. Öffnen Sie die `.env` Datei und passen Sie die folgenden Variablen entsprechend Ihrer Umgebung an:

Wichtige Hinweise:
- `SECRET_KEY` sollte für die Produktion in einen sicheren, zufällig generierten Wert geändert werden
- `TZ` definiert die Zeitzone für die Container
- `VITE_API_URL` sollte auf die URL Ihres API-Endpunkts verweisen, also normalerweise den Hostnamen - für lokale Entwicklung könnte dies `http://localhost:8000/api` sein
- `LOGLEVEL` kann je nach Bedarf auf `info`, `warning` oder `error` gesetzt werden
- `HTTP_PORT` und `HTTPS_PORT` definieren die Ports, unter denen die Anwendung extern erreichbar ist

### Container starten

Führen Sie den folgenden Befehl aus, um die Container zu bauen und zu starten:

```bash
docker-compose up -d
```

Nach erfolgreichem Start ist die Anwendung verfügbar unter:
- **HTTP**: http://localhost:80 (wird automatisch auf HTTPS umgeleitet)
- **HTTPS**: https://localhost:443

### Ersteinrichtung

1. Beim ersten Zugriff auf die Anwendung werden Sie aufgefordert, einen Administrator-Benutzer einzurichten.
2. Nach der Anmeldung konfigurieren Sie die Verbindung zu Ihrem Grafana-Server unter "Einstellungen".
3. Stellen Sie sicher, dass die Verbindung funktioniert, indem Sie auf "Verbindung testen" klicken.

## Aktualisieren der Anwendung

Um die Anwendung auf eine neue Version zu aktualisieren:

```bash
git pull
./cleanup-and-build.sh
docker-compose up -d
```

## Fehlersuche

### Logs einsehen

```bash
# Frontend-Logs
docker-compose logs frontend

# Backend-Logs
docker-compose logs backend

# NGINX-Logs
docker-compose logs nginx
```

### Bekannte Probleme

- Bei Verbindungsproblemen mit Grafana überprüfen Sie, ob die API-URL korrekt ist und der Benutzer über ausreichende Berechtigungen verfügt.
- Bei Problemen mit der E-Mail-Versendung überprüfen Sie die SMTP-Einstellungen und ob der SMTP-Server externe Verbindungen zulässt.

## Lizenz

[LICENSE](LICENSE) - Bitte beachten Sie die Lizenzbedingungen.