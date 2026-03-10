from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None
    LOGTAIL_API_KEY: Optional[str] = None  # Move here for no prefix

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class GlobalConfig(BaseConfig):
    DATABASE_URL: Optional[str] = None
    DB_FORCE_ROLL_BACK: bool = False
    DEMO_MODE: bool = False
    DEMO_DEFAULT_SCENARIO_ID: str = "tel_aviv_rooftop"


class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(
        env_prefix="DEV_", env_file=".env", extra="ignore"
    )


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(
        env_prefix="PROD_", env_file=".env", extra="ignore"
    )


class TestConfig(GlobalConfig):
    DATABASE_URL: Optional[str] = "sqlite:///test.db"
    DB_FORCE_ROLL_BACK: bool = True

    model_config = SettingsConfigDict(
        env_prefix="TEST_", env_file=".env", extra="ignore"
    )


@lru_cache()
def get_config(env_state: str) -> GlobalConfig:
    configs = {"dev": DevConfig, "prod": ProdConfig, "test": TestConfig}
    return configs.get(env_state, DevConfig)()


config = get_config(BaseConfig().ENV_STATE or "dev")
