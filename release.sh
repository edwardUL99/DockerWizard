#!/usr/bin/env bash

# Packages the release zip and tar files
VERSION="$1"

ARGS="bin dockerwizard example LICENSE README.md requirements.txt setup.py main.py"

TAR="tar -czf docker-wizard-$VERSION.tar.gz $ARGS"
ZIP="zip -r docker-wizard-$VERSION.zip $ARGS"

$TAR
$ZIP