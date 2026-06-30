import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def before_all(context):
    # Create a local symlink tree so ansible-playbook finds stefanfluit.kirby
    # without requiring an installed collection. Works for both local dev
    # and CI when the collection hasn't been published yet.
    collections_path = Path("/tmp/kirby-bdd-collections")
    link = collections_path / "ansible_collections" / "stefanfluit" / "kirby"
    link.parent.mkdir(parents=True, exist_ok=True)
    if not link.exists():
        link.symlink_to(PROJECT_ROOT)
    os.environ["ANSIBLE_COLLECTIONS_PATH"] = str(collections_path)

    os.chdir("tests/features/testdata/")
