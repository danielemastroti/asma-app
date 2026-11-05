"""
Unit tests for OperationLogger
"""

import unittest
from asma_core.operation_logger import OperationLogger, OperationLogEntry


class TestOperationLogger(unittest.TestCase):

    def setUp(self):
        OperationLogger._instance = None
        self.logger = OperationLogger()

    def tearDown(self):
        OperationLogger._instance = None

    def test_singleton_and_initial_state(self):
        logger2 = OperationLogger()
        self.assertIs(self.logger, logger2)
        entries = self.logger.get_entries()
        self.assertGreaterEqual(len(entries), 1)
        self.assertEqual(entries[0].category, "SISTEMA")

    def test_log_and_filtering(self):
        self.logger.log("💾", "BRANO", "Nuova revisione salvata", level="SUCCESS", user="Daniele")
        self.logger.log("🏷️", "TAG", "Tag rock rinominato", level="INFO", user="Admin")
        self.logger.log("🗑️", "CESTINO", "Brano eliminato", level="WARNING", user="Luca")

        entries = self.logger.get_entries(limit=10)
        self.assertEqual(entries[0].category, "CESTINO")
        self.assertEqual(entries[1].category, "TAG")
        self.assertEqual(entries[2].category, "BRANO")

        tag_entries = self.logger.get_entries(category="TAG")
        self.assertEqual(len(tag_entries), 1)
        self.assertEqual(tag_entries[0].message, "Tag rock rinominato")

    def test_clear_console(self):
        self.logger.log("🔍", "RICERCA", "Cercato brano", level="INFO")
        self.logger.clear()
        entries = self.logger.get_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].category, "CONSOLE")

    def test_to_terminal_line(self):
        entry = OperationLogEntry(
            timestamp="12:00:00",
            icon="💾",
            category="BRANO",
            message="Test save",
            level="SUCCESS",
            user="User1"
        )
        line = entry.to_terminal_line()
        self.assertIn("12:00:00", line)
        self.assertIn("[BRANO]", line)
        self.assertIn("Test save", line)


if __name__ == "__main__":
    unittest.main()
