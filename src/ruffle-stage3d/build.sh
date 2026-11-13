#!/bin/sh
# Recompile Ruffle 0.7.1 avec le cache des pipelines Stage3D, vers assets/ruffle-stage3d/.
# Prérequis : git, Rust (cible wasm32-unknown-unknown), wasm-bindgen-cli 0.2.127, Node 22 + npm.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
W=${BUILD:-/tmp/kt-ruffle}
[ -d "$W/.git" ] || git clone -q --depth 1 --branch v0.7.1 https://github.com/ruffle-rs/ruffle.git "$W"
cd "$W"
git checkout -q -- . && git apply "$HERE"/0001-*.patch
cd web
npm ci --no-audit --no-fund
npm run build --workspace=ruffle-core
npm run build --workspace=ruffle-selfhosted
rm -rf "$ROOT/assets/ruffle-stage3d" && mkdir -p "$ROOT/assets/ruffle-stage3d"
cp packages/selfhosted/dist/* "$ROOT/assets/ruffle-stage3d/"
rm -f "$ROOT/assets/ruffle-stage3d/"*.map
echo "OK : assets/ruffle-stage3d/"
