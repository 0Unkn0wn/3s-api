#!/bin/sh

# Read secrets and export them as environment variables
export DB_URL=$(cat /run/secrets/DB_URL)
export DB_USER=$(cat /run/secrets/DB_USER)
export DB_PASSWORD=$(cat /run/secrets/DB_PASSWORD)

# Execute the passed command
exec "$@"
