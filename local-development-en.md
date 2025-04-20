# Local Development Environment without Docker

This guide describes how to set up and run the Grafana PDF Reporter application locally without Docker. This approach is particularly useful for development purposes or when you want to run the application in an environment without Docker.

## Backend (Python/FastAPI)

### Prerequisites

- Python 3.9
- pip (Python Package Manager)
- Playwright with browser support
- A Grafana instance that can be accessed

### Installation

1. Navigate to the backend directory:
   ```bash
   cd grafana-pdf-reporter/backend
   ```

2. Create and activate a virtual Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright and the required browsers:
   ```bash
   playwright install-deps
   playwright install chromium
   ```
   
5. Create the necessary directories if they don't exist:
   ```bash
   mkdir -p templates layouts schedules config
   ```

### Configuration

1. Create a `.env` file in the backend directory with the following environment variables:
   ```
   LOGLEVEL=debug
   HOST=0.0.0.0
   PORT=8000
   TZ=Europe/Berlin
   SECRET_KEY='77oYKYadaKkYGsbvr6sWGRczQ1Xu8T6bGl4TW5kIfD8='
   ```

### Starting the Backend

1. Run the following command to start the backend:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. The backend is now available at `http://localhost:8000`. The API documentation can be viewed at `http://localhost:8000/api/docs`.

## Frontend (Vue.js)

### Prerequisites

- Node.js 16 or higher
- npm (Node Package Manager)

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd grafana-pdf-reporter/frontend
   ```

2. Install the required dependencies:
   ```bash
   npm install
   ```

### Configuration

1. Create or update the `public/env-config.js` file with the following content:
   ```javascript
   window.VITE_API_URL = "http://localhost:8000/api"
   ```

2. Alternatively, you can create a `.env.local` file:
   ```
   VITE_API_URL=http://localhost:8000/api
   ```

### Starting the Frontend

1. Run the following command to start the frontend in development mode:
   ```bash
   npm run dev
   ```

2. The frontend is now available at `http://localhost:8080`.

## Connecting to Grafana

For local development, the settings for connecting to your Grafana instance need to be configured manually:

1. Access the application and navigate to "Settings"
2. Enter the Grafana URL, username, and password
3. Test the connection with the "Test Connection" button

## Known Limitations in Local Development

1. **CORS Settings**: CORS issues might occur during local development. If necessary, enable CORS in your Grafana configuration or use a browser with disabled CORS restrictions for development purposes.

E.g. start Chrome with deactivated Web Security under Mac OS:

`open -n -a /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --args --user-data-dir="/tmp/chrome_dev_test" --disable-web-security`

2. **SSL/TLS**: The local development environment uses HTTP by default. If your Grafana instance requires HTTPS, you might need to make additional configurations.

3. **Schedules**: Report schedules only work when the backend is continuously running. In local development, scheduled reports may not execute as expected if the backend is restarted.

## Production Deployment without Docker

For a production deployment without Docker, you need to:

1. **Backend**: Set up the backend as a service, e.g., with systemd, supervisor, or a similar service manager.
   ```bash
   # Example for a systemd service file
   gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
   ```

2. **Frontend**: Build the frontend for production and deploy it with a web server like Nginx or Apache:
   ```bash
   # Build the frontend
   cd frontend
   npm run build
   
   # The generated files in the dist/ directory must then be copied to the web server
   ```

3. **Reverse Proxy**: Configure a reverse proxy like Nginx to provide the frontend and backend under a unified domain. You can adapt the configuration from the existing Nginx configuration in `nginx/conf/default.prod.conf`.

Note that this configuration requires further adjustments and security considerations for a complete production environment.

# API Usage with curl

To interact with the backend through the REST API, you need to obtain an authentication token. Here's an example of how to get a bearer token and query the API using `curl`:

> **Note**: If you've started the application with the existing `docker-compose.yml` file, the following approach won't work because port 8000 of the backend container is not exposed externally. For direct API access, you would need to modify the `docker-compose.yml` to expose the port:
> ```yaml
> services:
>   backend:
>     # ... other settings ...
>     ports:
>       - "8000:8000"  # Add this line
> ```
> Alternatively, remove the `:8000` part from the following `curl` commands.

### Obtaining an Authentication Token

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -d "username=admin&password=admin123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

The response should be a JSON object containing an access token, like this:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Calling API Endpoints with the Token

Use the obtained token to access protected API endpoints. Here's an example to retrieve all organizations:

```bash
curl -X GET http://localhost:8000/api/organizations \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

The response should be a list of available Grafana organizations:

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

You can use this authentication pattern for all API endpoints listed in the API documentation at `http://localhost:8000/api/docs`.
