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
    logging.error("❌ BOT_TOKEN не найден в переменных окружения!")
    exit(1)

# Импортируем данные и функции из наших модулей
try:
    from resistor_data import COLOR_CODES, MULTIPLIERS, TOLERANCE, EN_TO_RU_COLORS, INPUT_NORMALIZATION
    from smd_decoder import smd_to_resistance, resistance_to_smd, validate_smd_code
except ImportError as e:
    logging.error(f"❌ Ошибка импорта модулей: {e}")
    # Создаем заглушки для тестирования
    COLOR_CODES, MULTIPLIERS, TOLERANCE, EN_TO_RU_COLORS, INPUT_NORMALIZATION = {}, {}, {}, {}, {}
    def smd_to_resistance(code):
        return None
    def resistance_to_smd(value):
        return "Модуль SMD не доступен"
    def validate_smd_code(code):
        return False

# Контекст пользователя для хранения текущего режима
user_context = {}

# Создаем постоянную клавиатуру
def get_main_keyboard():
    """Возвращает основную клавиатуру"""
    keyboard = [
        [KeyboardButton("🎨 Цилиндрические"), KeyboardButton("🔤 SMD резисторы")],
        [KeyboardButton("ℹ️ Помощь"), KeyboardButton("🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def normalize_color_input(color):
    """Нормализует ввод цвета, приводя к стандартному виду"""
    color_lower = color.lower().strip()
    # Приводим к стандартному варианту написания
    return INPUT_NORMALIZATION.get(color_lower, color_lower)

def convert_colors_to_russian(colors):
    """Преобразует названия цветов на русский язык с правильными буквами 'ё'"""
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
    user_context[user_id] = 'main'
    
    welcome_text = """
🤖 *Resistor Bot* - универсальный помощник по резисторам

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
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user_id = update.effective_user.id
    user_context[user_id] = 'main'
    
    help_text = """
📖 *Справка по использованию*

*Основные команды:*
`/start` - начать работу
`/help` - показать эту справку

*Примеры запросов:*

*Цилиндрические резисторы:*
Цвета → Номинал: `коричневый чёрный красный золотой`
Номинал → Цвета: `1к`, `470 Ом` (покажет 4 и 5 полос)

*SMD резисторы:*
SMD код → Номинал: `103`, `4R7`
Номинал → SMD код: `10к`, `4.7 Ом`

*Подсказки:*
• Бот автоматически определит тип вашего запроса
• Используйте кнопки для выбора режима
• Все названия цветов выводятся с правильными буквами "ё"
• Для номиналов показываются обе маркировки: 4-полосная и 5-полосная
• Поддерживаются оба варианта написания: "жёлтый" и "желтый", "зелёный" и "зеленый"
    """
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий кнопок меню"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if text == "🎨 Цилиндрические":
        user_context[user_id] = 'throughhole'
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

*Примечание:*
Поддерживаются оба варианта написания: "жёлтый" и "желтый", "зелёный" и "зеленый"
        """
        await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        
    elif text == "🔤 SMD резисторы":
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

*Поддерживаемые форматы:*
• 3-значный код (E24 серия)
• 4-значный код (E96 серия)  
• Коды с R (меньше 100 Ом)
        """
        await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
        
    elif text == "🏠 Главное меню":
        user_context[user_id] = 'main'
        welcome_text = """
🏠 *Главное меню*

Выберите режим работы или просто отправьте запрос:

*Примеры запросов:*
• Цвета: `коричневый чёрный красный золотой`
• Номинал: `1к`, `470 Ом`  
• SMD код: `103`, `4R7`

Бот автоматически определит тип вашего запроса!

*Поддерживаются оба варианта написания:*
"жёлтый" и "желтый", "зелёный" и "зеленый"
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

def colors_to_resistance(colors):
    """Преобразование цветов в номинал резистора"""
    try:
        # Нормализуем ввод цветов
        normalized_colors = [normalize_color_input(color) for color in colors]
        colors_lower = [color.lower() for color in normalized_colors]
        
        if len(colors_lower) == 4:  # 4-полосная маркировка
            digit1 = COLOR_CODES[colors_lower[0]]
            digit2 = COLOR_CODES[colors_lower[1]]
            multiplier = MULTIPLIERS[colors_lower[2]]
            tolerance = TOLERANCE.get(colors_lower[3], '±20%')
            
            resistance = (digit1 * 10 + digit2) * multiplier
            
        elif len(colors_lower) == 5:  # 5-полосная маркировка
            digit1 = COLOR_CODES[colors_lower[0]]
            digit2 = COLOR_CODES[colors_lower[1]]
            digit3 = COLOR_CODES[colors_lower[2]]
            multiplier = MULTIPLIERS[colors_lower[3]]
            tolerance = TOLERANCE.get(colors_lower[4], '±20%')
            
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
    """Преобразование номинала в цветовую маркировку для 4 и 5 полос"""
    try:
        # Парсим входную строку
        match = re.search(r'(\d+\.?\d*)\s*([кмkKmM]?)\s*[оОoOmM]?', resistance_str)
        if not match:
            return None, None, "Неверный формат. Пример: '1к', '470 Ом', '2.2М'"
        
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
        return None, None, f"Ошибка: {str(e)}"

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
        color_multiplier = reverse_multiplier_map.get(multiplier_value, 'черный')
        color_tolerance = 'золотой'
        
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
        color_multiplier = reverse_multiplier_map.get(multiplier_value, 'черный')
        color_tolerance = 'коричневый'
        
        if color1 and color2 and color3 and color_multiplier:
            return [color1, color2, color3, color_multiplier, color_tolerance]
        return None
        
    except Exception:
        return None

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Сначала проверяем, не является ли сообщение нажатием кнопки меню
    if text in ["🎨 Цилиндрические", "🔤 SMD резисторы", "ℹ️ Помощь", "🏠 Главное меню"]:
        await handle_menu_buttons(update, context)
        return
    
    # Получаем текущий контекст пользователя
    current_context = user_context.get(user_id, 'main')
    
    # Определяем тип запроса на основе контекста и содержимого
    words = text.split()
    
    # Нормализуем слова для проверки цветов
    normalized_words = [normalize_color_input(word) for word in words]
    
    # Если явно указаны цвета - обрабатываем как цвета независимо от контекста
    if normalized_words and all(word.lower() in COLOR_CODES for word in normalized_words):
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
        colors_4, colors_5, error = resistance_to_colors(text)
        if error:
            response = error
        elif colors_4 or colors_5:
            response = "🎨 *Цветовые маркировки:*\n\n"
            
            if colors_4:
                russian_colors_4 = convert_colors_to_russian(colors_4)
                colors_str_4 = ' → '.join(russian_colors_4)
                response += f"*4-полосная:*\n`{colors_str_4}`\n\n"
            else:
                response += "*4-полосная:* не доступна для данного номинала\n\n"
                
            if colors_5:
                russian_colors_5 = convert_colors_to_russian(colors_5)
                colors_str_5 = ' → '.join(russian_colors_5)
                response += f"*5-полосная:*\n`{colors_str_5}`"
            else:
                response += "*5-полосная:* не доступна для данного номинала"
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
            colors_4, colors_5, error = resistance_to_colors(text)
            if error:
                response = error
            elif colors_4 or colors_5:
                response = "🎨 *Цветовые маркировки:*\n\n"
                
                if colors_4:
                    russian_colors_4 = convert_colors_to_russian(colors_4)
                    colors_str_4 = ' → '.join(russian_colors_4)
                    response += f"*4-полосная:*\n`{colors_str_4}`\n\n"
                else:
                    response += "*4-полосная:* не доступна для данного номинала\n\n"
                    
                if colors_5:
                    russian_colors_5 = convert_colors_to_russian(colors_5)
                    colors_str_5 = ' → '.join(russian_colors_5)
                    response += f"*5-полосная:*\n`{colors_str_5}`"
                else:
                    response += "*5-полосная:* не доступна для данного номинала"
            else:
                response = ("❌ Не удалось распознать запрос.\n\n"
                          "Возможные варианты:\n"
                          "• Цвета полос: `красный фиолетовый жёлтый золотой`\n"
                          "• Номинал: `1к`, `470 Ом`\n"
                          "• SMD код: `103`, `4R7`\n\n"
                          "Используйте кнопки для выбора режима:")
    
    await update.message.reply_text(response, parse_mode='Markdown', reply_markup=get_main_keyboard())

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
        logging.info("🤖 Бот запущен с поддержкой буквы 'ё'!")
        print("=" * 50)
        print("🤖 Resistor Bot успешно запущен!")
        print("📍 Используйте /start в Telegram")
        print("🎯 Функционал: цветовая маркировка + SMD коды")
        print("🔤 Поддержка буквы 'ё' в названиях цветов")
        print("🔧 Для остановки нажмите Ctrl+C")
        print("=" * 50)
        
        application.run_polling()
        
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")
        exit(1)

if __name__ == '__main__':
    main()