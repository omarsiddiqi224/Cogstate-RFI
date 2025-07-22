import logging
from pathlib import Path
from typing import Optional, Dict

from rfiprocessor.utils.logger import get_logger
from config import Config

# Configure logging
logger = get_logger(__name__)
config = Config()

# This dictionary will act as an in-memory cache to store prompts after their first read.
_prompt_cache: Dict[str, str] = {}

# Define the absolute path to the directory containing this file.
# This makes the loader robust, regardless of the current working directory.
PROMPTS_DIR = Path(config.PROMPTS_DIR)

def load_prompt(prompt_name: str) -> Optional[str]:
    """
    Loads a prompt from a .txt file in the prompts directory.
    This function implements an in-memory cache to avoid redundant file I/O.
    On the first call for a specific prompt, it reads the file from disk.
    Subsequent calls for the same prompt will return the cached content directly.
    Args:
        prompt_name: The base name of the prompt file (without the .txt extension).
                     For example, to load 'router_agent.txt', use prompt_name='router_agent'.
    Returns:
        The content of the prompt file as a string, or None if the file
        cannot be found or read.
    """
    # Check the cache first
    if prompt_name in _prompt_cache:
        logger.debug(f"Returning cached prompt: '{prompt_name}'")
        return _prompt_cache[prompt_name]

    file_path = PROMPTS_DIR / f"{prompt_name}.txt"
    logger.info(f"Loading prompt '{prompt_name}' from: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # Store the successfully loaded prompt in the cache
        _prompt_cache[prompt_name] = prompt_content
        
        return prompt_content

    except FileNotFoundError:
        logger.error(f"Prompt file not found at path: {file_path}")
        return None
    except IOError as e:
        logger.error(f"An I/O error occurred while reading prompt file {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading prompt '{prompt_name}': {e}")
        return None