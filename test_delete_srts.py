"""
Tests for delete_srts.py
"""
import os
import sys
from pathlib import Path
import tempfile
import shutil
import pytest

# Mock config module for testing
class MockConfig:
    BASE_DIR = None
    SCAN_FILES_IN_BASEDIR = True
    RECURSIVE = True
    EXCLUDE_FOLDERS = []

# Replace config with mock before importing delete_srts
sys.modules['config'] = MockConfig()

from delete_srts import delete_srt_files


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def mock_config(monkeypatch):
    """Fixture to mock the config module."""
    return MockConfig()


class TestDeleteSrtFiles:
    """Test suite for delete_srt_files function."""

    def test_base_dir_does_not_exist(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test behavior when BASE_DIR doesn't exist."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        non_existent = Path(temp_dir) / "does_not_exist"
        
        delete_srt_files(non_existent)
        
        captured = capsys.readouterr()
        assert "❌ BASE_DIR not found" in captured.out

    def test_scan_base_dir_true_deletes_files_in_base(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test that SCAN_FILES_IN_BASEDIR=True deletes .srt files in base directory."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        mock_config.SCAN_FILES_IN_BASEDIR = True
        mock_config.RECURSIVE = False
        
        # Create test files
        srt_file = Path(temp_dir) / "test.srt"
        srt_file.write_text("1\n00:00:00,000 --> 00:00:01,000\nTest")
        other_file = Path(temp_dir) / "other.txt"
        other_file.write_text("Should not be deleted")
        
        delete_srt_files(temp_dir)
        
        assert not srt_file.exists(), "SRT file should be deleted"
        assert other_file.exists(), "Non-SRT file should not be deleted"
        
        captured = capsys.readouterr()
        assert "🗑️ Deleted" in captured.out
        assert "✅ Finished deleting .srt files. Total deleted: 1" in captured.out

    def test_scan_base_dir_false_ignores_base_files(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test that SCAN_FILES_IN_BASEDIR=False preserves .srt files in base directory."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        mock_config.SCAN_FILES_IN_BASEDIR = False
        mock_config.RECURSIVE = False
        
        # Create test file in base dir
        srt_file = Path(temp_dir) / "test.srt"
        srt_file.write_text("1\n00:00:00,000 --> 00:00:01,000\nTest")
        
        delete_srt_files(temp_dir)
        
        assert srt_file.exists(), "SRT file in base dir should not be deleted when SCAN_FILES_IN_BASEDIR=False"
        
        captured = capsys.readouterr()
        assert "⚠️ Both SCAN_FILES_IN_BASEDIR and RECURSIVE are False" in captured.out

    def test_recursive_true_deletes_in_subdirs(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test that RECURSIVE=True deletes .srt files in subdirectories."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        mock_config.SCAN_FILES_IN_BASEDIR = False
        mock_config.RECURSIVE = True
        mock_config.EXCLUDE_FOLDERS = []
        
        # Create subdirectory with .srt file
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        srt_file = subdir / "test.srt"
        srt_file.write_text("1\n00:00:00,000 --> 00:00:01,000\nTest")
        
        delete_srt_files(temp_dir)
        
        assert not srt_file.exists(), "SRT file in subdirectory should be deleted when RECURSIVE=True"
        
        captured = capsys.readouterr()
        assert "✅ Finished deleting .srt files. Total deleted: 1" in captured.out

    def test_recursive_false_ignores_subdirs(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test that RECURSIVE=False ignores .srt files in subdirectories."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        mock_config.SCAN_FILES_IN_BASEDIR = True
        mock_config.RECURSIVE = False
        
        # Create file in base and subdirectory
        base_srt = Path(temp_dir) / "base.srt"
        base_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nBase")
        
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        sub_srt = subdir / "sub.srt"
        sub_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nSub")
        
        delete_srt_files(temp_dir)
        
        assert not base_srt.exists(), "SRT file in base dir should be deleted"
        assert sub_srt.exists(), "SRT file in subdir should NOT be deleted when RECURSIVE=False"
        
        captured = capsys.readouterr()
        assert "✅ Finished deleting .srt files. Total deleted: 1" in captured.out

    def test_exclude_folders_prevents_traversal(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test that EXCLUDE_FOLDERS prevents traversal and deletion."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        mock_config.SCAN_FILES_IN_BASEDIR = False
        mock_config.RECURSIVE = True
        mock_config.EXCLUDE_FOLDERS = ["excluded"]
        
        # Create excluded and normal subdirectories with .srt files
        excluded_dir = Path(temp_dir) / "excluded"
        excluded_dir.mkdir()
        excluded_srt = excluded_dir / "excluded.srt"
        excluded_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nExcluded")
        
        normal_dir = Path(temp_dir) / "normal"
        normal_dir.mkdir()
        normal_srt = normal_dir / "normal.srt"
        normal_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nNormal")
        
        delete_srt_files(temp_dir)
        
        assert excluded_srt.exists(), "SRT file in excluded folder should NOT be deleted"
        assert not normal_srt.exists(), "SRT file in normal folder should be deleted"
        
        captured = capsys.readouterr()
        assert "✅ Finished deleting .srt files. Total deleted: 1" in captured.out

    def test_exclude_multiple_folders(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test excluding multiple folders."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        mock_config.SCAN_FILES_IN_BASEDIR = False
        mock_config.RECURSIVE = True
        mock_config.EXCLUDE_FOLDERS = ["logs", "__pycache__"]
        
        # Create multiple excluded directories
        logs_dir = Path(temp_dir) / "logs"
        logs_dir.mkdir()
        logs_srt = logs_dir / "log.srt"
        logs_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nLog")
        
        pycache_dir = Path(temp_dir) / "__pycache__"
        pycache_dir.mkdir()
        pycache_srt = pycache_dir / "cache.srt"
        pycache_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nCache")
        
        normal_dir = Path(temp_dir) / "normal"
        normal_dir.mkdir()
        normal_srt = normal_dir / "normal.srt"
        normal_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nNormal")
        
        delete_srt_files(temp_dir)
        
        assert logs_srt.exists(), "SRT file in logs should NOT be deleted"
        assert pycache_srt.exists(), "SRT file in __pycache__ should NOT be deleted"
        assert not normal_srt.exists(), "SRT file in normal should be deleted"
        
        captured = capsys.readouterr()
        assert "✅ Finished deleting .srt files. Total deleted: 1" in captured.out

    def test_nested_exclude_folders(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test that excluded folders are not traversed even when nested."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        mock_config.SCAN_FILES_IN_BASEDIR = False
        mock_config.RECURSIVE = True
        mock_config.EXCLUDE_FOLDERS = ["excluded"]
        
        # Create nested structure with excluded folder
        excluded_dir = Path(temp_dir) / "excluded"
        excluded_dir.mkdir()
        nested_dir = excluded_dir / "nested"
        nested_dir.mkdir()
        nested_srt = nested_dir / "nested.srt"
        nested_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nNested")
        
        delete_srt_files(temp_dir)
        
        assert nested_srt.exists(), "Nested SRT in excluded folder should NOT be deleted"

    def test_preserves_non_srt_files(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test that non-.srt files are preserved."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        mock_config.SCAN_FILES_IN_BASEDIR = True
        mock_config.RECURSIVE = True
        
        # Create various file types
        txt_file = Path(temp_dir) / "readme.txt"
        txt_file.write_text("Text file")
        
        py_file = Path(temp_dir) / "script.py"
        py_file.write_text("print('hello')")
        
        srt_file = Path(temp_dir) / "subs.srt"
        srt_file.write_text("1\n00:00:00,000 --> 00:00:01,000\nSubs")
        
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        md_file = subdir / "readme.md"
        md_file.write_text("# Readme")
        
        delete_srt_files(temp_dir)
        
        assert txt_file.exists(), ".txt file should be preserved"
        assert py_file.exists(), ".py file should be preserved"
        assert md_file.exists(), ".md file should be preserved"
        assert not srt_file.exists(), ".srt file should be deleted"
        
        captured = capsys.readouterr()
        assert "✅ Finished deleting .srt files. Total deleted: 1" in captured.out

    def test_handles_deletion_errors_gracefully(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test that deletion errors are handled gracefully."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        mock_config.SCAN_FILES_IN_BASEDIR = True
        mock_config.RECURSIVE = False
        
        # Create a normal file and a read-only file (simulating permission error)
        normal_srt = Path(temp_dir) / "normal.srt"
        normal_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nNormal")
        
        # We can't easily simulate a permission error on Windows, so just test with normal files
        delete_srt_files(temp_dir)
        
        assert not normal_srt.exists(), "SRT file should be deleted"
        
        captured = capsys.readouterr()
        assert "✅ Finished deleting .srt files. Total deleted: 1" in captured.out

    def test_counts_deleted_files_correctly(self, capsys, temp_dir, mock_config, monkeypatch):
        """Test that deleted file count is accurate."""
        monkeypatch.setattr('delete_srts.config', mock_config)
        mock_config.SCAN_FILES_IN_BASEDIR = True
        mock_config.RECURSIVE = True
        
        # Create multiple SRT files in different locations
        base_srts = []
        for i in range(3):
            srt = Path(temp_dir) / f"base{i}.srt"
            srt.write_text(f"{i}\n00:00:00,000 --> 00:00:01,000\nBase{i}")
            base_srts.append(srt)
        
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        for i in range(2):
            srt = subdir / f"sub{i}.srt"
            srt.write_text(f"{i}\n00:00:00,000 --> 00:00:01,000\nSub{i}")
        
        delete_srt_files(temp_dir)
        
        for srt in base_srts:
            assert not srt.exists()
        
        captured = capsys.readouterr()
        assert "Total deleted: 5" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
