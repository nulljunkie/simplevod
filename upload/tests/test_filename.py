import pytest
from utils.filename import get_safe_filename, sanitize_filename, is_valid_filename

class TestFilenameSanitization:
    
    @pytest.mark.parametrize("filename,expected", [
        ("File Video.mp4", "file video.mp4"),
        ("My Video 😀.mp4", "my video 😀.mp4"),
        ("Video-File_Name.avi", "video-file_name.avi"),
        ("file<with>bad:chars.mkv", "filewithbadchars.mkv"),
        ("Video/Path\\File.mp4", "videopathfile.mp4"),
        ("CON.txt", "con_.txt"),
        ("file with spaces.mov", "file with spaces.mov"),
        ("Special!@#$%chars.webm", "special!@#$%chars.webm"),
        ("", "untitled"),
        ("你好世界.mp4", "你好世界.mp4"),
    ])
    def test_filename_sanitization(self, filename, expected):
        assert sanitize_filename(filename) == expected

    @pytest.mark.parametrize("filename", [
        "normal_file.mp4",
        "file with spaces.avi",
        "emoji_video_😀.mkv",
        "你好世界.mp4",
        "file-name_test.mov",
    ])
    def test_valid_filenames(self, filename):
        assert is_valid_filename(filename)

    @pytest.mark.parametrize("filename", [
        "",
        "file\x00with\x01null.mp4",
        "a" * 300,  # too long
        "CON.txt",
        "PRN.avi",
    ])
    def test_invalid_filenames(self, filename):
        assert not is_valid_filename(filename)

    def test_get_safe_filename(self):
        # Valid filename should return as-is
        assert get_safe_filename("valid_file.mp4") == "valid_file.mp4"
        
        # Invalid filename should be sanitized
        assert get_safe_filename("file<>bad.mp4") == "filebad.mp4"
        
        # Reserved name with fallback
        result = get_safe_filename("CON.txt", "backup.txt")
        assert result == "con_.txt"  # Should use sanitized version since it's valid