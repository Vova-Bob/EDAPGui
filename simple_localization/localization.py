import os
import json
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


def localization(key: str):
    """Decorator for automatic localization of function return values.

    Args:
        key: Localization key to use for the return value.

    Returns:
        Decorator function that wraps the original function.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get the localized text using the instance's locale manager
            if hasattr(self, 'locale'):
                try:
                    return self.locale[key]
                except KeyError:
                    logger.warning(f"Missing localization key: {key}")
                    return key  # Fallback to key name
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class LocalizationManager:
    """Class managing localization.

    Access to the localization data is done through the [] operator (e.g. localization["key"]).

    Attributes:
        folder_path (str): Path to the folder containing the localization files.
        available_languages (list[str]): List of available languages. Loaded when calling load().
        language (str): Current language.
        fallback_language (str): Fallback language when translation is missing.
    """

    def __init__(self, folder_path: str, language: str, fallback_language: str = "en") -> None:
        self.folder_path = folder_path
        self.available_languages = []
        self.language = language
        self.fallback_language = fallback_language

        self._data = {}  # Parsed localization file
        self._missing_keys = set()  # Track missing keys for logging

        # Load available languages
        self._load_available_languages()
        # Check if the localization files are bijective
        self._check_bijectivity()
        # Load the localization file. Raises an exception if the language is not available.
        self.change_language(self.language)

    def _load_available_languages(self) -> None:
        """Find all available languages in the specified directory"""
        for file in os.listdir(self.folder_path):
            if file.endswith(".json"):
                self.available_languages.append(file[:-5])

    def _check_bijectivity(self) -> None:
        """Check if the localization data is bijective.

        All json files should have the same keys. If not, an exception is raised.
        """
        keys = []

        # Add a list of all keys to a list
        for lang in self.available_languages:
            with open(f"{self.folder_path}/{lang}.json", "r", encoding='utf-8') as file:
                data = json.load(file)
                keys.append(list(data.keys()))

        # Compare the keys of the first language with the others
        for i in range(1, len(keys)):
            if keys[i] != keys[i - 1]:
                raise Exception("The localization files have different keys. Make sure they are all the same.")

    def __getitem__(self, key: str) -> str:
        """Get the localized string for the specified key.

        Args:
            key (str): Key to the localized string.

        Returns:
            str: The localized string from the json file.
        """
        if key not in self._data:
            # Log missing translation
            if key not in self._missing_keys:
                self._missing_keys.add(key)
                logger.warning(f"Missing localization key '{key}' in language '{self.language}'. Using fallback.")
            # Try fallback language
            if self.language != self.fallback_language:
                try:
                    with open(f"{self.folder_path}/{self.fallback_language}.json", "r", encoding='utf-8') as file:
                        fallback_data = json.load(file)
                        if key in fallback_data:
                            return fallback_data[key]
                except Exception as e:
                    logger.error(f"Failed to load fallback language '{self.fallback_language}': {e}")
            # Final fallback: return the key itself
            return key
        return self._data[key]

    def get_available_languages(self) -> list[str]:
        """Get list of available languages.

        Returns:
            list[str]: List of available language codes.
        """
        return self.available_languages

    def set_language(self, language: str) -> None:
        """Change the current language in real-time.

        Args:
            language (str): Language to load. Should be the name of the file without the extension.
                           (e.g. "en" for the file "en.json")

        Raises:
            Exception: If the language is not available.
        """
        # Check if the language is available
        if language not in self.available_languages:
            raise Exception(
                f"Language not found in {self.folder_path}. Is there a {self.folder_path}/{language}.json file?")

        # Update the language
        self.language = language
        self._missing_keys.clear()  # Clear missing keys cache
        self.refresh()

    def reload(self) -> None:
        """Reload localization files from specified folder.

        This is useful if the localization files have been updated on runtime.
        Called when updating the language.
        """
        # Clear missing keys cache
        self._missing_keys.clear()
        # Load the localization file
        self._data = {}
        with open(f"{self.folder_path}/{self.language}.json", "r", encoding='utf-8') as file:
            self._data = json.load(file)

    def get_fallback_text(self, key: str) -> str:
        """Get fallback text for a missing translation key.

        Args:
            key (str): The localization key that is missing.

        Returns:
            str: The fallback text from the fallback language, or the key itself if not found.
        """
        if self.language == self.fallback_language:
            return key  # Already using fallback

        try:
            with open(f"{self.folder_path}/{self.fallback_language}.json", "r", encoding='utf-8') as file:
                fallback_data = json.load(file)
                if key in fallback_data:
                    return fallback_data[key]
        except Exception as e:
            logger.error(f"Failed to load fallback language '{self.fallback_language}': {e}")

        return key  # Final fallback

    def refresh(self) -> None:
        """Load localization files from specified folder.

        This is useful if the localization files have been updated on runtime.
        Called when updating the language.
        """
        # Load the localization file
        self._data = {}
        with open(f"{self.folder_path}/{self.language}.json", "r", encoding='utf-8') as file:
            self._data = json.load(file)

    def change_language(self, language: str) -> None:
        """Update the data for specified language.

        Args:
            language (str): Language to load. Should be the name of the file without the extension. (e.g. "en_EN" for the file "en_EN.json")
        """
        # Check if the language is available
        if not language in self.available_languages:
            raise Exception(
                f"Language not found in {self.folder_path}. Is there a {self.folder_path}/{language}.json file?")

        # Update the language
        self.language = language
        self._missing_keys.clear()  # Clear missing keys cache
        self.refresh()
