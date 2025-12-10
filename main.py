import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from database_manager import DatabaseManager
from table_view import TableViewWidget
from record_view import RecordViewWidget
import create_database


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        
        self.db_manager = DatabaseManager("database.db")
        if not self.db_manager.connect():
            sys.exit(1)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Aplikasi Simpan Pinjam Uang - UAS Pemrograman Desktop")
        self.setGeometry(100, 100, 1200, 700)

        
        tabs = QTabWidget()

        
        self.table_view = TableViewWidget()
        tabs.addTab(self.table_view, "Table View (Filter)")

        
        self.record_view = RecordViewWidget()
        tabs.addTab(self.record_view, "Record View (CRUD)")

        self.setCentralWidget(tabs)


def main():
    
    if not os.path.exists('database.db'):
        print("Database 'database.db' tidak ditemukan. Membuat database baru...")
        create_database.create_database()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()