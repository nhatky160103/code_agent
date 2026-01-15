# Configuration settings for the Code Agent application

import os
from pathlib import Path

class Settings:
    def __init__(self):
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", None)
        self.logs_dir = Path(os.getenv("LOGS_DIR", "logs"))
        self.enable_metrics_server = os.getenv("ENABLE_METRICS_SERVER", "False").lower() in ("true", "1")
        self.metrics_port = int(os.getenv("METRICS_PORT", 8000))

    def ensure_directories(self):
        if not self.logs_dir.exists():
            self.logs_dir.mkdir(parents=True)

settings = Settings()
settings.ensure_directories()