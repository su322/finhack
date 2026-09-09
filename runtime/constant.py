import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
CONFIG_DIR = os.path.join(DATA_DIR, "config")
MODELS_DIR = os.path.join(DATA_DIR, "models")
PREDS_DIR = os.path.join(DATA_DIR, "preds")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
FACTORS_DIR = os.path.join(DATA_DIR, "factors")
