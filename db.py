import pymysql
from config import Config


def get_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        passwd=Config.DB_PASSWORD,
        db=Config.DB_NAME,
        charset='utf8mb4'
    )
