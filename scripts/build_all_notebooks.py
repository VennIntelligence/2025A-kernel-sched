#!/usr/bin/env python3
"""构建所有 notebooks（Git 迁移后首选）。

用法:
    uv run python scripts/build_all_notebooks.py
    uv run python scripts/build_all_notebooks.py --execute
"""

import re
import subprocess
import sys
from pathlib import Path


def find_notebook_dirs(notebooks_root: Path) -> list[Path]:
    """Find all notebook directories (contain fragments/ or NN_*.py files)."""
    dirs = []
    for d in sorted(notebooks_root.iterdir()):
        if not d.is_dir():
            continue
        fragments = d / "fragments"
        if fragments.is_dir():
            dirs.append(d)
        elif any(f for f in d.glob("*.py") if re.match(r"^\d+_", f.name)):
            dirs.append(d)
    return dirs


def main():
    do_execute = "--execute" in sys.argv

    # Find project root
    root = Path(__file__).resolve().parent.parent
    notebooks_root = root / "notebooks"
    if not notebooks_root.is_dir():
        print("❌ notebooks/ 目录不存在")
        sys.exit(1)

    dirs = find_notebook_dirs(notebooks_root)
    if not dirs:
        print("❌ 没有找到 notebook 目录")
        sys.exit(1)

    print(f"📚 找到 {len(dirs)} 个 notebook 目录\n")

    failed = []
    for d in dirs:
        print(f"\n{'='*60}")
        print(f"📓 构建: {d.relative_to(root)}")
        print(f"{'='*60}")

        cmd = [sys.executable, str(root / "scripts" / "build_notebook.py"), str(d)]
        if do_execute:
            cmd.append("--execute")

        result = subprocess.run(cmd, cwd=str(root))
        if result.returncode != 0:
            failed.append(d.name)

    print(f"\n{'='*60}")
    if failed:
        print(f"⚠️ {len(failed)} 个 notebook 构建失败: {', '.join(failed)}")
        sys.exit(1)
    else:
        print(f"✅ 全部 {len(dirs)} 个 notebook 构建成功")


if __name__ == "__main__":
    main()
