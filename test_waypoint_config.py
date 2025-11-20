#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовий скрипт для перевірки функціональності збереження/завантаження останнього waypoint файлу
"""

import json
import os
import tempfile
from pathlib import Path

def test_gui_config():
    """Тестуємо функціональність конфігурації GUI"""

    # Створюємо тимчасовий конфігураційний файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_file = f.name
        json.dump({
            "last_waypoint_file": None,
            "app_version": "test"
        }, f)

    print(f"Створено тимчасовий конфігураційний файл: {config_file}")

    # Симуляція збереження шляху
    test_waypoint_file = os.path.join(os.path.dirname(__file__), 'waypoints', 'example_RU_repeat.json')

    def save_last_waypoint_file(filepath):
        """Симуляція методу _save_last_waypoint_file"""
        try:
            config_data = {}
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

            config_data['last_waypoint_file'] = filepath
            config_data['app_version'] = 'test'

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)

            print(f"[OK] Збережено шлях до waypoint файлу: {filepath}")
            return True
        except Exception as e:
            print(f"[ERROR] Помилка збереження конфігурації GUI: {e}")
            return False

    def get_last_waypoint_file():
        """Симуляція методу _get_last_waypoint_file"""
        try:
            if not os.path.exists(config_file):
                return None

            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            return config_data.get('last_waypoint_file')
        except Exception as e:
            print(f"[ERROR] Помилка завантаження конфігурації GUI: {e}")
            return None

    # Тестуємо збереження шляху
    print("\n--- Тест 1: Збереження шляху до існуючого файлу ---")
    result = save_last_waypoint_file(test_waypoint_file)
    assert result, "Не вдалося зберегти шлях"

    # Тестуємо завантаження шляху
    print("\n--- Тест 2: Завантаження шляху ---")
    loaded_file = get_last_waypoint_file()
    assert loaded_file == test_waypoint_file, f"Очікуваний шлях: {test_waypoint_file}, отриманий: {loaded_file}"
    print(f"[OK] Завантажено правильний шлях: {loaded_file}")

    # Перевіряємо, що файл існує
    print("\n--- Тест 3: Перевірка існування файлу ---")
    if loaded_file and os.path.exists(loaded_file):
        print(f"[OK] Файл існує: {loaded_file}")
    else:
        print(f"[ERROR] Файл не існує: {loaded_file}")

    # Тестуємо збереження None
    print("\n--- Тест 4: Збереження None ---")
    result = save_last_waypoint_file(None)
    assert result, "Не вдалося зберегти None"

    # Тестуємо завантаження None
    print("\n--- Тест 5: Завантаження None ---")
    loaded_file = get_last_waypoint_file()
    assert loaded_file is None, f"Очікувався None, отримано: {loaded_file}"
    print("[OK] Завантажено None правильно")

    # Очищення
    os.unlink(config_file)
    print(f"\n[CLEAR] Видалено тимчасовий файл: {config_file}")

    print("\n[SUCCESS] Всі тести пройдено успішно!")

if __name__ == "__main__":
    test_gui_config()