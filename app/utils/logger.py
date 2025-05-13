import logging
import inspect
from pathlib import Path
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from app.config.settings import settings

# Crear el directorio de logs si no existe
Path(settings.LOGS_DIR).mkdir(parents=True, exist_ok=True)

# Cache de loggers para evitar duplicados
_loggers_cache = {}

def get_logger():
    # Detecta el módulo que pidió el logger
    frame = inspect.stack()[1]
    module_path = frame.filename
    module_name = Path(module_path).stem

    if module_name in _loggers_cache:
        return _loggers_cache[module_name]

    logger = logging.getLogger(module_name)
    logger.setLevel(settings.LOG_LEVEL)
    logger.propagate = False  # Evita logs duplicados en consola

    formatter = logging.Formatter(settings.LOG_FORMAT)

    # === 1. Log por módulo ===
    log_file_path = Path(settings.LOGS_DIR) / f"{module_name}.log"
    log_file_path.touch(exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(settings.LOG_LEVEL)
    logger.addHandler(file_handler)

    # === 2. Log por hora (opcional, comentá si no lo usás) ===
    if getattr(settings, "LOG_BY_HOUR", False):
        hour_filename = f"log{settings.CURRENT_TIME.strftime('%H')}.log"
        hourly_log_path = Path(settings.LOGS_DIR) / hour_filename
        hourly_log_path.touch(exist_ok=True)

        hourly_handler = RotatingFileHandler(
            filename=hourly_log_path,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8"
        )
        hourly_handler.setFormatter(formatter)
        hourly_handler.setLevel(settings.LOG_LEVEL)
        logger.addHandler(hourly_handler)

    # === 3. Console output ===
    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(settings.LOG_LEVEL)
    logger.addHandler(stream_handler)

    # Guardar en cache
    _loggers_cache[module_name] = logger
    return logger

# Silenciar ruido de SQLAlchemy
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
