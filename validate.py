from ModelEngine import ModelEngine
from QueryEngine import QueryEngine
from ValidationEngine import ValidationEngine
import json
import pandas as pd

config = { }
with open("config.json") as f:
    config = json.load(f)

validationEngine = ValidationEngine(
    config["validation_endpoint"]["url"],
    QueryEngine(config["data_endpoint"]["url"]),
    modelCacheEndpoint=config["model_cache_endpoint"]["url"])
validationEngine.processValidationRequests()
