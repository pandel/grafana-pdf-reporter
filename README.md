# Grafana PDF Reporter

## Overview

Grafana PDF Reporter is a web application for creating and managing PDF reports from Grafana dashboards. The application allows you to select panels from Grafana dashboards, arrange them in customizable layouts, format them with custom templates, and export them as PDF reports. Additionally, you can schedule recurring report jobs and send them via email.

IMPORTANT: you don't need the `grafana-image-renderer` Plugin and no Grafana enterprise license!

Introduction video: https://www.youtube.com/watch?v=X6ssfjGbemc

### Technologies Used for Development

The application was created entirely in interaction with Anthropic Claude 3.7 Sonnet. Therefore, it is quite possible that some seasoned developers might notice code sequences that could have been designed, implemented, or optimized differently. However, I am satisfied with the fact that it was possible to develop this application within an acceptable timeframe with the help of AI, following the motto: if it works, it works!

## Key Features

- **Report Designer**: Create reports by selecting and arranging panels from Grafana dashboards
- **Layouts**: Save and reuse report layouts
- **Templates**: Customizable headers, footers, and page formatting for consistent appearance
- **Schedules**: Automated report creation and distribution on a schedule
- **Multilingual**: Support for German and English
- **Themes**: Light and dark appearance

## Technology Stack

- **Frontend**: Vue.js 3, Vuetify, Axios, Pinia, mitt
- **Backend**: Python, FastAPI, Playwright
- **Database Integration**: Grafana API
- **Containers**: Docker, Nginx
- **Security**: JWT Authentication, HTTPS

## Preparatory Work for NGINX

### Generate SSL Certificates

For production operation, HTTPS with SSL certificates is required. You can create self-signed certificates using the provided script:

```bash
./generate-ssl-cert.sh
```

This script creates the files `cert.pem` and `key.pem` in the `nginx/ssl/` directory.

### Generate Diffie-Hellman Parameters

For additional security in SSL connections, Diffie-Hellman parameters are needed:

```bash
./generate-dhparam.sh
```

This script creates the file `dhparam.pem` in the `nginx/ssl/` directory.

### Generate Secret Key

To generate a secure random secret key for use in the `.env` file, run:

```bash
docker run --rm -t grafana-pdf-reporter-v3/backend:1.1.1 python /app/generate_secret_key.py
```

### Customize NGINX Configuration

The default NGINX configuration is suitable for most use cases. If needed, you can modify the following files:

- `nginx/conf/default.prod.conf`: Main NGINX configuration
- `nginx/security/security.conf`: Security settings for HTTPS

If you want to use a custom domain name explicitely, adjust the `server_name` directive in `default.prod.conf`.

## Grafana Selectors Settings

The application captures panels from Grafana dashboards using CSS selectors that may vary depending on the Grafana version. In the settings dialog under "Grafana Selectors," you can configure these selectors for different Grafana versions.

### When to adjust the selectors?

- When using a new Grafana version and panel capture doesn't work correctly
- When you are using custom designed panels which don't use the standard selectors

### Information about Grafana e2e selectors

Grafana uses the `data-testid` attribute as a marker for elements used in End-to-End (e2e) tests. These selectors are relatively stable between different versions but may change with major updates.

Working selectors are e.g.:
- In Grafana 9.x: `header-container` for the panel header
- In Grafana 11.x: `data-testid panel content` for the panel content

These selectors are identified as the beginning of the value in the data-testid attribute, which means that if, for example, the content has the complete value data-testid Panel header ${title}, including the individual and variable panel identifier, the selector will still be correctly identified.

If you're unsure which selector to use, you can open the browser developer tools while viewing a Grafana dashboard and search for elements with the `data-testid` attribute.

You can find a current overview about (versioned) Grafana selectors here:
https://github.com/grafana/grafana/tree/main/packages/grafana-e2e-selectors/src/selectors

### Configuring selectors

1. Navigate to "Settings" → "Grafana Selectors"
2. Click on "Add Selector"
3. Enter the version prefix (e.g., "9." for all versions starting with 9, mind the `.` (dot)!)
4. Enter the corresponding selector (e.g., "header-container")
5. Click "Save"

The application will then automatically use the appropriate selector based on the detected Grafana version, BUT it will only make a simple string comparison, that means, if the Grafana version of your server starts with the given version prefix, it will use the assigned selector for all versions like this.

## Docker Deployment

### Prerequisites

- Docker and Docker Compose installed
- Git for cloning the repository
- Grafana server with API access

### Configure Environment Variables

1. Copy the example file as a basis for your configuration:

```bash
cp env-example .env
```

2. Open the `.env` file and adjust the following variables according to your environment:

Important notes:
- `SECRET_KEY` should be changed to a secure, randomly generated value for production
- `TZ` defines the timezone for the containers
- `VITE_API_URL` should point to the URL of your API endpoint, typically the hostname - for local development, this could be `http://localhost:8000/api`
- `LOGLEVEL` can be set to `info`, `warning`, or `error` as needed
- `HTTP_PORT` and `HTTPS_PORT` define the ports on which the application will be externally accessible

### Start Containers

Run the following command to build and start the containers:

```bash
docker-compose up -d
```

After successful startup, the application is available at:
- **HTTP**: http://localhost:80 (automatically redirected to HTTPS)
- **HTTPS**: https://localhost:443

### Initial Setup

1. On first access, you will be prompted to set up an administrator user.
2. After logging in, configure the connection to your Grafana server under "Settings".
3. Ensure the connection works by clicking "Test Connection".

## Updating the Application

To update the application to a new version:

```bash
git pull
./cleanup-and-build.sh
docker-compose up -d
```

## Troubleshooting

### View Logs

```bash
# Frontend logs
docker-compose logs frontend

# Backend logs
docker-compose logs backend

# NGINX logs
docker-compose logs nginx
```

### Known Issues

- For connection problems with Grafana, verify that the API URL is correct and the user has sufficient permissions.
- For issues with email sending, check the SMTP settings and whether the SMTP server allows external connections.

## License

[LICENSE](LICENSE) - Please observe the licensing terms.