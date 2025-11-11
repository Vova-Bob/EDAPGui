"""Утиліта для роботи з локалізованими ресурсами у форматі .resx."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree


class ResourceManager:
    """Простий менеджер ресурсів для отримання локалізованих рядків."""

    def __init__(self, resource_path: Path) -> None:
        self.resource_path = resource_path
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        tree = ElementTree.parse(self.resource_path)
        root = tree.getroot()
        for data in root.findall("data"):
            key = data.get("name")
            if not key:
                continue
            value_element = data.find("value")
            value = value_element.text if value_element is not None else ""
            self._data[key] = value

    def get(self, key: str, **kwargs) -> str:
        value = self._data.get(key, key)
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value
        return value
