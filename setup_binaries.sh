#!/bin/bash

# Make the binaries executable
chmod +x wkhtmltopdf_bin/usr/local/bin/wkhtmltopdf
chmod +x wkhtmltopdf_bin/usr/local/bin/wkhtmltoimage

# Add the binaries to PATH
export PATH=$PATH:$(pwd)/wkhtmltopdf_bin/usr/local/bin

# Verify installation
wkhtmltopdf --version
wkhtmltoimage --version
