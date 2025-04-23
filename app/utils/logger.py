import logging
import inspect
from pathlib import Path
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from app.config.settings import settings

# Crear el directorio de logs si no existe
Path(settings.LOGS_DIR).mkdir(parents=True, exist_ok=True)

# Evita múltiples instancias
_loggers_cache = {}

def get_logger():
    frame = inspect.stack()[1]
    print("Frame -> ", inspect.stack())
    module_path = frame.filename
    module_name = Path(module_path).stem

    if module_name not in _loggers_cache:
        logger = logging.getLogger(module_name)
        logger.setLevel(settings.LOG_LEVEL)

        formatter = logging.Formatter(settings.LOG_FORMAT)

        log_file_path = Path(settings.LOGS_DIR) / f"{module_name}.log"

        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
        )
        file_handler.setLevel(settings.LOG_LEVEL)
        file_handler.setFormatter(formatter)

        stream_handler = StreamHandler()
        stream_handler.setLevel(settings.LOG_LEVEL)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.propagate = False  # Evita logs duplicados en consola

        _loggers_cache[module_name] = logger

    return _loggers_cache[module_name]

# Reducir el ruido de sqlalchemy
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
