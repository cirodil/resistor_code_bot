import logging
import re
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from PIL import Image
import pytesseract
import io
import cv2
import numpy as np
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.getenv('BOT_LOG_LEVEL', 'INFO')
)

# Настройка Tesseract (для Windows)
tesseract_path = os.getenv('TESSERACT_PATH')
if tesseract_path and os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Проверка обязательных переменных
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("❌ BOT_TOKEN не найден в переменных окружения!")
    exit(1)

# Импортируем функции из наших модулей
try:
    from resistor_cv import recognize_resistor_cv
    from smd_decoder import smd_to_resistance, resistance_to_smd, validate_smd_code
except ImportError as e:
    logging.error(f"❌ Ошибка импорта модулей: {e}")
    # Создаем заглушки для тестирования
    def recognize_resistor_cv(img):
        return "Модуль CV не доступен"
    
    def smd_to_resistance(code):
        return None
    
    def resistance_to_smd(value):
        return "Модуль SMD не доступен"
    
    def validate_smd_code(code):
        return False

# Цветовая маркировка резисторов (русские названия как основные)
COLOR_CODES = {
    'черный': 0, 'black': 0,
    'коричневый': 1, 'brown': 1,
    'красный': 2, 'red': 2,
    'оранжевый': 3, 'orange': 3,
    'желтый': 4, 'yellow': 4,
    'зеленый': 5, 'green': 5,
    'синий': 6, 'blue': 6,
    'фиолетовый': 7, 'violet': 7, 'purple': 7,
    'серый': 8, 'gray': 8, 'grey': 8,
    'белый': 9, 'white': 9,
    'золотой': -1, 'gold': -1,
    'серебряный': -2, 'silver': -2
}

MULTIPLIERS = {
    'черный': 1, 'black': 1,
    'коричневый': 10, 'brown': 10,
    'красный': 100, 'red': 100,
    'оранжевый': 1000, 'orange': 1000,
    'желтый': 10000, 'yellow': 10000,
    'зеленый': 100000, 'green': 100000,
    'синий': 1000000, 'blue': 1000000,
    'фиолетовый': 10000000, 'violet': 10000000, 'purple': 10000000,
    'серый': 100000000, 'gray': 100000000, 'grey': 100000000,
    'белый': 1000000000, 'white': 1000000000,
    'золотой': 0.1, 'gold': 0.1,
    'серебряный': 0.01, 'silver': 0.01
}

TOLERANCE = {
    'коричневый': '±1%', 'brown': '±1%',
    'красный': '±2%', 'red': '±2%',
    'зеленый': '±0.5%', 'green': '±0.5%',
    'синий': '±0.25%', 'blue': '±0.25%',
    'фиолетовый': '±0.1%', 'violet': '±0.1%', 'purple': '±0.1%',
    'серый': '±0.05%', 'gray': '±0.05%', 'grey': '±0.05%',
    'золотой': '±5%', 'gold': '±5%',
    'серебряный': '±10%', 'silver': '±10%',
    'нет': '±20%'
}

# Словарь для преобразования английских названий в русские
EN_TO_RU_COLORS = {
    'black': 'черный',
    'brown': 'коричневый', 
    'red': 'красный',
    'orange': 'оранжевый',
    'yellow': 'желтый',
    'green': 'зеленый',
    'blue': 'синий',
    'violet': 'фиолетовый',
    'purple': 'фиолетовый',
    'gray': 'серый',
    'grey': 'серый',
    'white': 'белый',
    'gold': 'золотой',
    'silver': 'серебряный'
}

# Контекст пользователя для хранения текущего режима
user_context = {}

