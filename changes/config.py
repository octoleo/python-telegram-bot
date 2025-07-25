# noqa: INP001
# pylint: disable=import-error
"""Configuration for the chango changelog tool"""

import re
from collections.abc import Collection
from pathlib import Path
from typing import Optional

from chango import Version
from chango.concrete import DirectoryChanGo, DirectoryVersionScanner, HeaderVersionHistory
from chango.concrete.sections import GitHubSectionChangeNote, Section, SectionVersionNote

version_scanner = DirectoryVersionScanner(base_directory=".", unreleased_directory="unreleased")


class ChangoSectionChangeNote(
    GitHubSectionChangeNote.with_sections(  # type: ignore[misc]
        [
            Section(uid="highlights", title="Highlights", sort_order=0),
            Section(uid="breaking", title="Breaking Changes", sort_order=1),
            Section(uid="security", title="Security Changes", sort_order=2),
            Section(uid="deprecations", title="Deprecations", sort_order=3),
            Section(uid="features", title="New Features", sort_order=4),
            Section(uid="bugfixes", title="Bug Fixes", sort_order=5),
            Section(uid="dependencies", title="Dependencies", sort_order=6),
            Section(uid="other", title="Other Changes", sort_order=7),
            Section(uid="documentation", title="Documentation", sort_order=8),
            Section(uid="internal", title="Internal Changes", sort_order=9),
        ]
    )
):
    """Custom change note type for PTB. Mainly overrides get_sections to map labels to sections"""

    OWNER = "python-telegram-bot"
    REPOSITORY = "python-telegram-bot"

    @classmethod
    def get_sections(
        cls,
        labels: Collection[str],
        issue_types: Optional[Collection[str]],
    ) -> set[str]:
        """Override get_sections to have customized auto-detection of relevant sections based on
        the pull request and linked issues. Certainly not perfect in all cases, but should be a
        good start for most PRs.
        """
        combined_labels = set(labels) | (set(issue_types or []))

        mapping = {
            "🐛 bug": "bugfixes",
            "💡 feature": "features",
            "🧹 chore": "internal",
            "⚙️ bot-api": "features",
            "⚙️ documentation": "documentation",
            "⚙️ tests": "internal",
            "⚙️ ci-cd": "internal",
            "⚙️ security": "security",
            "⚙️ examples": "documentation",
            "⚙️ type-hinting": "other",
            "🛠 refactor": "internal",
            "🛠 breaking": "breaking",
            "⚙️ dependencies": "dependencies",
            "🔗 github-actions": "internal",
            "🛠 code-quality": "internal",
        }

        # we want to return *all* from the mapping that are in the combined_labels
        # removing superfluous sections from the fragment is a tad easier than adding them
        found = {section for label, section in mapping.items() if label in combined_labels}

        # if we have not found any sections, we default to "other"
        return found or {"other"}


class CustomChango(DirectoryChanGo):
    """Custom ChanGo class for overriding release"""

    def release(self, version: Version) -> bool:
        """replace "14.5" with version.uid except in the contrib guide
        then call super
        """
        root = Path(__file__).parent.parent / "src"
        python_files = root.rglob("*.py")
        pattern = re.compile(r"NEXT\.VERSION")
        excluded_paths = {root / "docs/source/contribute.rst"}
        for file_path in python_files:
            if str(file_path) in excluded_paths:
                continue

            content = file_path.read_text(encoding="utf-8")
            modified = pattern.sub(version.uid, content)

            if content != modified:
                file_path.write_text(modified, encoding="utf-8")

        return super().release(version)


chango_instance = CustomChango(
    change_note_type=ChangoSectionChangeNote,
    version_note_type=SectionVersionNote,
    version_history_type=HeaderVersionHistory,
    scanner=version_scanner,
)
