from __future__ import annotations

import importlib.util
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

SPEC = importlib.util.spec_from_file_location(
    "index_local_evidence", TOOLS_DIR / "index_local_evidence.py"
)
assert SPEC and SPEC.loader
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)


class LocalEvidenceIndexTests(unittest.TestCase):
    def make_tree(self, root: Path) -> None:
        nested = root / "nested"
        nested.mkdir(parents=True)
        (root / "record.json").write_text('{"result": 1}\n')
        (nested / "trajectory.json").write_text('{"steps": []}\n')
        (root / "record.json").chmod(0o600)
        nested.chmod(0o700)
        root.chmod(0o700)

    def test_identical_copy_has_identical_mode_aware_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            copy = base / "copy"
            self.make_tree(source)
            shutil.copytree(source, copy, copy_function=shutil.copy2)
            source_index = INDEXER.index_root("source", source)
            copy_index = INDEXER.index_root("copy", copy)
            self.assertEqual(
                source_index["tree_sha256"],
                copy_index["tree_sha256"],
            )

    def test_content_and_mode_changes_change_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "evidence"
            self.make_tree(root)
            original = INDEXER.index_root("evidence", root)["tree_sha256"]
            (root / "record.json").write_text('{"result": 2}\n')
            content_changed = INDEXER.index_root("evidence", root)["tree_sha256"]
            self.assertNotEqual(original, content_changed)
            (root / "record.json").write_text('{"result": 1}\n')
            (root / "record.json").chmod(0o640)
            mode_changed = INDEXER.index_root("evidence", root)["tree_sha256"]
            self.assertNotEqual(original, mode_changed)

    def test_symlink_target_is_indexed_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "evidence"
            external = base / "external"
            root.mkdir()
            external.write_text("outside\n")
            (root / "external-link").symlink_to(external)
            indexed = INDEXER.index_root("evidence", root)
            symlink = next(
                record for record in indexed["entries"] if record["type"] == "symlink"
            )
            self.assertEqual(symlink["target"], str(external))
            self.assertTrue(stat.S_ISLNK((root / "external-link").lstat().st_mode))


if __name__ == "__main__":
    unittest.main()