def convert_colors_to_russian(colors):
    """Преобразует названия цветов на русский язык"""
    russian_colors = []
    for color in colors:
        color_lower = color.lower()
        if color_lower in EN_TO_RU_COLORS:
            russian_colors.append(EN_TO_RU_COLORS[color_lower])
        else:
            # Если цвет уже на русском, оставляем как есть
            russian_colors.append(color)
    return russian_colors

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    user_context[user_id] = 'main'  # Сбрасываем контекст
    
    welcome_text = """
🤖 *Resistor Bot* - универсальный помощник по резисторам

*Доступные функции:*

🎨 *Цилиндрические резисторы:*
  • Определение номинала по цветам
  • Получение цветовой маркировки по номиналу
  • Распознавание по фото

🔤 *SMD резисторы:*
  • Расшифровка кода в номинал
  • Генерация кода по номиналу
  • Поддержка E24, E96 серий

📷 *Распознавание по фото:*
  • Цилиндрические резисторы (цветные полосы)
  • SMD резисторы (текстовые коды)

*Примеры команд:*
`/throughhole` - работа с цилиндрическими резисторами
`/smd` - работа с SMD резисторами  
`/photo` - распознавание по фото
    """
    
    keyboard = [
        [InlineKeyboardButton("🎨 Цилиндрические", callback_data="throughhole")],
        [InlineKeyboardButton("🔤 SMD резисторы", callback_data="smd")],
        [InlineKeyboardButton("📷 Распознавание фото", callback_data="photo")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "throughhole":
        user_context[user_id] = 'throughhole'
        text = """
🎨 *Режим: Цилиндрические резисторы*

Теперь отправьте:
• Цвета полос для определения номинала
• Номинал для получения цветовой маркировки

*Примеры:*
`красный фиолетовый желтый золотой`
`1.5к` 
`470 Ом`
`2.2М`
        """
        
    elif query.data == "smd":
        user_context[user_id] = 'smd'
        text = """
🔤 *Режим: SMD резисторы*

Теперь отправьте:
• SMD код для расшифровки
• Номинал для генерации кода

*Примеры кодов:*
`103` = 10 кОм
`4R7` = 4.7 Ом  
`01C` = 10 кОм (E96)
`R047` = 0.047 Ом

*Примеры номиналов:*
`10к`, `4.7 Ом`, `100к`, `0.47`
        """
        
    elif query.data == "photo":
        user_context[user_id] = 'photo'
        text = """
📷 *Режим: Распознавание по фото*

Отправьте фото:
• Цилиндрического резистора (цветные полосы)
• SMD резистора (текстовый код)

*Советы для лучшего распознавания:*
• Хорошее освещение
• Четкий фокус
• Контрастный фон
• Прямой угол съемки

Бот автоматически определит тип резистора.
        """
        
    elif query.data == "help":
        user_context[user_id] = 'main'
        text = """
ℹ️ *Помощь по использованию*

*Основные команды:*
`/start` - начать работу
`/throughhole` - цилиндрические резисторы  
`/smd` - SMD резисторы
`/photo` - распознавание фото

*Примеры запросов:*
Цвета → Номинал: `коричневый черный красный золотой`
Номинал → Цвета: `1к`, `470 Ом`
SMD код → Номинал: `103`, `4R7`
Номинал → SMD код: `10к`, `4.7 Ом`

*Распознавание по фото:*
Отправьте четкое фото резистора. Для лучшего результата:
• Используйте хорошее освещение
• Контрастный фон
• Четко видимые цветные полосы или текст
        """
    
    elif query.data == "back":
        # Возврат к главному меню
        user_context[user_id] = 'main'
        welcome_text = """
🤖 *Resistor Bot* - универсальный помощник по резисторам

Выберите нужный режим работы:
        """
        keyboard = [
            [InlineKeyboardButton("🎨 Цилиндрические", callback_data="throughhole")],
            [InlineKeyboardButton("🔤 SMD резисторы", callback_data="smd")],
            [InlineKeyboardButton("📷 Распознавание фото", callback_data="photo")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=welcome_text, 
            parse_mode='Markdown', 
            reply_markup=reply_markup
        )
        return
    
    else:
        # Неизвестная команда - возвращаем в главное меню
        user_context[user_id] = 'main'
        await start(update, context)
        return
    
    # Для всех остальных случаев показываем кнопку "Назад"
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text, 
        parse_mode='Markdown', 
        reply_markup=reply_markup
    )

async def throughhole_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для работы с цилиндрическими резисторами"""
    user_id = update.effective_user.id
    user_context[user_id] = 'throughhole'
    
    help_text = """
🎨 *Режим: Цилиндрические резисторы*

Теперь отправьте:
• Цвета полос для определения номинала
• Номинал для получения цветовой маркировки

*Примеры:*
`красный фиолетовый желтый золотой`
`1.5к` 
`470 Ом`
`2.2М`
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def smd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для работы с SMD резисторами"""
    user_id = update.effective_user.id
    user_context[user_id] = 'smd'
    
    help_text = """
🔤 *Режим: SMD резисторы*

Теперь отправьте:
• SMD код для расшифровки
• Номинал для генерации кода

*Примеры кодов:*
`103` = 10 кОм
`4R7` = 4.7 Ом  
`01C` = 10 кОм (E96)
`R047` = 0.047 Ом

*Примеры номиналов:*
`10к`, `4.7 Ом`, `100к`, `0.47`
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для распознавания по фото"""
    user_id = update.effective_user.id
    user_context[user_id] = 'photo'
    
    help_text = """
📷 *Режим: Распознавание по фото*

Отправьте фото:
• Цилиндрического резистора (цветные полосы)
• SMD резистора (текстовый код)

*Советы для лучшего распознавания:*
• Хорошее освещение
• Четкий фокус
• Контрастный фон
• Прямой угол съемки

Бот автоматически определит тип резистора.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user_id = update.effective_user.id
    user_context[user_id] = 'main'
    
    help_text = """
📖 *Справка по использованию*

*Основные команды:*
`/start` - начать работу
`/throughhole` - цилиндрические резисторы  
`/smd` - SMD резисторы
`/photo` - распознавание фото

*Примеры запросов:*
Цвета → Номинал: `коричневый черный красный золотой`
Номинал → Цвета: `1к`, `470 Ом`
SMD код → Номинал: `103`, `4R7`
Номинал → SMD код: `10к`, `4.7 Ом`

*Распознавание по фото:*
Отправьте четкое фото резистора. Для лучшего результата:
• Используйте хорошее освещение
• Контрастный фон
• Четко видимые цветные полосы или текст
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

def colors_to_resistance(colors):
    """Преобразование цветов в номинал резистора"""
    try:
        colors = [color.lower() for color in colors]
        
        if len(colors) == 4:  # 4-полосная маркировка
            digit1 = COLOR_CODES[colors[0]]
            digit2 = COLOR_CODES[colors[1]]
            multiplier = MULTIPLIERS[colors[2]]
            tolerance = TOLERANCE.get(colors[3], '±20%')
            
            resistance = (digit1 * 10 + digit2) * multiplier
            
        elif len(colors) == 5:  # 5-полосная маркировка
            digit1 = COLOR_CODES[colors[0]]
            digit2 = COLOR_CODES[colors[1]]
            digit3 = COLOR_CODES[colors[2]]
            multiplier = MULTIPLIERS[colors[3]]
            tolerance = TOLERANCE.get(colors[4], '±20%')
            
            resistance = (digit1 * 100 + digit2 * 10 + digit3) * multiplier
            
        else:
            return None, "Неверное количество цветов. Используйте 4 или 5 цветов."
        
        # Форматирование результата
        if resistance >= 1000000:
            result = f"{resistance / 1000000:.2f} МОм"
        elif resistance >= 1000:
            result = f"{resistance / 1000:.2f} кОм"
        else:
            result = f"{resistance:.0f} Ом"
            
        return result, tolerance
        
    except Exception as e:
        return None, f"Ошибка: {str(e)}. Проверьте правильность ввода цветов."

def resistance_to_colors(resistance_str):
    """Преобразование номинала в цветовую маркировку"""
    try:
        # Парсим входную строку
        match = re.search(r'(\d+\.?\d*)\s*([кмkKmM]?)\s*[оОoOmM]?', resistance_str)
        if not match:
            return None, "Неверный формат. Пример: '1к', '470 Ом', '2.2М'"
        
        value, unit = match.groups()
        value = float(value)
        
        # Конвертируем в Омы
        if unit and unit.lower() in ['к', 'k']:
            value *= 1000
        elif unit and unit.lower() in ['м', 'm']:
            value *= 1000000
        
        resistance = int(value)
        
        # Определяем тип маркировки (4 или 5 полос)
        if resistance < 100:
            # 4-полосная маркировка
            digit1 = resistance // 10
            digit2 = resistance % 10
            digits = [digit1, digit2]
            num_bands = 4
        else:
            # 5-полосная маркировка для большей точности
            digits = []
            temp = resistance
            while temp > 0 and len(digits) < 3:
                digits.insert(0, temp % 10)
                temp //= 10
            while len(digits) < 3:
                digits.insert(0, 0)
            num_bands = 5
        
        # Находим множитель
        multiplier_exp = len(str(resistance)) - len(digits)
        multiplier_value = 10 ** multiplier_exp
        
        # Ищем цвета (используем русские названия)
        reverse_color_map = {v: k for k, v in COLOR_CODES.items() if v >= 0 and k in ['черный', 'коричневый', 'красный', 'оранжевый', 'желтый', 'зеленый', 'синий', 'фиолетовый', 'серый', 'белый']}
        reverse_multiplier_map = {v: k for k, v in MULTIPLIERS.items() if k in ['черный', 'коричневый', 'красный', 'оранжевый', 'желтый', 'зеленый', 'синий', 'фиолетовый', 'серый', 'белый', 'золотой', 'серебряный']}
        
        colors = []
        for digit in digits[:2] if num_bands == 4 else digits[:3]:
            color = reverse_color_map.get(digit)
            if color:
                colors.append(color)
        
        # Цвет множителя
        multiplier_color = reverse_multiplier_map.get(multiplier_value)
        if not multiplier_color:
            # Находим ближайший
            possible_multipliers = [(abs(k - multiplier_value), v) for k, v in MULTIPLIERS.items() if k not in [0.1, 0.01] and k in ['черный', 'коричневый', 'красный', 'оранжевый', 'желтый', 'зеленый', 'синий', 'фиолетовый', 'серый', 'белый']]
            possible_multipliers.sort()
            multiplier_color = possible_multipliers[0][1] if possible_multipliers else 'черный'
        
        colors.append(multiplier_color)
        colors.append('золотой')  # Допуск по умолчанию
        
        return colors, num_bands
        
    except Exception as e:
        return None, f"Ошибка: {str(e)}"

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Получаем текущий контекст пользователя
    current_context = user_context.get(user_id, 'main')
    
    # Определяем тип запроса на основе контекста и содержимого
    words = text.lower().split()
    
    # Если явно указаны цвета - обрабатываем как цвета независимо от контекста
    if words and all(word in COLOR_CODES for word in words):
        # Запрос с цветами - цилиндрический резистор
        resistance, tolerance = colors_to_resistance(words)
        if resistance:
            response = f"🎯 *Номинал резистора:* {resistance}\n📊 *Допуск:* {tolerance}"
        else:
            response = tolerance
            
    # Если явно указан SMD код - обрабатываем как SMD независимо от контекста
    elif validate_smd_code(text):
        # SMD код
        result = smd_to_resistance(text)
        if result:
            value, code_type = result
            response = f"🔤 *SMD код:* `{text.upper()}`\n💎 *Номинал:* {value}\n📋 *Тип:* {code_type}"
        else:
            response = f"❌ Не удалось расшифровать SMD код: `{text}`"
            
    # Если контекст явно указан - используем его
    elif current_context == 'throughhole':
        # В контексте цилиндрических резисторов - пробуем как номинал для цветовой маркировки
        colors, num_bands = resistance_to_colors(text)
        if colors:
            # Преобразуем цвета в русские названия
            russian_colors = convert_colors_to_russian(colors)
            colors_str = ' → '.join(russian_colors)
            band_type = "4-полосной" if num_bands == 4 else "5-полосной"
            response = f"🎨 *Цветовая маркировка* ({band_type}):\n`{colors_str}`"
        else:
            response = ("❌ Не удалось распознать номинал для цветовой маркировки.\n\n"
                      "Примеры:\n"
                      "• `1к` → 1000 Ом\n"
                      "• `470 Ом` → 470 Ом\n"
                      "• `2.2М` → 2.2 МОм")
            
    elif current_context == 'smd':
        # В контексте SMD резисторов - пробуем как номинал для SMD кода
        smd_result = resistance_to_smd(text)
        if smd_result and "Не удалось" not in smd_result and "Ошибка" not in smd_result:
            if isinstance(smd_result, tuple) and len(smd_result) == 3:
                value, codes, series = smd_result
                codes_str = "\n".join([f"• `{code}` ({s})" for code, s in zip(codes, series)])
                response = f"💎 *Номинал:* {value}\n🔤 *SMD коды:*\n{codes_str}"
            else:
                response = f"💎 {smd_result}"
        else:
            response = ("❌ Не удалось сгенерировать SMD код.\n\n"
                      "Примеры:\n"
                      "• `10к` → 103, 01C\n"
                      "• `4.7 Ом` → 4R7\n"
                      "• `100к` → 104, 01D")
    
    else:
        # Автоматическое определение в главном меню
        # Сначала пробуем как SMD
        smd_result = resistance_to_smd(text)
        if smd_result and "Не удалось" not in smd_result and "Ошибка" not in smd_result:
            if isinstance(smd_result, tuple) and len(smd_result) == 3:
                value, codes, series = smd_result
                codes_str = "\n".join([f"• `{code}` ({s})" for code, s in zip(codes, series)])
                response = f"💎 *Номинал:* {value}\n🔤 *SMD коды:*\n{codes_str}"
            else:
                response = f"💎 {smd_result}"
        else:
            # Пробуем как цилиндрический
            colors, num_bands = resistance_to_colors(text)
            if colors:
                # Преобразуем цвета в русские названия
                russian_colors = convert_colors_to_russian(colors)
                colors_str = ' → '.join(russian_colors)
                band_type = "4-полосной" if num_bands == 4 else "5-полосной"
                response = f"🎨 *Цветовая маркировка* ({band_type}):\n`{colors_str}`"
            else:
                response = ("❌ Не удалось распознать запрос.\n\n"
                          "Возможные варианты:\n"
                          "• Цвета полос: `красный фиолетовый желтый золотой`\n"
                          "• Номинал: `1к`, `470 Ом`\n"
                          "• SMD код: `103`, `4R7`\n\n"
                          "Используйте команды для выбора режима:\n"
                          "`/throughhole` - цилиндрические резисторы\n"
                          "`/smd` - SMD резисторы")
    
    await update.message.reply_text(response, parse_mode='Markdown')

def preprocess_image_for_ocr(image):
    """Предобработка изображения для OCR"""
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    # Увеличиваем контраст
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий с использованием CV и OCR"""
    try:
        await update.message.reply_text("🔍 Анализирую изображение...")
        
        # Получаем фото
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Конвертируем в numpy array для OpenCV
        nparr = np.frombuffer(photo_bytes, np.uint8)
        image_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Пытаемся распознать как цилиндрический резистор с помощью CV
        cv_result = recognize_resistor_cv(image_cv)
        
        if cv_result and "Не удалось" not in cv_result and "Ошибка" not in cv_result:
            response = f"📷 *Распознано (CV):*\n{cv_result}"
            await update.message.reply_text(response, parse_mode='Markdown')
            return
        
        # Если CV не сработало, пробуем OCR для SMD кодов
        await update.message.reply_text("👁️ Пробую распознать текст...")
        
        image_pil = Image.open(io.BytesIO(photo_bytes))
        processed_image = preprocess_image_for_ocr(image_pil)
        
        # Распознаем текст с оптимизацией для SMD кодов
        custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789RrMmKkFfABCDEFGHXYZabcxyz.-'
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        # Очищаем распознанный текст
        cleaned_text = re.sub(r'[^\w\.\-]', '', text.strip())
        
        if cleaned_text and len(cleaned_text) >= 2:
            # Пробуем распознать как SMD код
            if validate_smd_code(cleaned_text):
                result = smd_to_resistance(cleaned_text)
                if result:
                    value, code_type = result
                    response = (f"📷 *Распознано (OCR):*\n"
                              f"🔤 *SMD код:* `{cleaned_text.upper()}`\n"
                              f"💎 *Номинал:* {value}\n"
                              f"📋 *Тип:* {code_type}")
                else:
                    response = f"📷 Распознан текст: `{cleaned_text}`\nНо не удалось определить SMD код."
            else:
                # Пробуем распознать как обычный номинал
                colors, num_bands = resistance_to_colors(cleaned_text)
                if colors:
                    # Преобразуем цвета в русские названия
                    russian_colors = convert_colors_to_russian(colors)
                    colors_str = ' → '.join(russian_colors)
                    band_type = "4-полосной" if num_bands == 4 else "5-полосной"
                    response = (f"📷 *Распознано:* `{cleaned_text}`\n"
                              f"🎨 *Цветовая маркировка* ({band_type}):\n`{colors_str}`")
                else:
                    response = f"📷 Распознан текст: `{cleaned_text}`\nНе удалось определить номинал резистора."
        else:
            response = ("❌ Не удалось распознать резистор на изображении.\n\n"
                       "*Советы:*\n• Убедитесь, что полосы или код четко видны\n"
                       "• Используйте хорошее освещение\n• Сфотографируйте на контрастном фоне")
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Ошибка обработки изображения: {e}")
        await update.message.reply_text(f"❌ Ошибка обработки изображения: {str(e)}")

def main():
    """Основная функция"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("throughhole", throughhole_command))
        application.add_handler(CommandHandler("smd", smd_command))
        application.add_handler(CommandHandler("photo", photo_command))
        application.add_handler(CommandHandler("help", help_command))
        
        # Обработчики кнопок
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Обработчики сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        # Запуск бота
        logging.info("🤖 Бот запущен с поддержкой SMD резисторов!")
        print("=" * 50)
        print("🤖 Resistor Bot успешно запущен!")
        print("📍 Используйте /start в Telegram")
        print("🔧 Для остановки нажмите Ctrl+C")
        print("=" * 50)
        
        application.run_polling()
        
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")
        exit(1)

if __name__ == '__main__':
    main()