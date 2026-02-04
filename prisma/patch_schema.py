"""
Post-pull patch for prisma/schema.prisma.

Prisma's `db pull` strips @ignore on relation fields pointing to @@ignore models.
This script adds them back automatically.

Usage:
    prisma db pull && python prisma/patch_schema.py
"""

import re
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.prisma"


def main():
    content = SCHEMA_PATH.read_text()
    lines = content.splitlines()

    # Pass 1: collect all models marked with @@ignore
    ignored_models: set[str] = set()
    current_model: str | None = None
    for line in lines:
        m = re.match(r"^model\s+(\w+)\s*\{", line)
        if m:
            current_model = m.group(1)
        if "@@ignore" in line and current_model:
            ignored_models.add(current_model)
        if line.strip() == "}":
            current_model = None

    print(f"Ignored models ({len(ignored_models)}): {sorted(ignored_models)}")

    # Pass 2: add @ignore to relations pointing to ignored models
    patched_lines: list[str] = []
    current_model = None
    current_is_ignored = False
    changes = 0

    for line in lines:
        m = re.match(r"^model\s+(\w+)\s*\{", line)
        if m:
            current_model = m.group(1)
            current_is_ignored = current_model in ignored_models
        if line.strip() == "}":
            current_model = None
            current_is_ignored = False

        # Only patch inside non-ignored models
        if current_model and not current_is_ignored and "@ignore" not in line:
            # Match:  fieldName   TypeName[?[]]   @relation(...)
            rel = re.match(r"^(\s+\S+\s+)(\w+)([\?\[\]]*\s+@relation\(.+)$", line)
            if rel:
                target_model = rel.group(2)
                if target_model in ignored_models:
                    line = line.rstrip() + " @ignore"
                    field_name = line.strip().split()[0]
                    print(f"  Added @ignore: {current_model}.{field_name} -> {target_model}")
                    changes += 1

        patched_lines.append(line)

    if changes:
        SCHEMA_PATH.write_text("\n".join(patched_lines))
        print(f"\nPatched {changes} relation(s). Schema updated.")
    else:
        print("\nNo patches needed.")


if __name__ == "__main__":
    main()
