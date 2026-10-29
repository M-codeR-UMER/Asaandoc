from pydantic_settings import BaseSettings, SettingsConfigDict

_base_config = SettingsConfigDict( # this is used to setup the path of env and some additional attributes also.
    env_file= "./.env", # path of env.
    env_ignore_empty=True, # Ignore if env is empty. 
    extra="ignore", # This allow us to take only above class attributes from env.
)

class DatabaseSettings(BaseSettings):
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str    
    
    REDIS_HOST: str
    REDIS_PORT: int
    
    model_config =_base_config
    
    @property
    def POSTGRES_URL(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}" 

class Security_settings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str

    model_config= _base_config

class Notification_settings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM_NAME: str
    MAIL_FROM: str
    MAIL_SERVER: str
    MAIL_PORT: int

    model_config= _base_config
    
db_settings = DatabaseSettings() #type: ignore  
security_settings = Security_settings()  #type: ignore
notification_settings = Notification_settings() #type: ignore