import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.shared.configuration.config import env_config_manager


# CORS Setup (Dynamic from Configuration)
def setup_cors_middleware(app: FastAPI):
    # Get origins from dynaconf settings
    origins = env_config_manager.get_dynamic_setting("CORS_ORIGINS", ["*"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["content-disposition"],
    )
