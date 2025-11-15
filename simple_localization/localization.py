import os
import json


class LocalizationManager:
    """Class managing localization.

    Access to the localization data is done through the [] operator (e.g. localization["key"]).

    Attributes:
        folder_path (str): Path to the folder containing the localization files.
        available_languages (list[str]): List of available languages. Loaded when calling load().
        language (str): Current language.
    """

    def __init__(self, folder_path: str, language: str) -> None:
        self.folder_path = folder_path
        self.available_languages = []
        self.language = language

        self._data = {}  # Parsed localization file

        # Load available languages
        self._load_available_languages()
        # Check if the localization files are bijective
        self._check_bijectivity()
        # Load the localization file. Raises an exception if the language is not available.
        self.change_language(self.language)

    def _load_available_languages(self) -> None:
        """Find all available languages in the specified directory"""
        for file in os.listdir(self.folder_path):
            if not file.endswith(".json"):
                continue
            if file.startswith("OCR_"):
                # OCR locale files are handled by a dedicated manager.
                continue
            self.available_languages.append(file[:-5])
        self.available_languages.sort()

    def _check_bijectivity(self) -> None:
        """Check if the localization data is bijective.

        All json files should have the same keys. If not, an exception is raised.
        """
        keys = {}

        # Capture each language's key set.
        for language in self.available_languages:
            with open(f"{self.folder_path}/{language}.json", "r", encoding='utf-8') as file:
                data = json.load(file)
                # OCR keys live in dedicated OCR locale files, but older locale
                # packs (or local user overrides) may still contain entries
                # prefixed with "ocr.". Exclude them from the bijectivity check
                # so UI localization integrity is verified independently of OCR
                # tokens and we avoid false positives like the reported
                # CARTOGRAPHICS mismatch.
                filtered_keys = {k for k in data.keys() if not k.startswith("ocr.")}
                keys[language] = filtered_keys

        if not keys:
            return

        iterator = iter(keys.items())
        reference_language, reference_keys = next(iterator)
        for language, language_keys in iterator:
            if language_keys != reference_keys:
                missing = sorted(reference_keys - language_keys)
                extra = sorted(language_keys - reference_keys)
                raise Exception(
                    "The localization files have different keys. "
                    f"Language '{language}' missing: {missing}; extra: {extra}."
                )

    def __getitem__(self, key: str) -> str:
        """Get the localized string for the specified key.

        Args:
            key (str): Key to the localized string.

        Returns:
            str: The localized string from the json file.
        """
        return self._data[key]

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
        self.refresh()


class OCRTokenManager:
    """Load HUD/OCR tokens independent of the UI localization files."""

    def __init__(self, folder_path: str, language: str) -> None:
        self.folder_path = folder_path
        self.language = language
        self.available_languages = []
        self._data = {}

        self._load_available_languages()
        self._check_bijectivity()
        self.change_language(language)

    def _load_available_languages(self) -> None:
        prefix = "OCR_"
        for file in os.listdir(self.folder_path):
            if file.startswith(prefix) and file.endswith(".json"):
                self.available_languages.append(file[len(prefix):-5])
        self.available_languages.sort()

    def _file_path(self, language: str) -> str:
        return os.path.join(self.folder_path, f"OCR_{language}.json")

    def _check_bijectivity(self) -> None:
        if not self.available_languages:
            raise Exception("No OCR locale files found. Expected OCR_*.json entries.")

        key_sets: dict[str, set[str]] = {}
        for language in self.available_languages:
            path = self._file_path(language)
            with open(path, "r", encoding='utf-8') as file:
                key_sets[language] = set(json.load(file).keys())

        iterator = iter(key_sets.items())
        reference_language, reference_keys = next(iterator)
        for language, language_keys in iterator:
            if language_keys != reference_keys:
                missing = sorted(reference_keys - language_keys)
                extra = sorted(language_keys - reference_keys)
                raise Exception(
                    "OCR locale files have different keys. "
                    f"Language '{language}' missing: {missing}; extra: {extra}."
                )

    def __getitem__(self, key: str) -> str:
        return self._data[key]

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def refresh(self) -> None:
        path = self._file_path(self.language)
        with open(path, "r", encoding='utf-8') as file:
            self._data = json.load(file)

    def change_language(self, language: str) -> None:
        if language not in self.available_languages:
            raise Exception(
                f"OCR language not found in {self.folder_path}. "
                f"Is there a {self.folder_path}/OCR_{language}.json file?"
            )
        self.language = language
        self.refresh()
