from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QMessageBox


class DatabaseManager:

    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self.db = None

    def connect(self):
        """Membuat koneksi ke database SQLite"""
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(self.db_name)

        if not self.db.open():
            QMessageBox.critical(None, "Database Error",
                                 f"Tidak dapat membuka database: {self.db_name}")
            return False

        return True

    def execute_query(self, query_string):
        """Eksekusi query SQL"""
        query = QSqlQuery()
        if not query.exec(query_string):
            print(f"Error executing query: {query.lastError().text()}")
            return False
        return True