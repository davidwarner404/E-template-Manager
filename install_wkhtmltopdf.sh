#!/bin/bash

# Create a directory for wkhtmltopdf/wkhtmltoimage binaries
mkdir -p wkhtmltopdf_bin

# Download the precompiled wkhtmltox binary (use the correct URL for the version)
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-3/wkhtmltox-0.12.6-3.archlinux-x86_64.pkg.tar.xz

# Extract the tar.xz file
tar -xJf wkhtmltopdf_bin/wkhtmltox.tar.xz -C wkhtmltopdf_bin --strip-components=1

# Make the wkhtmltopdf and wkhtmltoimage binaries executable
chmod +x wkhtmltopdf_bin/bin/wkhtmltopdf
chmod +x wkhtmltopdf_bin/bin/wkhtmltoimage

# Add the wkhtmltopdf and wkhtmltoimage binaries to the PATH
export PATH=$PATH:$(pwd)/wkhtmltopdf_bin/bin

# Print version to verify installation
wkhtmltoimage --version
