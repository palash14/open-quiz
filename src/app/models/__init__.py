# /src/app/models/__init__.py
import os
import importlib
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Get the current directory (i.e., the models directory)
models_directory = os.path.dirname(__file__)

# Dynamically import all Python files (excluding __init__.py) in the models directory
for filename in os.listdir(models_directory):
    if filename.endswith(".py") and filename != "__init__.py":
        module_name = filename[:-3]  # Remove the ".py" extension to get the module name
        importlib.import_module(f"{__name__}.{module_name}")
