#!/bin/bash
# Script to generate Diffie-Hellman parameters for enhanced SSL security

# Create directories if they don't exist
mkdir -p ./nginx/ssl

# Generate the dhparam file (this may take a few minutes)
echo "Generating Diffie-Hellman parameters (2048 bit). This may take several minutes..."
openssl dhparam -out ./nginx/ssl/dhparam.pem 2048

# Set appropriate permissions
chmod 644 ./nginx/ssl/dhparam.pem

echo "Diffie-Hellman parameters generated successfully."
echo "Location: ./nginx/ssl/dhparam.pem"
