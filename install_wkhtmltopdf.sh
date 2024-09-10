#!/bin/bash

# Update package list
apt-get update

# Install wkhtmltopdf (this includes wkhtmltoimage)
apt-get install -y wkhtmltopdf

# Optional: Verify installation
wkhtmltoimage --version
