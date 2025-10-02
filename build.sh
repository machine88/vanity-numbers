#!/usr/bin/env bash
set -euo pipefail

# ========= Paths =========
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$ROOT_DIR/infra/build"
SITE_DIR="$BUILD_DIR/site"

VANITY_DIR="$ROOT_DIR/lambda/vanity"
API_DIR="$ROOT_DIR/lambda/api"
WEB_DIR="$ROOT_DIR/web"

TMP_VANITY="$ROOT_DIR/.tmp_vanity_pkg"
TMP_API="$ROOT_DIR/.tmp_api_pkg"

# ========= Helpers =========
msg(){ echo -e "\033[1;36m[build]\033[0m $*"; }
die(){ echo -e "\033[1;31m[build:ERROR]\033[0m $*" >&2; exit 1; }

# ========= Sanity =========
[[ -d "$VANITY_DIR" ]] || die "Missing $VANITY_DIR"
[[ -f "$VANITY_DIR/handler.py" ]] || die "Missing $VANITY_DIR/handler.py"
[[ -f "$VANITY_DIR/requirements.txt" ]] || die "Missing $VANITY_DIR/requirements.txt"

BUILD_API=false
if [[ -d "$API_DIR" && -f "$API_DIR/api_handler.py" && -f "$API_DIR/requirements.txt" ]]; then
  BUILD_API=true
fi

BUILD_WEB=false
if [[ -d "$WEB_DIR" && -f "$WEB_DIR/index.html" && -f "$WEB_DIR/app.js" ]]; then
  BUILD_WEB=true
fi

# ========= Clean =========
msg "Preparing build folders..."
rm -rf "$BUILD_DIR" "$TMP_VANITY" "$TMP_API"
mkdir -p "$BUILD_DIR" "$SITE_DIR" "$TMP_VANITY"
[[ "$BUILD_API" == true ]] && mkdir -p "$TMP_API"

# ========= Vanity Lambda (as package app/...) =========
msg "Building vanity Lambda package..."
python3 -m pip install -q -r "$VANITY_DIR/requirements.txt" -t "$TMP_VANITY"

# Create package folder inside the deployment root
mkdir -p "$TMP_VANITY/app"
: > "$TMP_VANITY/app/__init__.py"

# Copy your code into app/ (exclude tests, caches)
rsync -a \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'tests' \
  "$VANITY_DIR/" "$TMP_VANITY/app/"

# Show what will be zipped (debug)
msg "Vanity package staging contents:"
( cd "$TMP_VANITY" && find app -maxdepth 2 -print | sort )

# Zip it
( cd "$TMP_VANITY" && zip -qr "$BUILD_DIR/lambda_vanity.zip" . )

# Verify (use zipinfo -1 for reliable single-column output)
if unzip -Z1 "$BUILD_DIR/lambda_vanity.zip" | awk 'BEGIN{f=0} $0=="app/handler.py"{f=1} END{exit (f?0:1)}'; then
  msg "✓ vanity zip -> $BUILD_DIR/lambda_vanity.zip"
else
  msg "ZIP listing:"
  unzip -Z1 "$BUILD_DIR/lambda_vanity.zip" | sed -n '1,200p'
  die "app/handler.py NOT found in ZIP — packaging failed"
fi
msg "✓ vanity zip -> $BUILD_DIR/lambda_vanity.zip"

# ========= API Lambda (optional) =========
if [[ "$BUILD_API" == true ]]; then
  msg "Building API Lambda package..."
  python3 -m pip install -q -r "$API_DIR/requirements.txt" -t "$TMP_API"
  rsync -a --exclude '__pycache__' --exclude '*.pyc' "$API_DIR/" "$TMP_API/"
  ( cd "$TMP_API" && zip -qr "$BUILD_DIR/lambda_api.zip" . )
  msg "✓ API zip -> $BUILD_DIR/lambda_api.zip"
fi

# ========= Web (optional) =========
if [[ "$BUILD_WEB" == true ]]; then
  msg "Staging web assets..."
  cp -f "$WEB_DIR/index.html" "$SITE_DIR/index.html"
  cp -f "$WEB_DIR/app.js"     "$SITE_DIR/app.js"
  msg "✓ site/ -> $SITE_DIR"
fi

# ========= Summary =========
cat <<EOF

========================================
 Build complete
========================================
Vanity Lambda zip : $BUILD_DIR/lambda_vanity.zip
$([[ "$BUILD_API" == true ]] && echo "API Lambda zip    : $BUILD_DIR/lambda_api.zip")
$([[ "$BUILD_WEB" == true ]] && echo "Web site files    : $SITE_DIR/index.html, app.js")

IMPORTANT:
  • In Terraform for the vanity function set: handler = "app.handler"
    (because the code is now inside the app/ package in the ZIP)

Next:
  1) cd infra/terraform
  2) terraform apply -var="connect_instance_id=09ce49c9-edf5-4751-abb6-12b6447d34cc"
EOF