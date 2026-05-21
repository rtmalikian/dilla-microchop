from __future__ import annotations

import sys
import types
import unittest

# microchop_sampler imports optional audio dependencies at module import time.
# These tests target pure path handling, so stub the unavailable dependencies.
for name in ("librosa", "mido", "soundfile"):
    sys.modules.setdefault(name, types.ModuleType(name))

import microchop_sampler


class OutputPathSafetyTests(unittest.TestCase):
    def test_render_stem_replaces_path_separators_and_unsafe_punctuation(self):
        self.assertEqual(
            microchop_sampler.safe_render_stem("Lead/../../Secrets: Take 1"),
            "lead_secrets_take_1",
        )

    def test_render_stem_keeps_default_track_name_stable(self):
        self.assertEqual(microchop_sampler.safe_render_stem("Main Melody"), "main_melody")


if __name__ == "__main__":
    unittest.main()
