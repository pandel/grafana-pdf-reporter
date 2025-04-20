#!/bin/bash
# Script to generate self-signed SSL certificates for development/testing purposes

# Create directories if they don't exist
mkdir -p ./nginx/ssl

# Generate a self-signed SSL certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./nginx/ssl/key.pem \
  -out ./nginx/ssl/cert.pem \
  -subj "/C=DE/ST=State/L=City/O=Organization/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

# Set appropriate permissions
chmod 600 ./nginx/ssl/key.pem
chmod 644 ./nginx/ssl/cert.pem

echo "Self-signed SSL certificates generated successfully."
echo "Location: ./nginx/ssl/"