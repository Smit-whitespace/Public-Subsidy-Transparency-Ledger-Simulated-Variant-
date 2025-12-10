from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Public Subsidy Transparency Ledger"
    DATABASE_URL: str = "sqlite:///./pstl.db"
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    BLOCKCHAIN_RPC: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
