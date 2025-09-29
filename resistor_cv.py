import cv2
import numpy as np

# Диапазоны цветов в HSV для обнаружения полос резисторов
Colour_Range = [
    [(0, 0, 0), (180, 255, 30), "BLACK", 0, (0, 0, 0)],
    [(0, 50, 10), (15, 255, 100), "BROWN", 1, (0, 51, 102)],
    [(0, 100, 50), (10, 255, 255), "RED", 2, (0, 0, 255)],
    [(5, 100, 100), (15, 255, 255), "ORANGE", 3, (0, 128, 255)],
    [(20, 100, 100), (30, 255, 255), "YELLOW", 4, (0, 255, 255)],
    [(35, 50, 50), (85, 255, 255), "GREEN", 5, (0, 255, 0)],
    [(100, 100, 50), (130, 255, 255), "BLUE", 6, (255, 0, 0)],
    [(130, 50, 50), (160, 255, 255), "VIOLET", 7, (255, 0, 127)],
    [(0, 0, 40), (180, 50, 100), "GRAY", 8, (128, 128, 128)],
    [(0, 0, 200), (180, 30, 255), "WHITE", 9, (255, 255, 255)],
    [(15, 50, 50), (25, 255, 255), "GOLD", -1, (0, 215, 255)],
    [(0, 0, 150), (180, 30, 200), "SILVER", -2, (192, 192, 192)]
]

# Дополнительный диапазон для красного (т.к. красный в HSV пересекает 0)
Red_low2 = (170, 100, 50)
Red_high2 = (180, 255, 255)

# Минимальная площадь контура
min_area = 100

def preprocess_resistor_image(img):
    """Предобработка изображения резистора"""
    # Увеличиваем резкость
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    img = cv2.filter2D(img, -1, kernel)
    
    # Билинейная фильтрация для уменьшения шума
    img = cv2.bilateralFilter(img, 9, 75, 75)
    
    return img

def validContours(cont):
    """Проверка валидности контуров"""
    if cv2.contourArea(cont) < min_area:
        return False
    
    x, y, w, h = cv2.boundingRect(cont)
    aspect_ratio = float(w) / h
    
    # Фильтруем слишком широкие или слишком узкие контуры
    if aspect_ratio > 3.0 or aspect_ratio < 0.1:
        return False
        
    return True

def findBands(img):
    """Поиск цветных полос на резисторе"""
    img_processed = preprocess_resistor_image(img)
    img_hsv = cv2.cvtColor(img_processed, cv2.COLOR_BGR2HSV)
    img_gray = cv2.cvtColor(img_processed, cv2.COLOR_BGR2GRAY)
    
    # Адаптивная threshold для выделения областей
    thresh = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    thresh = cv2.bitwise_not(thresh)
    
    bandpos = []

    for clr in Colour_Range:
        mask = cv2.inRange(img_hsv, np.array(clr[0]), np.array(clr[1]))
        
        # Особенная обработка для красного цвета
        if clr[2] == "RED":
            red_mask2 = cv2.inRange(img_hsv, np.array(Red_low2), np.array(Red_high2))
            mask = cv2.bitwise_or(mask, red_mask2)
        
        # Применяем маску к threshold
        mask = cv2.bitwise_and(mask, thresh)
        
        # Морфологические операции для улучшения контуров
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cont in contours:
            if validContours(cont):
                # Находим самую левую точку контура
                leftmost = tuple(cont[cont[:,:,0].argmin()][0])
                bandpos.append(leftmost + (clr[2], clr[3]))
    
    # Сортируем полосы по X координате (слева направо)
    return sorted(bandpos, key=lambda x: x[0])

def calculate_resistance_from_bands(bands):
    """Вычисление номинала резистора из найденных полос"""
    if not bands or len(bands) < 3:
        return None
    
    # Определяем тип маркировки по количеству полос
    num_bands = len(bands)
    
    try:
        if num_bands in [3, 4]:
            # 4-полосная маркировка: цифра, цифра, множитель, допуск
            digits = [band[3] for band in bands[:2]]
            multiplier = bands[2][3]
            
            # Если множитель отрицательный (золотой/серебряный), обрабатываем особо
            if multiplier < 0:
                if multiplier == -1:  # золотой
                    multiplier_val = 0.1
                else:  # серебряный
                    multiplier_val = 0.01
            else:
                multiplier_val = 10 ** multiplier
                
            resistance = (digits[0] * 10 + digits[1]) * multiplier_val
            
        elif num_bands >= 5:
            # 5-полосная маркировка: цифра, цифра, цифра, множитель, допуск
            digits = [band[3] for band in bands[:3]]
            multiplier = bands[3][3]
            
            if multiplier < 0:
                if multiplier == -1:
                    multiplier_val = 0.1
                else:
                    multiplier_val = 0.01
            else:
                multiplier_val = 10 ** multiplier
                
            resistance = (digits[0] * 100 + digits[1] * 10 + digits[2]) * multiplier_val
        
        else:
            return None
            
        return resistance
        
    except Exception as e:
        print(f"Ошибка расчета: {e}")
        return None

def format_resistance(value):
    """Форматирование значения сопротивления"""
    if value is None:
        return None
        
    if value >= 1000000:
        return f"{value / 1000000:.2f} МОм"
    elif value >= 1000:
        return f"{value / 1000:.2f} кОм"
    elif value < 1:
        return f"{value:.2f} Ом"
    else:
        return f"{int(value)} Ом"

def recognize_resistor_cv(image):
    """Основная функция распознавания резистора через компьютерное зрение"""
    try:
        bands = findBands(image)
        
        if not bands:
            return "Не удалось обнаружить цветные полосы"
        
        resistance_value = calculate_resistance_from_bands(bands)
        
        if resistance_value is None:
            return f"Обнаружено {len(bands)} полос, но не удалось вычислить номинал"
        
        formatted_value = format_resistance(resistance_value)
        bands_info = " → ".join([band[2] for band in bands[:4]])
        
        return f"🎯 *Номинал:* {formatted_value}\n🎨 *Полосы:* {bands_info}\n*Метод:* Компьютерное зрение"
        
    except Exception as e:
        return f"Ошибка распознавания: {str(e)}"

# Функция для тестирования
if __name__ == '__main__':
    # Тестирование на локальном изображении
    test_image = cv2.imread('test_resistor.jpg')
    if test_image is not None:
        result = recognize_resistor_cv(test_image)
        print(result)
    else:
        print("Тестовое изображение не найдено")