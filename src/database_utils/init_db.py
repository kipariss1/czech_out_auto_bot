from src.database_utils.database_factory import DBFactory

db_handler = DBFactory.create_db_handler()
db_handler.create_tables()