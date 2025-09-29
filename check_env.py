#!/usr/bin/env python3
"""
Скрипт для проверки окружения и настроек бота
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Проверка окружения"""
    load_dotenv()
    
    print("🔍 Проверка окружения Resistor Bot...")
    print("=" * 50)
    
    # Проверка .env файла
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"✅ Файл {env_file} найден")
    else:
        print(f"❌ Файл {env_file} не найден")
        print("   Создайте его из .env.example")
        return False
    
    # Проверка обязательных переменных
    bot_token = os.getenv('BOT_TOKEN')
    if bot_token and bot_token != 'your_telegram_bot_token_here':
        print("✅ BOT_TOKEN установлен")
    else:
        print("❌ BOT_TOKEN не установлен или имеет значение по умолчанию")
        return False
    
    # Проверка Tesseract
    tesseract_path = os.getenv('TESSERACT_PATH')
    if tesseract_path and os.path.exists(tesseract_path):
        print("✅ Tesseract найден")
    else:
        print("⚠️  Tesseract не настроен (не обязательно для Linux/Mac)")
    
    # Проверка зависимостей
    try:
        import telegram
        import PIL
        import cv2
        import numpy
        import pytesseract
        print("✅ Все Python зависимости установлены")
    except ImportError as e:
        print(f"❌ Ошибка зависимостей: {e}")
        return False
    
    print("=" * 50)
    print("🎉 Окружение настроено правильно!")
    print("🚀 Запустите бота: python resistor_bot.py")
    
    return True

if __name__ == '__main__':
    success = check_environment()
    sys.exit(0 if success else 1)