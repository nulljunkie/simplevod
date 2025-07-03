import time
from typing import Optional
from pathvalidate import sanitize_filename as pv_sanitize_filename, is_valid_filename as pv_is_valid_filename

def get_safe_filename(original_filename: str, fallback_name: Optional[str] = None) -> str:
    """
    Get a safe filename, using fallback if needed.
    
    Args:
        original_filename: The original filename to sanitize
        fallback_name: Optional fallback name if original and sanitized are invalid
        
    Returns:
        A safe filename string
    """
    if is_valid_filename(original_filename):
        return original_filename
    
    sanitized = sanitize_filename(original_filename)
    if is_valid_filename(sanitized):
        return sanitized
    
    if fallback_name and is_valid_filename(fallback_name):
        return fallback_name
    
    # Extract extension if possible
    extension = ""
    if "." in original_filename:
        parts = original_filename.rsplit(".", 1)
        if len(parts) == 2 and len(parts[1]) <= 10:
            extension = "." + parts[1]
    
    return f"file_{int(time.time())}{extension}"

def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize a filename using pathvalidate library.
    
    Args:
        filename: The filename to sanitize
        max_length: Maximum length for the filename (default: 100)
        
    Returns:
        A sanitized filename string
    """
    if not filename:
        return "untitled"
    
    # Use pathvalidate to sanitize the filename
    sanitized = pv_sanitize_filename(filename, platform="universal")
    
    # Handle empty result
    if not sanitized or sanitized.isspace():
        return "untitled"
    
    # Truncate if necessary
    if len(sanitized) > max_length:
        # Try to preserve extension
        if "." in sanitized:
            name, ext = sanitized.rsplit(".", 1)
            if len(ext) <= 10:  # reasonable extension length
                max_name_length = max_length - len(ext) - 1
                if max_name_length > 0:
                    sanitized = name[:max_name_length] + "." + ext
                else:
                    sanitized = sanitized[:max_length]
            else:
                sanitized = sanitized[:max_length]
        else:
            sanitized = sanitized[:max_length]
    
    return sanitized.lower()

def is_valid_filename(filename: str) -> bool:
    """
    Check if a filename is valid using pathvalidate library.
    
    Args:
        filename: The filename to validate
        
    Returns:
        True if the filename is valid, False otherwise
    """
    if not filename or len(filename) > 255:
        return False
    
    # Check if filename is only whitespace
    if filename.strip() == "":
        return False
    
    return pv_is_valid_filename(filename, platform="universal")