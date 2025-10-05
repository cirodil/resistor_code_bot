import logging
import re
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.getenv('BOT_LOG_LEVEL', 'INFO')
)

# Проверка обязательных переменных
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("❌ BOT_TOKEN not found in environment variables!")
    exit(1)

# Импортируем данные и функции из наших модулей
try:
    from resistor_data import COLOR_CODES, MULTIPLIERS, TOLERANCE, EN_TO_RU_COLORS, INPUT_NORMALIZATION, RU_TO_EN_COLORS
    from smd_decoder import smd_to_resistance, resistance_to_smd, validate_smd_code
except ImportError as e:
    logging.error(f"❌ Error importing modules: {e}")
    # Создаем заглушки для тестирования
    COLOR_CODES, MULTIPLIERS, TOLERANCE, EN_TO_RU_COLORS, INPUT_NORMALIZATION, RU_TO_EN_COLORS = {}, {}, {}, {}, {}, {}
    def smd_to_resistance(code):
        return None
    def resistance_to_smd(value):
        return "SMD module not available"
    def validate_smd_code(code):
        return False

# Контекст пользователя для хранения текущего режима и языка
user_context = {}

# Создаем постоянную клавиатуру
def get_main_keyboard(language='ru'):
    """Возвращает основную клавиатуру"""
    if language == 'en':
        keyboard = [
            [KeyboardButton("🎨 Cylindrical"), KeyboardButton("🔤 SMD Resistors")],
            [KeyboardButton("🌐 Language"), KeyboardButton("ℹ️ Help"), KeyboardButton("🏠 Main Menu")]
        ]
    else:
        keyboard = [
            [KeyboardButton("🎨 Цилиндрические"), KeyboardButton("🔤 SMD резисторы")],
            [KeyboardButton("🌐 Язык"), KeyboardButton("ℹ️ Помощь"), KeyboardButton("🏠 Главное меню")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_language_keyboard():
    """Клавиатура выбора языка"""
    keyboard = [
        [KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇺🇸 English")],
        [KeyboardButton("🔙 Back")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def normalize_color_input(color):
    """Нормализует ввод цвета, приводя к стандартному виду"""
    # Приводим к нижнему регистру и убираем пробелы
    color_lower = color.lower().strip()
    
    # Заменяем букву 'ё' на 'е' для единообразия
    color_lower = color_lower.replace('ё', 'е')
    
    # Приводим к стандартному варианту написания
    normalized = INPUT_NORMALIZATION.get(color_lower, color_lower)
    
    # Также заменяем 'ё' на 'е' в нормализованном результате
    normalized = normalized.replace('ё', 'е')
    
    return normalized

def convert_colors_to_target_language(colors, target_language='ru'):
    """Преобразует названия цветов на указанный язык"""
    converted_colors = []
    for color in colors:
        color_lower = color.lower()
        if target_language == 'en' and color_lower in RU_TO_EN_COLORS:
            converted_colors.append(RU_TO_EN_COLORS[color_lower])
        elif target_language == 'ru' and color_lower in EN_TO_RU_COLORS:
            converted_colors.append(EN_TO_RU_COLORS[color_lower])
        else:
            # Если цвет уже на нужном языке, оставляем как есть
            converted_colors.append(color)
    return converted_colors

def get_user_language(user_id):
    """Получает язык пользователя"""
    return user_context.get(user_id, {}).get('language', 'ru')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    if user_id not in user_context:
        user_context[user_id] = {'mode': 'main', 'language': 'ru'}
    else:
        user_context[user_id]['mode'] = 'main'
    
    language = get_user_language(user_id)
    
    if language == 'en':
        welcome_text = """
🤖 *Resistor Code Bot* - Universal resistor assistant

*Available features:*

🎨 *Cylindrical Resistors:*
  • Determine value by colors
  • Get color coding by value (4 and 5 bands)

🔤 *SMD Resistors:*
  • Decode code to value
  • Generate code by value
  • Support for E24, E96 series

*Just send:*
• Band colors (4 or 5 colors) - e.g.: `yellow violet red gold`
• Resistor value (1k, 470 Ohm, 2.2M)
• SMD code (103, 4R7, 01C)

*Use buttons below for navigation:*
        """
    else:
        welcome_text = """
🤖 *Resistor Code Bot* - универсальный помощник по резисторам

*Доступные функции:*

🎨 *Цилиндрические резисторы:*
  • Определение номинала по цветам
  • Получение цветовой маркировки по номиналу (4 и 5 полос)

🔤 *SMD резисторы:*
  • Расшифровка кода в номинал
  • Генерация кода по номиналу
  • Поддержка E24, E96 серий

*Просто отправьте:*
• Цвета полос (4 или 5 цветов) - например: `жёлтый фиолетовый красный золотой`
• Номинал резистора (1к, 470 Ом, 2.2М)
• SMD код (103, 4R7, 01C)

*Используйте кнопки ниже для навигации:*
        """
    
    await update.message.reply_text(
        welcome_text, 
        parse_mode='Markdown', 
        reply_markup=get_main_keyboard(language)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user_id = update.effective_user.id
    user_context[user_id]['mode'] = 'main'
    
    language = get_user_language(user_id)
    
    if language == 'en':
        help_text = """
📖 *Usage Help*

*Basic commands:*
`/start` - start working
`/help` - show this help

*Request examples:*

*Cylindrical Resistors:*
Colors → Value: `brown black red gold`
Value → Colors: `1k`, `470 Ohm`

*SMD Resistors:*
SMD code → Value: `103`, `4R7`
Value → SMD code: `10k`, `4.7 Ohm`

*Tips:*
• Bot automatically detects your request type
• Use buttons to select mode
• Both Russian and English color names are supported
• Both 4-band and 5-band markings are shown
        """
    else:
        help_text = """
📖 *Справка по использованию*

*Основные команды:*
`/start` - начать работу
`/help` - показать эту справку

*Примеры запросов:*

*Цилиндрические резисторы:*
Цвета → Номинал: `коричневый чёрный красный золотой`
Номинал → Цвета: `1к`, `470 Ом`

*SMD резисторы:*
SMD код → Номинал: `103`, `4R7`
Номинал → SMD код: `10к`, `4.7 Ом`

*Подсказки:*
• Бот автоматически определит тип вашего запроса
• Используйте кнопки для выбора режима
• Поддерживаются русские и английские названия цветов
• Для номиналов показываются обе маркировки: 4-полосная и 5-полосная
        """
    await update.message.reply_text(help_text, parse_mode='Markdown', 
                                  reply_markup=get_main_keyboard(language))

async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий кнопок меню"""
    user_id = update.effective_user.id
    text = update.message.text
    language = get_user_language(user_id)
    
    if text in ["🎨 Цилиндрические", "🎨 Cylindrical"]:
        user_context[user_id]['mode'] = 'throughhole'
        if language == 'en':
            help_text = """
🎨 *Mode: Cylindrical Resistors*

Now send:
• Band colors to determine value
• Value to get color coding

*Color examples:*
`red violet yellow gold`
`brown black red silver`

*Value examples:*
`1.5k` 
`470 Ohm`
`2.2M`

*Bot will show both markings:*
• 4-band (2 digits, multiplier, tolerance)
• 5-band (3 digits, multiplier, tolerance)
            """
        else:
            help_text = """
🎨 *Режим: Цилиндрические резисторы*

Теперь отправьте:
• Цвета полос для определения номинала
• Номинал для получения цветовой маркировки

*Примеры цветов:*
`красный фиолетовый жёлтый золотой`
`коричневый чёрный красный серебряный`

*Примеры номиналов:*
`1.5к` 
`470 Ом`
`2.2М`

*Бот покажет обе маркировки:*
• 4-полосная (2 цифры, множитель, допуск)
• 5-полосная (3 цифры, множитель, допуск)
            """
        await update.message.reply_text(help_text, parse_mode='Markdown', 
                                      reply_markup=get_main_keyboard(language))
        
    elif text in ["🔤 SMD резисторы", "🔤 SMD Resistors"]:
        user_context[user_id]['mode'] = 'smd'
        if language == 'en':
            help_text = """
🔤 *Mode: SMD Resistors*

Now send:
• SMD code to decode
• Value to generate code

*Code examples:*
`103` = 10 kOhm
`4R7` = 4.7 Ohm  
`01C` = 10 kOhm (E96)
`R047` = 0.047 Ohm

*Value examples:*
`10k`, `4.7 Ohm`, `100k`, `0.47`

*Supported formats:*
• 3-digit code (E24 series)
• 4-digit code (E96 series)  
• R-codes (less than 100 Ohm)
            """
        else:
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

*Поддерживаемые форматы:*
• 3-значный код (E24 серия)
• 4-значный код (E96 серия)  
• Коды с R (меньше 100 Ом)
            """
        await update.message.reply_text(help_text, parse_mode='Markdown', 
                                      reply_markup=get_main_keyboard(language))
        
    elif text in ["ℹ️ Помощь", "ℹ️ Help"]:
        await help_command(update, context)
        
    elif text in ["🏠 Главное меню", "🏠 Main Menu"]:
        user_context[user_id]['mode'] = 'main'
        if language == 'en':
            welcome_text = """
🏠 *Main Menu*

Select operation mode or just send a request:

*Request examples:*
• Colors: `brown black red gold`
• Value: `1k`, `470 Ohm`  
• SMD code: `103`, `4R7`

Bot automatically detects your request type!

*Both Russian and English color names are supported*
            """
        else:
            welcome_text = """
🏠 *Главное меню*

Выберите режим работы или просто отправьте запрос:

*Примеры запросов:*
• Цвета: `коричневый чёрный красный золотой`
• Номинал: `1к`, `470 Ом`  
• SMD код: `103`, `4R7`

Бот автоматически определит тип вашего запроса!

*Поддерживаются русские и английские названия цветов*
            """
        await update.message.reply_text(welcome_text, parse_mode='Markdown', 
                                      reply_markup=get_main_keyboard(language))
    
    elif text in ["🌐 Язык", "🌐 Language"]:
        user_context[user_id]['mode'] = 'language'
        if language == 'en':
            text = "🌐 *Select Language*"
        else:
            text = "🌐 *Выберите язык*"
        await update.message.reply_text(text, parse_mode='Markdown', 
                                      reply_markup=get_language_keyboard())
    
    elif text == "🇷🇺 Русский":
        user_context[user_id]['language'] = 'ru'
        user_context[user_id]['mode'] = 'main'
        await update.message.reply_text("✅ Язык изменен на Русский", 
                                      reply_markup=get_main_keyboard('ru'))
    
    elif text == "🇺🇸 English":
        user_context[user_id]['language'] = 'en'
        user_context[user_id]['mode'] = 'main'
        await update.message.reply_text("✅ Language changed to English", 
                                      reply_markup=get_main_keyboard('en'))
    
    elif text == "🔙 Back":
        user_context[user_id]['mode'] = 'main'
        await update.message.reply_text("🏠", 
                                      reply_markup=get_main_keyboard(language))

def colors_to_resistance(colors):
    """Преобразование цветов в номинал резистора"""
    try:
        # Нормализуем ввод цветов
        normalized_colors = [normalize_color_input(color) for color in colors]
        
        if len(normalized_colors) == 4:  # 4-полосная маркировка
            digit1 = COLOR_CODES[normalized_colors[0]]
            digit2 = COLOR_CODES[normalized_colors[1]]
            multiplier = MULTIPLIERS[normalized_colors[2]]
            tolerance = TOLERANCE.get(normalized_colors[3], '±20%')
            
            resistance = (digit1 * 10 + digit2) * multiplier
            
        elif len(normalized_colors) == 5:  # 5-полосная маркировка
            digit1 = COLOR_CODES[normalized_colors[0]]
            digit2 = COLOR_CODES[normalized_colors[1]]
            digit3 = COLOR_CODES[normalized_colors[2]]
            multiplier = MULTIPLIERS[normalized_colors[3]]
            tolerance = TOLERANCE.get(normalized_colors[4], '±20%')
            
            resistance = (digit1 * 100 + digit2 * 10 + digit3) * multiplier
            
        else:
            return None, "Invalid number of colors. Use 4 or 5 colors."
        
        # Форматирование результата
        if resistance >= 1000000:
            result = f"{resistance / 1000000:.2f} MOhm"
        elif resistance >= 1000:
            result = f"{resistance / 1000:.2f} kOhm"
        else:
            result = f"{resistance:.0f} Ohm"
            
        return result, tolerance
        
    except Exception as e:
        return None, f"Error: {str(e)}. Check color input correctness."

def resistance_to_colors(resistance_str):
    """Преобразование номинала в цветовую маркировку для 4 и 5 полос"""
    try:
        # Парсим входную строку (поддержка русского и английского)
        match = re.search(r'(\d+\.?\d*)\s*([кkKmM]?)\s*[оОoO]?[hmHM]?', resistance_str)
        if not match:
            return None, None, "Invalid format. Example: '1k', '470 Ohm', '2.2M'"
        
        value, unit = match.groups()
        value = float(value)
        
        # Конвертируем в Омы
        if unit and unit.lower() in ['к', 'k']:
            value *= 1000
        elif unit and unit.lower() in ['м', 'm']:
            value *= 1000000
        
        resistance = value
        
        # Создаем обратные словари для преобразования
        reverse_color_map = {v: k for k, v in COLOR_CODES.items() if v >= 0}
        reverse_multiplier_map = {v: k for k, v in MULTIPLIERS.items()}
        
        # Маркировка для 4 полос
        colors_4 = calculate_4_band_colors(resistance, reverse_color_map, reverse_multiplier_map)
        
        # Маркировка для 5 полос
        colors_5 = calculate_5_band_colors(resistance, reverse_color_map, reverse_multiplier_map)
        
        return colors_4, colors_5, None
        
    except Exception as e:
        return None, None, f"Error: {str(e)}"

def calculate_4_band_colors(resistance, reverse_color_map, reverse_multiplier_map):
    """Вычисляет цвета для 4-полосной маркировки"""
    try:
        if resistance < 0.1:
            return None  # Слишком маленькое сопротивление для 4-полосной маркировки
        
        # Находим подходящий множитель
        multiplier_value = 1
        value = resistance
        
        while value < 10 and multiplier_value > 0.01:
            multiplier_value /= 10
            value = resistance / multiplier_value
        
        while value >= 100 and multiplier_value < 1000000000:
            multiplier_value *= 10
            value = resistance / multiplier_value
        
        if value < 10 or value >= 100:
            return None
        
        # Округляем до целого
        value_int = int(round(value))
        
        # Получаем цифры
        digit1 = value_int // 10
        digit2 = value_int % 10
        
        # Получаем цвета
        color1 = reverse_color_map.get(digit1)
        color2 = reverse_color_map.get(digit2)
        color_multiplier = reverse_multiplier_map.get(multiplier_value, 'black')
        color_tolerance = 'gold'
        
        if color1 and color2 and color_multiplier:
            return [color1, color2, color_multiplier, color_tolerance]
        return None
        
    except Exception:
        return None

def calculate_5_band_colors(resistance, reverse_color_map, reverse_multiplier_map):
    """Вычисляет цвета для 5-полосной маркировки"""
    try:
        if resistance < 0.01:
            return None  # Слишком маленькое сопротивление для 5-полосной маркировки
        
        # Находим подходящий множитель
        multiplier_value = 1
        value = resistance
        
        while value < 100 and multiplier_value > 0.001:
            multiplier_value /= 10
            value = resistance / multiplier_value
        
        while value >= 1000 and multiplier_value < 100000000:
            multiplier_value *= 10
            value = resistance / multiplier_value
        
        if value < 100 or value >= 1000:
            return None
        
        # Округляем до целого
        value_int = int(round(value))
        
        # Получаем цифры
        digit1 = value_int // 100
        digit2 = (value_int // 10) % 10
        digit3 = value_int % 10
        
        # Получаем цвета
        color1 = reverse_color_map.get(digit1)
        color2 = reverse_color_map.get(digit2)
        color3 = reverse_color_map.get(digit3)
        color_multiplier = reverse_multiplier_map.get(multiplier_value, 'black')
        color_tolerance = 'brown'
        
        if color1 and color2 and color3 and color_multiplier:
            return [color1, color2, color3, color_multiplier, color_tolerance]
        return None
        
    except Exception:
        return None

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    language = get_user_language(user_id)
    
    # Если пользователь еще не инициализирован
    if user_id not in user_context:
        user_context[user_id] = {'mode': 'main', 'language': 'ru'}
    
    # Сначала проверяем, не является ли сообщение нажатием кнопки меню
    menu_buttons = ["🎨 Цилиндрические", "🔤 SMD резисторы", "ℹ️ Помощь", "🏠 Главное меню",
                   "🎨 Cylindrical", "🔤 SMD Resistors", "ℹ️ Help", "🏠 Main Menu",
                   "🌐 Язык", "🌐 Language", "🇷🇺 Русский", "🇺🇸 English", "🔙 Back"]
    
    if text in menu_buttons:
        await handle_menu_buttons(update, context)
        return
    
    # Получаем текущий контекст пользователя
    current_mode = user_context[user_id].get('mode', 'main')
    
    # Определяем тип запроса на основе контекста и содержимого
    words = text.split()
    
    # Нормализуем слова для проверки цветов
    normalized_words = [normalize_color_input(word) for word in words]
    
    # Если явно указаны цвета - обрабатываем как цвета независимо от контекста
    if normalized_words and all(word.lower() in COLOR_CODES for word in normalized_words):
        # Запрос с цветами - цилиндрический резистор
        resistance, tolerance = colors_to_resistance(words)
        if resistance:
            if language == 'en':
                response = f"🎯 *Resistor value:* {resistance}\n📊 *Tolerance:* {tolerance}"
            else:
                response = f"🎯 *Номинал резистора:* {resistance}\n📊 *Допуск:* {tolerance}"
        else:
            response = tolerance
            
    # Если явно указан SMD код - обрабатываем как SMD независимо от контекста
    elif validate_smd_code(text):
        # SMD код
        result = smd_to_resistance(text)
        if result:
            value, code_type = result
            if language == 'en':
                response = f"🔤 *SMD code:* `{text.upper()}`\n💎 *Value:* {value}\n📋 *Type:* {code_type}"
            else:
                response = f"🔤 *SMD код:* `{text.upper()}`\n💎 *Номинал:* {value}\n📋 *Тип:* {code_type}"
        else:
            if language == 'en':
                response = f"❌ Could not decode SMD code: `{text}`"
            else:
                response = f"❌ Не удалось расшифровать SMD код: `{text}`"
            
    # Если контекст явно указан - используем его
    elif current_mode == 'throughhole':
        # В контексте цилиндрических резисторов - пробуем как номинал для цветовой маркировки
        colors_4, colors_5, error = resistance_to_colors(text)
        if error:
            response = error
        elif colors_4 or colors_5:
            if language == 'en':
                response = "🎨 *Color coding:*\n\n"
            else:
                response = "🎨 *Цветовые маркировки:*\n\n"
            
            if colors_4:
                target_colors_4 = convert_colors_to_target_language(colors_4, language)
                colors_str_4 = ' → '.join(target_colors_4)
                if language == 'en':
                    response += f"*4-band:*\n`{colors_str_4}`\n\n"
                else:
                    response += f"*4-полосная:*\n`{colors_str_4}`\n\n"
            else:
                if language == 'en':
                    response += "*4-band:* not available for this value\n\n"
                else:
                    response += "*4-полосная:* не доступна для данного номинала\n\n"
                    
            if colors_5:
                target_colors_5 = convert_colors_to_target_language(colors_5, language)
                colors_str_5 = ' → '.join(target_colors_5)
                if language == 'en':
                    response += f"*5-band:*\n`{colors_str_5}`"
                else:
                    response += f"*5-полосная:*\n`{colors_str_5}`"
            else:
                if language == 'en':
                    response += "*5-band:* not available for this value"
                else:
                    response += "*5-полосная:* не доступна для данного номинала"
        else:
            if language == 'en':
                response = ("❌ Could not recognize value for color coding.\n\n"
                          "Examples:\n"
                          "• `1k` → 1000 Ohm\n"
                          "• `470 Ohm` → 470 Ohm\n"
                          "• `2.2M` → 2.2 MOhm")
            else:
                response = ("❌ Не удалось распознать номинал для цветовой маркировки.\n\n"
                          "Примеры:\n"
                          "• `1к` → 1000 Ом\n"
                          "• `470 Ом` → 470 Ом\n"
                          "• `2.2М` → 2.2 МОм")
            
    elif current_mode == 'smd':
        # В контексте SMD резисторов - пробуем как номинал для SMD кода
        smd_result = resistance_to_smd(text)
        if smd_result and "Could not" not in smd_result and "Error" not in smd_result and "Не удалось" not in smd_result and "Ошибка" not in smd_result:
            if isinstance(smd_result, tuple) and len(smd_result) == 3:
                value, codes, series = smd_result
                codes_str = "\n".join([f"• `{code}` ({s})" for code, s in zip(codes, series)])
                if language == 'en':
                    response = f"💎 *Value:* {value}\n🔤 *SMD codes:*\n{codes_str}"
                else:
                    response = f"💎 *Номинал:* {value}\n🔤 *SMD коды:*\n{codes_str}"
            else:
                response = f"💎 {smd_result}"
        else:
            if language == 'en':
                response = ("❌ Could not generate SMD code.\n\n"
                          "Examples:\n"
                          "• `10k` → 103, 01C\n"
                          "• `4.7 Ohm` → 4R7\n"
                          "• `100k` → 104, 01D")
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
        if smd_result and "Could not" not in smd_result and "Error" not in smd_result and "Не удалось" not in smd_result and "Ошибка" not in smd_result:
            if isinstance(smd_result, tuple) and len(smd_result) == 3:
                value, codes, series = smd_result
                codes_str = "\n".join([f"• `{code}` ({s})" for code, s in zip(codes, series)])
                if language == 'en':
                    response = f"💎 *Value:* {value}\n🔤 *SMD codes:*\n{codes_str}"
                else:
                    response = f"💎 *Номинал:* {value}\n🔤 *SMD коды:*\n{codes_str}"
            else:
                response = f"💎 {smd_result}"
        else:
            # Пробуем как цилиндрический
            colors_4, colors_5, error = resistance_to_colors(text)
            if error:
                response = error
            elif colors_4 or colors_5:
                if language == 'en':
                    response = "🎨 *Color coding:*\n\n"
                else:
                    response = "🎨 *Цветовые маркировки:*\n\n"
                
                if colors_4:
                    target_colors_4 = convert_colors_to_target_language(colors_4, language)
                    colors_str_4 = ' → '.join(target_colors_4)
                    if language == 'en':
                        response += f"*4-band:*\n`{colors_str_4}`\n\n"
                    else:
                        response += f"*4-полосная:*\n`{colors_str_4}`\n\n"
                else:
                    if language == 'en':
                        response += "*4-band:* not available for this value\n\n"
                    else:
                        response += "*4-полосная:* не доступна для данного номинала\n\n"
                        
                if colors_5:
                    target_colors_5 = convert_colors_to_target_language(colors_5, language)
                    colors_str_5 = ' → '.join(target_colors_5)
                    if language == 'en':
                        response += f"*5-band:*\n`{colors_str_5}`"
                    else:
                        response += f"*5-полосная:*\n`{colors_str_5}`"
                else:
                    if language == 'en':
                        response += "*5-band:* not available for this value"
                    else:
                        response += "*5-полосная:* не доступна для данного номинала"
            else:
                if language == 'en':
                    response = ("❌ Could not recognize request.\n\n"
                              "Possible options:\n"
                              "• Band colors: `red violet yellow gold`\n"
                              "• Value: `1k`, `470 Ohm`\n"
                              "• SMD code: `103`, `4R7`\n\n"
                              "Use buttons to select mode:")
                else:
                    response = ("❌ Не удалось распознать запрос.\n\n"
                              "Возможные варианты:\n"
                              "• Цвета полос: `красный фиолетовый жёлтый золотой`\n"
                              "• Номинал: `1к`, `470 Ом`\n"
                              "• SMD код: `103`, `4R7`\n\n"
                              "Используйте кнопки для выбора режима:")
    
    await update.message.reply_text(response, parse_mode='Markdown', 
                                  reply_markup=get_main_keyboard(language))

def main():
    """Основная функция"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        # Обработчик текстовых сообщений (включая кнопки меню)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # Запуск бота
        logging.info("🤖 Bot started with multilingual support!")
        print("=" * 50)
        print("🤖 Resistor Code Bot successfully started!")
        print("📍 Use /start in Telegram")
        print("🎯 Features: color coding + SMD codes")
        print("🌐 Multilingual support: Russian & English")
        print("🔧 Press Ctrl+C to stop")
        print("=" * 50)
        
        application.run_polling()
        
    except Exception as e:
        logging.error(f"❌ Critical error: {e}")
        exit(1)

if __name__ == '__main__':
    main()