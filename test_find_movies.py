"""
Comprehensive tests for find_movies() function in process_single_movie.py

Tests directory structure handling for:
- Deeply nested folders
- Multiple nesting levels
- Multiple files per folder
- Config settings (SCAN_FILES_IN_BASEDIR, EXCLUDE_FOLDERS)
"""

import os
import sys
from pathlib import Path
import tempfile
import shutil
import pytest

# Mock config module
class MockConfig:
    BASE_DIR = None
    VIDEO_EXTENSIONS = [".mp4", ".mkv", ".mov", ".avi"]
    SCAN_FILES_IN_BASEDIR = True
    EXCLUDE_FOLDERS = []

sys.modules['config'] = MockConfig()

from main.process_single_movie import find_movies


@pytest.fixture
def temp_structure():
    """Create temporary directory structure for testing."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def create_file(path: Path, name: str) -> Path:
    """Create a file in the given path."""
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / name
    file_path.write_text("")
    return file_path


class TestFindMoviesDeepNesting:
    """Test deeply nested folder structures."""
    
    def test_three_level_nesting_single_file(self, temp_structure):
        """Test: TV Shows > Avatar > Season 1 > video.mkv"""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create structure
        create_file(base / "TV Shows" / "Avatar" / "Season 1", "episode1.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 1
        assert movies[0].name == "episode1.mkv"
        assert "Avatar" in str(movies[0])
        assert "Season 1" in str(movies[0])
    
    def test_two_level_nesting_single_file(self, temp_structure):
        """Test: TV Shows > Avatar > video.mkv"""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create structure
        create_file(base / "TV Shows" / "Avatar", "episode1.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 1
        assert movies[0].name == "episode1.mkv"
        assert "Avatar" in str(movies[0])
    
    def test_one_level_nesting_single_file(self, temp_structure):
        """Test: TV Shows > video.mkv"""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create structure
        create_file(base / "TV Shows", "episode1.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 1
        assert movies[0].name == "episode1.mkv"
        assert "TV Shows" in str(movies[0])
    
    def test_base_level_single_file(self, temp_structure):
        """Test: video.mkv (at base level)"""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create file at base
        create_file(base, "movie.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 1
        assert movies[0].name == "movie.mkv"


class TestFindMoviesMultipleLevels:
    """Test mixed nesting levels."""
    
    def test_multiple_nesting_levels_mixed(self, temp_structure):
        """Test files at different nesting levels in same structure."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create mixed structure
        create_file(base, "base_movie.mkv")
        create_file(base / "Movies", "movie1.mkv")
        create_file(base / "TV Shows" / "Avatar", "avatar_ep1.mkv")
        create_file(base / "TV Shows" / "Avatar" / "Season 1", "avatar_s1_ep1.mkv")
        create_file(base / "TV Shows" / "Avatar" / "Season 1", "avatar_s1_ep2.mkv")
        create_file(base / "TV Shows" / "Shrek", "shrek_movie.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 6
        assert any(m.name == "base_movie.mkv" for m in movies)
        assert any(m.name == "movie1.mkv" for m in movies)
        assert sum(1 for m in movies if "avatar" in m.name.lower()) == 3
        assert any(m.name == "shrek_movie.mkv" for m in movies)
    
    def test_multiple_files_per_folder(self, temp_structure):
        """Test multiple video files in same folder."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create structure with multiple files
        create_file(base / "Movies" / "Action", "movie1.mkv")
        create_file(base / "Movies" / "Action", "movie2.mp4")
        create_file(base / "Movies" / "Action", "movie3.avi")
        create_file(base / "Movies" / "Comedy", "funny1.mkv")
        create_file(base / "Movies" / "Comedy", "funny2.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 5
        action_movies = [m for m in movies if "Action" in str(m)]
        comedy_movies = [m for m in movies if "Comedy" in str(m)]
        assert len(action_movies) == 3
        assert len(comedy_movies) == 2


class TestFindMoviesExcludeFolders:
    """Test EXCLUDE_FOLDERS configuration."""
    
    def test_exclude_single_folder(self, temp_structure):
        """Test excluding a single folder."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = ["Excluded"]
        
        # Create structure with excluded folder
        create_file(base / "Movies", "movie1.mkv")
        create_file(base / "Excluded", "movie2.mkv")
        create_file(base / "TV Shows", "show1.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 2
        assert not any("Excluded" in str(m) for m in movies)
        assert any(m.name == "movie1.mkv" for m in movies)
        assert any(m.name == "show1.mkv" for m in movies)
    
    def test_exclude_multiple_folders(self, temp_structure):
        """Test excluding multiple folders."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = ["Samples", "__pycache__", "Archive"]
        
        # Create structure
        create_file(base / "Movies", "movie1.mkv")
        create_file(base / "Samples", "sample.mkv")
        create_file(base / "__pycache__", "cache.mkv")
        create_file(base / "Archive", "old.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 1
        assert movies[0].name == "movie1.mkv"
    
    def test_exclude_nested_folder_prevents_recursion(self, temp_structure):
        """Test that excluding a folder prevents descent into it."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = ["Excluded"]
        
        # Create deeply nested structure with excluded folder
        create_file(base / "Movies", "movie1.mkv")
        create_file(base / "Excluded" / "Subfolder1" / "Subfolder2", "movie2.mkv")
        create_file(base / "TV Shows" / "Avatar", "show1.mkv")
        
        movies = find_movies(base)
        
        # Should only find 2, not 3 (excluded folder prevents recursion)
        assert len(movies) == 2
        assert not any("Excluded" in str(m) for m in movies)


class TestFindMoviesScanFilesInBaseDir:
    """Test SCAN_FILES_IN_BASEDIR configuration."""
    
    def test_scan_files_in_basedir_true(self, temp_structure):
        """Test SCAN_FILES_IN_BASEDIR=True includes base level files."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create files at base and in subfolder
        create_file(base, "base_movie.mkv")
        create_file(base / "Subfolder", "sub_movie.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 2
        assert any(m.name == "base_movie.mkv" for m in movies)
        assert any(m.name == "sub_movie.mkv" for m in movies)
    
    def test_scan_files_in_basedir_false(self, temp_structure):
        """Test SCAN_FILES_IN_BASEDIR=False excludes base level files."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = False
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create files at base and in subfolder
        create_file(base, "base_movie.mkv")
        create_file(base / "Subfolder", "sub_movie.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 1
        assert movies[0].name == "sub_movie.mkv"
        assert not any(m.name == "base_movie.mkv" for m in movies)


class TestFindMoviesDuplicatePrevention:
    """Test that duplicates are prevented."""
    
    def test_no_duplicate_files(self, temp_structure):
        """Test that files are not duplicated in results."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create structure
        create_file(base / "Movies" / "Action", "movie.mkv")
        create_file(base / "Movies" / "Comedy", "movie.mkv")
        create_file(base / "TV Shows" / "Avatar" / "Season 1", "episode.mkv")
        
        movies = find_movies(base)
        
        # Should be 3 unique files
        assert len(movies) == 3
        # Check all are unique paths
        paths = [str(m) for m in movies]
        assert len(paths) == len(set(paths))


class TestFindMoviesSorting:
    """Test that results are sorted properly."""
    
    def test_sorting_by_parent_then_name(self, temp_structure):
        """Test that files are sorted by parent folder then by filename."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create structure with specific ordering
        create_file(base / "Zebra", "z_movie.mkv")
        create_file(base / "Zebra", "a_movie.mkv")
        create_file(base / "Alpha", "z_movie.mkv")
        create_file(base / "Alpha", "a_movie.mkv")
        create_file(base / "Beta", "movie.mkv")
        
        movies = find_movies(base)
        
        # Should be sorted by parent folder name, then by filename
        parent_names = [m.parent.name for m in movies]
        # Alpha should come before Beta, Beta before Zebra (alphabetical)
        assert parent_names.index("Alpha") < parent_names.index("Beta")
        assert parent_names.index("Beta") < parent_names.index("Zebra")


class TestFindMoviesFileExtensions:
    """Test that only correct file extensions are found."""
    
    def test_only_video_extensions(self, temp_structure):
        """Test that only .mp4, .mkv, .mov, .avi are found."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create files with various extensions
        create_file(base / "Movies", "movie.mkv")
        create_file(base / "Movies", "movie.mp4")
        create_file(base / "Movies", "movie.mov")
        create_file(base / "Movies", "movie.avi")
        create_file(base / "Movies", "subtitle.srt")
        create_file(base / "Movies", "audio.mp3")
        create_file(base / "Movies", "readme.txt")
        
        movies = find_movies(base)
        
        assert len(movies) == 4
        assert all(m.suffix in [".mkv", ".mp4", ".mov", ".avi"] for m in movies)


class TestFindMoviesCombinedConfigs:
    """Test combinations of configurations."""
    
    def test_exclude_and_scan_false(self, temp_structure):
        """Test SCAN_FILES_IN_BASEDIR=False with EXCLUDE_FOLDERS."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = False
        MockConfig.EXCLUDE_FOLDERS = ["Excluded"]
        
        # Create structure
        create_file(base, "base_movie.mkv")
        create_file(base / "Movies", "movie1.mkv")
        create_file(base / "Excluded", "excluded.mkv")
        create_file(base / "TV Shows" / "Avatar", "show.mkv")
        
        movies = find_movies(base)
        
        # Should have 2: movie1.mkv and show.mkv (not base_movie, not excluded)
        assert len(movies) == 2
        assert not any(m.name == "base_movie.mkv" for m in movies)
        assert not any(m.name == "excluded.mkv" for m in movies)
        assert any(m.name == "movie1.mkv" for m in movies)
        assert any(m.name == "show.mkv" for m in movies)


class TestFindMoviesEmptyDirs:
    """Test handling of empty directories."""
    
    def test_empty_directories_dont_cause_errors(self, temp_structure):
        """Test that empty directories don't cause issues."""
        base = Path(temp_structure)
        MockConfig.BASE_DIR = str(base)
        MockConfig.SCAN_FILES_IN_BASEDIR = True
        MockConfig.EXCLUDE_FOLDERS = []
        
        # Create empty and non-empty folders
        (base / "EmptyFolder").mkdir(parents=True)
        (base / "AnotherEmpty" / "Nested").mkdir(parents=True)
        create_file(base / "WithFiles", "movie.mkv")
        
        movies = find_movies(base)
        
        assert len(movies) == 1
        assert movies[0].name == "movie.mkv"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
