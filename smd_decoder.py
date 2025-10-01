import re
from resistor_data import E24_SERIES, E96_SERIES

# E96 multiplier codes (letters)
E96_MULTIPLIERS = {
    'Z': 0.001, 'Y': 0.01, 'X': 0.1, 'A': 1, 'B': 10, 'C': 100,
    'D': 1000, 'E': 10000, 'F': 100000
}

# E96 value codes (2-digit + letter)
E96_CODES = {
    '01': 100, '02': 102, '03': 105, '04': 107, '05': 110, '06': 113,
    '07': 115, '08': 118, '09': 121, '10': 124, '11': 127, '12': 130,
    '13': 133, '14': 137, '15': 140, '16': 143, '17': 147, '18': 150,
    '19': 154, '20': 158, '21': 162, '22': 165, '23': 169, '24': 174,
    '25': 178, '26': 182, '27': 187, '28': 191, '29': 196, '30': 200,
    '31': 205, '32': 210, '33': 215, '34': 221, '35': 226, '36': 232,
    '37': 237, '38': 243, '39': 249, '40': 255, '41': 261, '42': 267,
    '43': 274, '44': 280, '45': 287, '46': 294, '47': 301, '48': 309,
    '49': 316, '50': 324, '51': 332, '52': 340, '53': 348, '54': 357,
    '55': 365, '56': 374, '57': 383, '58': 392, '59': 402, '60': 412,
    '61': 422, '62': 432, '63': 442, '64': 453, '65': 464, '66': 475,
    '67': 487, '68': 499, '69': 511, '70': 523, '71': 536, '72': 549,
    '73': 562, '74': 576, '75': 590, '76': 604, '77': 619, '78': 634,
    '79': 649, '80': 665, '81': 681, '82': 698, '83': 715, '84': 732,
    '85': 750, '86': 768, '87': 787, '88': 806, '89': 825, '90': 845,
    '91': 866, '92': 887, '93': 909, '94': 931, '95': 953, '96': 976
}

def validate_smd_code(code):
    """Проверка валидности SMD кода"""
    if not code or len(code) < 2:
        return False
    
    code = code.upper().strip()
    
    # 3-digit code (E24)
    if re.match(r'^[0-9]{3}$', code):
        return True
    
    # 4-digit code (E96)
    if re.match(r'^[0-9]{2}[A-Z]$', code):
        return code[:2] in E96_CODES and code[2] in E96_MULTIPLIERS
    
    # Codes with R (resistance < 100 Ohm)
    if re.match(r'^[Rr][0-9\.]+$', code) or re.match(r'^[0-9\.]*[Rr][0-9]*$', code):
        return True
    
    # 4-digit with R (like R047)
    if re.match(r'^[Rr][0-9]{3}$', code):
        return True
    
    return False

def smd_to_resistance(code):
    """Преобразование SMD кода в значение сопротивления"""
    if not validate_smd_code(code):
        return None
    
    code = code.upper().strip()
    
    try:
        # 3-digit code (E24 series)
        if re.match(r'^[0-9]{3}$', code):
            significant = int(code[:2])
            multiplier = 10 ** int(code[2])
            resistance = significant * multiplier
            return format_resistance(resistance), "E24 (3-digit)"
        
        # 4-digit code with letter (E96 series)
        elif re.match(r'^[0-9]{2}[A-Z]$', code):
            value_code = code[:2]
            multiplier_code = code[2]
            
            if value_code in E96_CODES and multiplier_code in E96_MULTIPLIERS:
                significant = E96_CODES[value_code] / 100.0  # Convert to actual value
                multiplier = E96_MULTIPLIERS[multiplier_code]
                resistance = significant * multiplier
                return format_resistance(resistance), "E96 (4-digit)"
        
        # Codes with R (resistance < 100 Ohm)
        elif 'R' in code:
            # Replace R with decimal point and handle different formats
            if code.startswith('R'):
                # Format: R047 = 0.047 Ohm
                number_part = code[1:]
                if number_part.isdigit():
                    resistance = float('0.' + number_part)
                else:
                    resistance = float('0.' + number_part.replace('.', ''))
            elif code.endswith('R'):
                # Format: 47R = 47 Ohm
                resistance = float(code[:-1])
            else:
                # Format: 4R7 = 4.7 Ohm
                parts = code.split('R')
                if len(parts) == 2:
                    resistance = float(parts[0] + '.' + parts[1])
                else:
                    return None
            
            return format_resistance(resistance), "R-format"
        
        # 4-digit with R at start (like R047)
        elif re.match(r'^R[0-9]{3}$', code):
            resistance = float('0.' + code[1:])
            return format_resistance(resistance), "R-format (4-digit)"
    
    except (ValueError, IndexError):
        return None
    
    return None

