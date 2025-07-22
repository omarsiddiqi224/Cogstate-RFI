import os
from .logger import get_logger

logger = get_logger(__name__)

# --- File Scanning Function ---
def list_all_file_paths(root_dir):
    """
    Generates a list of all file paths within a given root directory,
    including files in nested subfolders. Handles potential errors during directory traversal.

    Args:
        root_dir (str): The path to the root directory to start scanning from.

    Returns:
        list: A list of absolute file paths. Returns an empty list if an error occurs.
    """
    file_paths = []
    try:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                file_paths.append(file_path)
                logger.debug(f"Found file: {file_path}") # Log at DEBUG level for verbose output
    except FileNotFoundError:
        logger.error(f"Error: The root directory '{root_dir}' was not found during traversal.")
        return []
    except PermissionError:
        logger.error(f"Error: Permission denied when accessing '{root_dir}' or a subdirectory.")
        return []
    except Exception as e:
        logger.critical(f"An unexpected error occurred while walking through '{root_dir}': {e}", exc_info=True)
        return []
    return file_paths