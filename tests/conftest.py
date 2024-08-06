from pathlib import Path

PATCH_DIR = Path(__file__).parent / "patches"
TEST_PATCHES = list(PATCH_DIR.glob("*.spn"))
assert TEST_PATCHES, "No test patches found in the patches directory."