def resistance_to_smd(resistance_str):
    """Преобразование значения сопротивления в SMD коды"""
    try:
        # Parse resistance value (support both Russian and English units)
        match = re.search(r'(\d+\.?\d*)\s*([кkKmM]?)\s*[оОoO]?[hmHM]?', resistance_str)
        if not match:
            return "Invalid value format"
        
        value, unit = match.groups()
        value = float(value)
        
        # Convert to Ohms
        if unit and unit.lower() in ['к', 'k']:
            value *= 1000
        elif unit and unit.lower() in ['м', 'm']:
            value *= 1000000
        
        resistance = value
        
        # Generate codes for different series
        codes = []
        series_types = []
        
        # E24 (3-digit) code
        e24_code = resistance_to_e24(resistance)
        if e24_code:
            codes.append(e24_code)
            series_types.append("E24")
        
        # E96 (4-digit) code
        e96_code = resistance_to_e96(resistance)
        if e96_code:
            codes.append(e96_code)
            series_types.append("E96")
        
        # R-format code (for resistances < 100 Ohm)
        r_code = resistance_to_r_format(resistance)
        if r_code:
            codes.append(r_code)
            series_types.append("R-format")
        
        if codes:
            formatted_value = format_resistance(resistance)
            return formatted_value, codes, series_types
        else:
            return "Could not find SMD code for this value"
    
    except Exception as e:
        return f"Conversion error: {str(e)}"

def resistance_to_e24(resistance):
    """Преобразование в E24 код (3-digit)"""
    if resistance < 0.1 or resistance > 999000000:
        return None
    
    # Find closest E24 value
    for e24_val in E24_SERIES:
        for exp in range(-2, 7):  # From 0.01 to 10M
            calculated = e24_val * (10 ** exp)
            if abs(calculated - resistance) / resistance < 0.1:  # 10% tolerance
                significant = int(e24_val * 10)
                multiplier = exp - 1
                if 0 <= multiplier <= 9:
                    return f"{significant:02d}{multiplier}"
    
    return None

def resistance_to_e96(resistance):
    """Преобразование в E96 код (4-digit)"""
    if resistance < 0.001 or resistance > 99900000:
        return None
    
    # Find closest E96 value
    for e96_val in E96_SERIES:
        for mult_code, multiplier in E96_MULTIPLIERS.items():
            calculated = e96_val * multiplier
            if abs(calculated - resistance) / resistance < 0.01:  # 1% tolerance
                # Find the 2-digit code for this E96 value
                for code, val in E96_CODES.items():
                    if abs(val - e96_val * 100) < 0.1:
                        return f"{code}{mult_code}"
    
    return None

def resistance_to_r_format(resistance):
    """Преобразование в R-формат код"""
    if resistance < 0.001:
        return None
    elif resistance < 1:
        # Format: R047 = 0.047 Ohm
        value_str = f"{resistance:.3f}".split('.')[1]
        return f"R{value_str}"
    elif resistance < 10:
        # Format: 4R7 = 4.7 Ohm
        int_part = int(resistance)
        frac_part = int(round((resistance - int_part) * 10))
        return f"{int_part}R{frac_part}"
    elif resistance < 100:
        # Format: 47R = 47 Ohm
        return f"{int(resistance)}R"
    else:
        return None

def format_resistance(value):
    """Форматирование значения сопротивления"""
    if value >= 1000000:
        return f"{value / 1000000:.2f} MOhm"
    elif value >= 1000:
        return f"{value / 1000:.2f} kOhm"
    elif value < 1:
        return f"{value:.3f} Ohm"
    else:
        return f"{value:.1f} Ohm".rstrip('0').rstrip('.')