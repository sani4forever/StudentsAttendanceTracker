import logging
import os

def setup_logger():
    # Создаем папку для логов, если нет
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/app.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("AttendanceApp")