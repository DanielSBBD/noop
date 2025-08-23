#!/bin/bash
set -e

ORIG_DIR=$(pwd)
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

pip install -r requirements.txt -t "$TEMP_DIR"
cp lambda_function.py "$TEMP_DIR"
cd "$TEMP_DIR"
zip -r "$ORIG_DIR/lambda-package.zip" .