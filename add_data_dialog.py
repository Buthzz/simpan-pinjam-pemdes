from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QPushButton, QLineEdit, QLabel, QComboBox,
                             QMessageBox, QDateEdit, QStackedWidget, QWidget)
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtCore import Qt, QDate


class AddDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tambah Data Baru")
        self.setGeometry(200, 200, 600, 400)
        self.db = QSqlQuery().database() # Get the current QSqlDatabase instance

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.init_type_selector()
        self.init_stacked_forms()
        self.init_buttons()

    def init_type_selector(self):
        # Widget untuk memilih tipe data (Peminjam, Pinjaman, Cicilan)
        type_selector_layout = QHBoxLayout()
        type_selector_layout.addWidget(QLabel("Pilih Tipe Data:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Peminjam", "Pinjaman", "Cicilan"])
        self.type_combo.currentIndexChanged.connect(self.change_form)
        type_selector_layout.addWidget(self.type_combo)
        self.main_layout.addLayout(type_selector_layout)

    def init_stacked_forms(self):
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.form_peminjam = self._create_peminjam_form()
        self.form_pinjaman = self._create_pinjaman_form()
        self.form_cicilan = self._create_cicilan_form()

        self.stacked_widget.addWidget(self.form_peminjam) # Index 0
        self.stacked_widget.addWidget(self.form_pinjaman) # Index 1
        self.stacked_widget.addWidget(self.form_cicilan)  # Index 2

        self.change_form(0) # Default to Peminjam form

    def _create_peminjam_form(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.peminjam_fields = {}
        self.peminjam_fields['nama'] = QLineEdit()
        self.peminjam_fields['alamat'] = QLineEdit()
        self.peminjam_fields['no_telp'] = QLineEdit()
        self.peminjam_fields['email'] = QLineEdit()

        layout.addRow("Nama:", self.peminjam_fields['nama'])
        layout.addRow("Alamat:", self.peminjam_fields['alamat'])
        layout.addRow("No. Telp:", self.peminjam_fields['no_telp'])
        layout.addRow("Email:", self.peminjam_fields['email'])
        return widget

    def _create_pinjaman_form(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.pinjaman_fields = {}
        self.pinjaman_fields['id_peminjam'] = QComboBox()
        self.pinjaman_fields['jumlah_pinjaman'] = QLineEdit()
        self.pinjaman_fields['tanggal_pinjam'] = QDateEdit(calendarPopup=True)
        self.pinjaman_fields['tanggal_pinjam'].setDisplayFormat("yyyy-MM-dd")
        self.pinjaman_fields['tanggal_pinjam'].setDate(QDate.currentDate())
        self.pinjaman_fields['tanggal_selesai'] = QDateEdit(calendarPopup=True)
        self.pinjaman_fields['tanggal_selesai'].setDisplayFormat("yyyy-MM-dd")
        self.pinjaman_fields['tanggal_selesai'].setDate(QDate.currentDate().addMonths(6)) # Default 6 months
        self.pinjaman_fields['status'] = QComboBox()
        self.pinjaman_fields['status'].addItems(["Aktif", "Lunas"])

        layout.addRow("Peminjam:", self.pinjaman_fields['id_peminjam'])
        layout.addRow("Jumlah Pinjaman:", self.pinjaman_fields['jumlah_pinjaman'])
        layout.addRow("Tanggal Pinjam:", self.pinjaman_fields['tanggal_pinjam'])
        layout.addRow("Tanggal Selesai:", self.pinjaman_fields['tanggal_selesai'])
        layout.addRow("Status:", self.pinjaman_fields['status'])

        self._load_peminjam_to_combo(self.pinjaman_fields['id_peminjam'])
        return widget

    def _create_cicilan_form(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.cicilan_fields = {}
        self.cicilan_fields['nama_peminjam'] = QComboBox() # User selects borrower name
        self.cicilan_fields['id_pinjaman'] = QComboBox() # Populated based on selected borrower
        self.cicilan_fields['cicilan_ke'] = QLineEdit()
        self.cicilan_fields['jumlah_cicilan'] = QLineEdit()
        self.cicilan_fields['tanggal_bayar'] = QDateEdit(calendarPopup=True)
        self.cicilan_fields['tanggal_bayar'].setDisplayFormat("yyyy-MM-dd")
        self.cicilan_fields['tanggal_bayar'].setDate(QDate.currentDate())
        self.cicilan_fields['status_bayar'] = QComboBox()
        self.cicilan_fields['status_bayar'].addItems(["Belum Bayar", "Lunas"])

        layout.addRow("Nama Peminjam:", self.cicilan_fields['nama_peminjam'])
        layout.addRow("ID Pinjaman:", self.cicilan_fields['id_pinjaman'])
        layout.addRow("Cicilan Ke-:", self.cicilan_fields['cicilan_ke'])
        layout.addRow("Jumlah Cicilan:", self.cicilan_fields['jumlah_cicilan'])
        layout.addRow("Tanggal Bayar:", self.cicilan_fields['tanggal_bayar'])
        layout.addRow("Status Bayar:", self.cicilan_fields['status_bayar'])

        self._load_peminjam_to_combo(self.cicilan_fields['nama_peminjam'])
        self.cicilan_fields['nama_peminjam'].currentIndexChanged.connect(self._load_pinjaman_to_combo)
        # Initial load for pinjaman if a peminjam is pre-selected
        if self.cicilan_fields['nama_peminjam'].currentData() is not None:
             self._load_pinjaman_to_combo(self.cicilan_fields['nama_peminjam'].currentIndex())

        return widget

    def _load_peminjam_to_combo(self, combo_box):
        combo_box.clear()
        query = QSqlQuery(self.db)
        query.exec("SELECT id_peminjam, nama FROM peminjam ORDER BY nama")
        combo_box.addItem("Pilih Peminjam", None) # Add a placeholder
        while query.next():
            combo_box.addItem(query.value(1), query.value(0)) # text=nama, data=id

    def _load_pinjaman_to_combo(self, index):
        peminjam_id = self.cicilan_fields['nama_peminjam'].currentData()
        self.cicilan_fields['id_pinjaman'].clear()
        if peminjam_id is None:
            self.cicilan_fields['id_pinjaman'].addItem("Pilih Pinjaman", None)
            return

        query = QSqlQuery(self.db)
        query.prepare("SELECT id_pinjaman, jumlah_pinjaman, tanggal_pinjam FROM pinjaman WHERE id_peminjam = ?")
        query.addBindValue(peminjam_id)
        query.exec()

        self.cicilan_fields['id_pinjaman'].addItem("Pilih Pinjaman", None) # Placeholder
        while query.next():
            loan_id = query.value(0)
            amount = query.value(1)
            date = query.value(2)
            display_text = f"ID: {loan_id} - Rp {amount:,.0f} ({date})"
            self.cicilan_fields['id_pinjaman'].addItem(display_text, loan_id)

    def init_buttons(self):
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Simpan")
        self.cancel_button = QPushButton("Batal")

        self.save_button.clicked.connect(self.save_data)
        self.cancel_button.clicked.connect(self.reject) # Reject closes the dialog

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(button_layout)

    def change_form(self, index):
        self.stacked_widget.setCurrentIndex(index)
        # Optionally update dialog size based on form
        if index == 0: # Peminjam
            self.setFixedSize(400, 300)
        elif index == 1: # Pinjaman
            self.setFixedSize(500, 350)
        elif index == 2: # Cicilan
            self.setFixedSize(500, 400)


    def save_data(self):
        current_form_index = self.stacked_widget.currentIndex()

        if current_form_index == 0: # Peminjam
            self._save_peminjam()
        elif current_form_index == 1: # Pinjaman
            self._save_pinjaman()
        elif current_form_index == 2: # Cicilan
            self._save_cicilan()

    def _save_peminjam(self):
        nama = self.peminjam_fields['nama'].text().strip()
        alamat = self.peminjam_fields['alamat'].text().strip()
        no_telp = self.peminjam_fields['no_telp'].text().strip()
        email = self.peminjam_fields['email'].text().strip()

        if not all([nama, alamat, no_telp, email]):
            QMessageBox.warning(self, "Input Error", "Semua field harus diisi untuk Peminjam.")
            return

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO peminjam (nama, alamat, no_telp, email) VALUES (?, ?, ?, ?)")
        query.addBindValue(nama)
        query.addBindValue(alamat)
        query.addBindValue(no_telp)
        query.addBindValue(email)

        if query.exec():
            QMessageBox.information(self, "Sukses", "Data Peminjam berhasil ditambahkan.")
            self.accept() # Close dialog
        else:
            QMessageBox.critical(self, "Error", f"Gagal menambahkan Peminjam: {query.lastError().text()}")

    def _save_pinjaman(self):
        id_peminjam = self.pinjaman_fields['id_peminjam'].currentData()
        jumlah_pinjaman_str = self.pinjaman_fields['jumlah_pinjaman'].text().strip()
        tanggal_pinjam = self.pinjaman_fields['tanggal_pinjam'].date().toString("yyyy-MM-dd")
        tanggal_selesai = self.pinjaman_fields['tanggal_selesai'].date().toString("yyyy-MM-dd")
        status = self.pinjaman_fields['status'].currentText()

        if id_peminjam is None:
            QMessageBox.warning(self, "Input Error", "Peminjam harus dipilih.")
            return
        if not jumlah_pinjaman_str:
            QMessageBox.warning(self, "Input Error", "Jumlah Pinjaman harus diisi.")
            return
        try:
            jumlah_pinjaman = float(jumlah_pinjaman_str)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Jumlah Pinjaman harus berupa angka.")
            return

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO pinjaman (id_peminjam, jumlah_pinjaman, tanggal_pinjam, tanggal_selesai, status) VALUES (?, ?, ?, ?, ?)")
        query.addBindValue(id_peminjam)
        query.addBindValue(jumlah_pinjaman)
        query.addBindValue(tanggal_pinjam)
        query.addBindValue(tanggal_selesai)
        query.addBindValue(status)

        if query.exec():
            QMessageBox.information(self, "Sukses", "Data Pinjaman berhasil ditambahkan.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Gagal menambahkan Pinjaman: {query.lastError().text()}")

    def _save_cicilan(self):
        id_pinjaman = self.cicilan_fields['id_pinjaman'].currentData()
        cicilan_ke_str = self.cicilan_fields['cicilan_ke'].text().strip()
        jumlah_cicilan_str = self.cicilan_fields['jumlah_cicilan'].text().strip()
        tanggal_bayar = self.cicilan_fields['tanggal_bayar'].date().toString("yyyy-MM-dd")
        status_bayar = self.cicilan_fields['status_bayar'].currentText()

        if id_pinjaman is None:
            QMessageBox.warning(self, "Input Error", "Pinjaman harus dipilih.")
            return
        if not cicilan_ke_str:
            QMessageBox.warning(self, "Input Error", "Cicilan Ke- harus diisi.")
            return
        try:
            cicilan_ke = int(cicilan_ke_str)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Cicilan Ke- harus berupa angka bulat.")
            return
        if not jumlah_cicilan_str:
            QMessageBox.warning(self, "Input Error", "Jumlah Cicilan harus diisi.")
            return
        try:
            jumlah_cicilan = float(jumlah_cicilan_str)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Jumlah Cicilan harus berupa angka.")
            return

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO cicilan (id_pinjaman, cicilan_ke, jumlah_cicilan, tanggal_bayar, status_bayar) VALUES (?, ?, ?, ?, ?)")
        query.addBindValue(id_pinjaman)
        query.addBindValue(cicilan_ke)
        query.addBindValue(jumlah_cicilan)
        query.addBindValue(tanggal_bayar)
        query.addBindValue(status_bayar)

        if query.exec():
            QMessageBox.information(self, "Sukses", "Data Cicilan berhasil ditambahkan.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Gagal menambahkan Cicilan: {query.lastError().text()}")

