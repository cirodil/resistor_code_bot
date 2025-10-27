FROM python:3.11-slim

WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем директорию для логов и даем права
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Создаем не-root пользователя для безопасности
RUN useradd -m -r botuser && chown -R botuser:botuser /app
USER botuser

# Запускаем бота
CMD ["python", "resistor_code_bot.py"]