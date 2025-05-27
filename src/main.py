import json
import logging
import time
from datetime import datetime, timedelta

from requests import RequestException, session
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import AppConfig
from sources import SourceConfig
from models import db
from rss import RssReader
from .sources import main as sources_main

logger = logging.Logger(__name__)

def main():
    """
    程序入口
    """
    sources_main()

if __name__ == "__main__":
    main()
