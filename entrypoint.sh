#!/bin/sh

# Create a file to store the secrets
SECRETS_FILE=/app/.env

# Check if secrets are available and write them to the file
if [ -f /run/secrets/DB_URL ]; then
  echo "DB_URL=$(cat /run/secrets/DB_URL)" >> $SECRETS_FILE
fi
if [ -f /run/secrets/DB_USER ]; then
  echo "DB_USER=$(cat /run/secrets/DB_USER)" >> $SECRETS_FILE
fi
if [ -f /run/secrets/DB_PASSWORD ]; then
  echo "DB_PASSWORD=$(cat /run/secrets/DB_PASSWORD)" >> $SECRETS_FILE
fi

# Export the variables from the secrets file
export $(grep -v '^#' $SECRETS_FILE | xargs)

# Execute the passed command
exec "$@"
