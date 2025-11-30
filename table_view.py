from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTableView, QLabel, QLineEdit, QComboBox, QStyledItemDelegate)
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlQueryModel


class CurrencyDelegate(QStyledItemDelegate):
    """Delegate untuk format currency"""

    def displayText(self, value, locale):
        try:
            # Coba konversi ke float
            num = float(value)
            # Format dengan pemisah ribuan
            return f"Rp {num:,.0f}".replace(",", ".")
        except:
            return str(value)


class TableViewWidget(QWidget):
    """Widget untuk menampilkan data dengan QTableView dan 2 filter"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # === Filter Section (2 input filter) ===
        filter_layout = QHBoxLayout()

        # Filter 1: Nama Peminjam
        filter_layout.addWidget(QLabel("Filter Peminjam:"))
        self.filter_peminjam = QLineEdit()
        self.filter_peminjam.setPlaceholderText("Ketik nama peminjam...")
        self.filter_peminjam.textChanged.connect(self.update_query)
        filter_layout.addWidget(self.filter_peminjam)

        # Filter 2: Status
        filter_layout.addWidget(QLabel("Filter Status:"))
        self.filter_status = QComboBox()
        self.filter_status.addItems(["Semua", "Aktif", "Lunas", "Belum Bayar"])
        self.filter_status.currentTextChanged.connect(self.update_query)
        filter_layout.addWidget(self.filter_status)

        layout.addLayout(filter_layout)

        # === Table View ===
        self.table = QTableView()
        self.table.setSortingEnabled(True)

        # Set delegate untuk kolom currency
        self.currency_delegate = CurrencyDelegate()

        layout.addWidget(self.table)

        # Model menggunakan QSqlQueryModel
        self.model = QSqlQueryModel()
        self.table.setModel(self.model)

        self.setLayout(layout)
        self.update_query()

    def update_query(self):
        """Update query berdasarkan filter - Signal textChanged"""
        nama_filter = self.filter_peminjam.text()
        status_filter = self.filter_status.currentText()

        # Query JOIN 3 tabel
        query = '''
                SELECT pinjaman.id_pinjaman     AS "ID Pinjaman", \
                       peminjam.nama            AS "Nama Peminjam", \
                       peminjam.no_telp         AS "No. Telp", \
                       pinjaman.jumlah_pinjaman AS "Jumlah Pinjaman", \
                       pinjaman.tanggal_pinjam  AS "Tanggal Pinjam", \
                       pinjaman.tanggal_selesai AS "Tanggal Selesai", \
                       pinjaman.status          AS "Status Pinjaman", \
                       cicilan.cicilan_ke       AS "Cicilan Ke", \
                       cicilan.jumlah_cicilan   AS "Jumlah Cicilan", \
                       cicilan.status_bayar     AS "Status Cicilan"
                FROM pinjaman
                         JOIN peminjam ON pinjaman.id_peminjam = peminjam.id_peminjam
                         LEFT JOIN cicilan ON pinjaman.id_pinjaman = cicilan.id_pinjaman
                WHERE 1 = 1 \
                '''

        # Terapkan filter nama
        if nama_filter:
            query += f" AND peminjam.nama LIKE '%{nama_filter}%'"

        # Terapkan filter status
        if status_filter != "Semua":
            if status_filter in ["Aktif", "Lunas"]:
                query += f" AND pinjaman.status = '{status_filter}'"
            else:
                query += f" AND cicilan.status_bayar = '{status_filter}'"

        query += " ORDER BY pinjaman.id_pinjaman, cicilan.cicilan_ke"

        self.model.setQuery(query)

        # Set currency delegate untuk kolom jumlah
        # Kolom 3 = jumlah_pinjaman, kolom 8 = jumlah_cicilan (karena ada kolom no_telp)
        self.table.setItemDelegateForColumn(3, self.currency_delegate)
        self.table.setItemDelegateForColumn(8, self.currency_delegate)