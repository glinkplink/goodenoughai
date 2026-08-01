#!/bin/sh
# Phase 1-only, checksum-pinned Ollama runtime upgrade with recoverable rollback.

set -eu

EXPECTED_HOST="TheImp"
VERSION="0.32.5"
ARCHIVE="/tmp/goodenough-ollama-linux-amd64-v0.32.5.tar.zst"
STAGE="/tmp/goodenough-ollama-v0.32.5-staged"
EXPECTED_ARCHIVE_SHA256="f7d6bdbcf71b83aa8670c4e7dc4b6936c0952fcf8b114eaf6a11cbadb9684214"
EXPECTED_UNIT_SHA256="11758d469d3f103e53a9612a8ffcb3a3e61834c994c08d412bb051f3c827dbd3"
EXPECTED_OVERRIDE_SHA256="d30d58cf12bef230f581111197653c4a5d58d655beba93877027040f331f8922"
OLD_BIN="/usr/local/bin/ollama"
OLD_LIB="/usr/local/lib/ollama"
BIN_BACKUP="/usr/local/bin/ollama-0.17.4-backup"
LIB_BACKUP="/usr/local/lib/ollama-0.17.4-backup"
FAILED_BIN="/tmp/goodenough-ollama-v0.32.5-failed-bin"
FAILED_LIB="/tmp/goodenough-ollama-v0.32.5-failed-lib"
UNIT="/etc/systemd/system/ollama.service"
OVERRIDE="/etc/systemd/system/ollama.service.d/override.conf"
MODEL_DIR="/usr/share/ollama/.ollama/models"
MOVED_OLD=0

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

rollback() {
    status=$?
    trap - EXIT INT TERM HUP
    if [ "$status" -ne 0 ] && [ "$MOVED_OLD" -eq 1 ]; then
        echo "Upgrade failed; restoring Ollama 0.17.4 runtime." >&2
        systemctl stop ollama 2>/dev/null || true
        if [ -e "$OLD_BIN" ] && [ ! -e "$FAILED_BIN" ]; then
            mv "$OLD_BIN" "$FAILED_BIN"
        fi
        if [ -e "$OLD_LIB" ] && [ ! -e "$FAILED_LIB" ]; then
            mv "$OLD_LIB" "$FAILED_LIB"
        fi
        if [ -e "$BIN_BACKUP" ]; then
            mv "$BIN_BACKUP" "$OLD_BIN"
        fi
        if [ -e "$LIB_BACKUP" ]; then
            mv "$LIB_BACKUP" "$OLD_LIB"
        fi
        systemctl start ollama 2>/dev/null || true
    fi
    exit "$status"
}

trap rollback EXIT INT TERM HUP

[ "$(id -u)" -eq 0 ] || fail "must run as root"
[ "$(hostname)" = "$EXPECTED_HOST" ] || fail "expected hostname $EXPECTED_HOST"
[ -f "$ARCHIVE" ] || fail "missing verified archive $ARCHIVE"
[ -x "$STAGE/bin/ollama" ] || fail "missing staged Ollama binary"
[ -d "$STAGE/lib/ollama" ] || fail "missing staged Ollama libraries"
[ -d "$MODEL_DIR" ] || fail "configured model directory is missing"
[ ! -e "$BIN_BACKUP" ] || fail "binary backup path already exists"
[ ! -e "$LIB_BACKUP" ] || fail "library backup path already exists"
[ ! -e "$FAILED_BIN" ] || fail "failed-binary holding path already exists"
[ ! -e "$FAILED_LIB" ] || fail "failed-library holding path already exists"

archive_sha256=$(sha256sum "$ARCHIVE" | awk '{print $1}')
[ "$archive_sha256" = "$EXPECTED_ARCHIVE_SHA256" ] || fail "archive checksum mismatch"
unit_sha256=$(sha256sum "$UNIT" | awk '{print $1}')
[ "$unit_sha256" = "$EXPECTED_UNIT_SHA256" ] || fail "systemd unit changed since pre-capture"
override_sha256=$(sha256sum "$OVERRIDE" | awk '{print $1}')
[ "$override_sha256" = "$EXPECTED_OVERRIDE_SHA256" ] || fail "systemd override changed since pre-capture"

systemctl stop ollama
mv "$OLD_BIN" "$BIN_BACKUP"
mv "$OLD_LIB" "$LIB_BACKUP"
MOVED_OLD=1
install -o root -g root -m 755 "$STAGE/bin/ollama" "$OLD_BIN"
cp -a "$STAGE/lib/ollama" "$OLD_LIB"
chown -R root:root "$OLD_LIB"

[ "$(sha256sum "$UNIT" | awk '{print $1}')" = "$EXPECTED_UNIT_SHA256" ] || fail "systemd unit was modified"
[ "$(sha256sum "$OVERRIDE" | awk '{print $1}')" = "$EXPECTED_OVERRIDE_SHA256" ] || fail "systemd override was modified"
systemctl start ollama
systemctl is-active --quiet ollama || fail "Ollama service did not become active"

MOVED_OLD=0
trap - EXIT INT TERM HUP
echo "Installed Ollama $VERSION; preserved 0.17.4 runtime backups and systemd configuration."
