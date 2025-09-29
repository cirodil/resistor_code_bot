import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Класс для управления настройками приложения"""
    
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = os.getenv('BOT_ADMIN_ID')
    
    # Tesseract OCR
    TESSERACT_PATH = os.getenv('TESSERACT_PATH')
    
    # Logging
    LOG_LEVEL = os.getenv('BOT_LOG_LEVEL', 'INFO')
    
    # Bot settings
    MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10MB
    REQUEST_TIMEOUT = 30
    
    @classmethod
    def validate(cls):
        """Проверка обязательных настроек"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN не установлен в .env файле")
        
        if errors:
            raise ValueError("Ошибки конфигурации:\n- " + "\n- ".join(errors))
    
    @classmethod
    def setup_tesseract(cls):
        """Настройка пути к Tesseract"""
        if cls.TESSERACT_PATH and os.path.exists(cls.TESSERACT_PATH):
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = cls.TESSERACT_PATH
            return True
        return False

# Проверяем настройки при импорте
Config.validate()