#!/usr/bin/env python3
"""
update_secrets.py
=================
One-click secret generator + updater for your Local AI Stack.

Run anytime you want fresh keys:
    python update_secrets.py
"""

import secrets
import string
import shutil
import re
from pathlib import Path

# ====================== CONFIG ======================
ROOT = Path(__file__).parent.resolve()

FILES_TO_UPDATE = {
    "WEBUI_SECRET_KEY":         (ROOT / "docker-compose.yml",          False),
    "SEARXNG_SECRET_KEY":       (ROOT / "docker-compose.yml",          False),
    "N8N_BASIC_AUTH_PASSWORD":  (ROOT / "compose/automation.yml",      False),
    "FLOWISE_PASSWORD":         (ROOT / "compose/automation.yml",      False),
    "NEXTAUTH_SECRET":          (ROOT / "compose/automation.yml",      False),
    "AUTH_SECRET":              (ROOT / "compose/ui-extras.yml",       False),
    "NEXT_AUTH_SECRET":         (ROOT / "compose/ui-extras.yml",       False),
    "JWT_SECRET":               (ROOT / "compose/ui-extras.yml",       False),
    "LANGFUSE_SECRET_KEY":      (ROOT / "compose/guardrails.yml",      False),   # skipped if file missing
    "secret_key":               (ROOT / "config/searxng/settings.yml", True),    # YAML style
}

# ====================== GENERATE KEYS ======================
def generate_hex(length: int = 32) -> str:
    return secrets.token_hex(length)

def generate_alphanum(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

keys = {
    "WEBUI_SECRET_KEY":        generate_hex(32),
    "SEARXNG_SECRET_KEY":      generate_hex(32),
    "N8N_BASIC_AUTH_PASSWORD": generate_alphanum(32),
    "FLOWISE_PASSWORD":        generate_alphanum(32),
    "NEXTAUTH_SECRET":         generate_hex(64),
    "AUTH_SECRET":             generate_hex(64),
    "JWT_SECRET":              generate_hex(64),
    "LANGFUSE_SECRET_KEY":     generate_hex(64),
}

# ====================== PRINT & CONFIRM ======================
print("\n=== GENERATED SECRETS ===")
for name, value in keys.items():
    print(f"{name}={value}")

confirm = input("\nApply these secrets to all .yml files? (type Y to continue): ").strip().upper()
if confirm != "Y":
    print("Cancelled.")
    exit()

# ====================== UPDATE FILES ======================
def update_file(file_path: Path, key_name: str, new_value: str, is_yaml: bool):
    if not file_path.exists():
        return

    # Backup
    backup = file_path.with_suffix(file_path.suffix + ".bak")
    shutil.copy2(file_path, backup)
    print(f"→ Backed up: {backup.name}")

    content = file_path.read_text(encoding="utf-8")

    if is_yaml:
        # Matches:   secret_key: oldvalue   or   secret_key: "oldvalue"
        pattern = rf"^(\s*{key_name}\s*:\s*[\"']?).*?([\"']?\s*(?:#.*)?)$"
        replacement = rf"\1{new_value}\2"
    else:
        # Matches:   KEY=oldvalue
        pattern = rf"^({key_name}=).*"
        replacement = rf"\1{new_value}"

    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    file_path.write_text(content, encoding="utf-8")
    print(f"✅ Updated: {file_path.name}")

print("\nUpdating files...")
for key_name, (file_path, is_yaml) in FILES_TO_UPDATE.items():
    update_file(file_path, key_name, keys.get(key_name, ""), is_yaml)

print("\n🎉 All secrets updated successfully!")
print("Backups created (.bak files).")
print("\nRestart your stack with:")
print("   docker compose down && docker compose up -d")