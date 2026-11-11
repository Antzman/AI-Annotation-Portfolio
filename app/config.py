import os
import secrets


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = "sqlite:///portfolio.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
