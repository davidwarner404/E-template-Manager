#!/bin/bash

# Update package list
sudo apt-get update

# Install wkhtmltopdf (this includes wkhtmltoimage)
sudo apt-get install -y wkhtmltopdf

# Optional: Verify installation
wkhtmltoimage --version
