from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QPushButton, QLineEdit, QLabel, QComboBox,
                             QMessageBox, QDateEdit, QStackedWidget, QWidget)
from PyQt6.QtSql import QSqlQuery, QSqlDatabase
from PyQt6.QtCore import Qt, QDate, QLocale, pyqtProperty
from PyQt6.QtGui import QDoubleValidator


class CurrencyLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        validator = QDoubleValidator(0.0, 1000000000000000.0, 2, self)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.setValidator(validator)

        self._numeric_value = 0.0
        self.indonesian_locale = QLocale(QLocale.Language.Indonesian, QLocale.Country.Indonesia)
        self.editingFinished.connect(self._on_editing_finished)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def _format_value_for_display(self, value):
        try:
            num = float(value)
            
            
            return f"Rp {self.indonesian_locale.toString(num, 'f', 0)}"
        except (ValueError, TypeError):
            return ""

    def _get_numeric_from_display_text(self, text):
        
        cleaned_text = text.replace("Rp ", "").strip()
        try:
            
            num, ok = self.indonesian_locale.toDouble(cleaned_text)
            if ok:
                return num
            else:
                return 0.0
        except (ValueError, TypeError):
            return 0.0

    def get_numeric_value(self):
        
        return self._numeric_value

    def set_numeric_value(self, value):
        if value is None:
            value = 0.0
        new_numeric_value = float(value)
        if self._numeric_value != new_numeric_value:
            self._numeric_value = new_numeric_value
            
            super().setText(self._format_value_for_display(self._numeric_value))

    
    
    
    numeric_value = pyqtProperty(float, get_numeric_value, set_numeric_value, user=True)

    def _on_editing_finished(self):
        
        
        current_display_text = self.text()
        parsed_value = self._get_numeric_from_display_text(current_display_text)
        self.set_numeric_value(parsed_value) 

    
    def setText(self, text):
        if isinstance(text, (int, float)):
            self.set_numeric_value(text)
        else:
            
            num = self._get_numeric_from_display_text(text)
            self.set_numeric_value(num)

    def text(self):
        
        return super().text()


class AddDataDialog(QDialog):
    def __init__(self, parent=None, table_type=None): 
        super().__init__(parent)
        self.setWindowTitle("Tambah Data Baru")
        self.setGeometry(200, 200, 600, 400)
        self.db = QSqlDatabase.database() 
        self.table_type = table_type 

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        
        self.table_to_index = {"peminjam": 0, "pinjaman": 1, "cicilan": 2}

        self.type_selector_widget = QWidget() 
        self.init_type_selector()
        self.main_layout.addWidget(self.type_selector_widget)

        self.init_stacked_forms()
        self.init_buttons()

        if self.table_type:
            
            
            self.type_selector_widget.hide()
            if self.table_type in self.table_to_index:
                self.change_form(self.table_to_index[self.table_type])
            else:
                QMessageBox.critical(self, "Error", f"Invalid table type: {self.table_type}")
                self.reject() 
        else:
            
            self.change_form(0) 


    def init_type_selector(self):
        
        type_selector_layout = QHBoxLayout(self.type_selector_widget)
        type_selector_layout.addWidget(QLabel("Pilih Tipe Data:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Peminjam", "Pinjaman", "Cicilan"])
        self.type_combo.currentTextChanged.connect(self.change_form_by_name) 
        type_selector_layout.addWidget(self.type_combo)


    def init_stacked_forms(self):
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.form_peminjam = self._create_peminjam_form()
        self.form_pinjaman = self._create_pinjaman_form()
        self.form_cicilan = self._create_cicilan_form()

        self.stacked_widget.addWidget(self.form_peminjam) 
        self.stacked_widget.addWidget(self.form_pinjaman) 
        self.stacked_widget.addWidget(self.form_cicilan)  


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
        self.pinjaman_fields['jumlah_pinjaman'] = CurrencyLineEdit()
        self.pinjaman_fields['tanggal_pinjam'] = QDateEdit(calendarPopup=True)
        self.pinjaman_fields['tanggal_pinjam'].setDisplayFormat("yyyy-MM-dd")
        self.pinjaman_fields['tanggal_pinjam'].setDate(QDate.currentDate())
        self.pinjaman_fields['tanggal_selesai'] = QDateEdit(calendarPopup=True)
        self.pinjaman_fields['tanggal_selesai'].setDisplayFormat("yyyy-MM-dd")
        self.pinjaman_fields['tanggal_selesai'].setDate(QDate.currentDate().addMonths(6)) 
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
        self.cicilan_fields['nama_peminjam'] = QComboBox() 
        self.cicilan_fields['id_pinjaman'] = QComboBox() 
        self.cicilan_fields['cicilan_ke'] = QLineEdit()
        self.cicilan_fields['jumlah_cicilan'] = CurrencyLineEdit()
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
        
        if self.cicilan_fields['nama_peminjam'].currentData() is not None:
             self._load_pinjaman_to_combo(self.cicilan_fields['nama_peminjam'].currentIndex())

        return widget

    def _load_peminjam_to_combo(self, combo_box):
        combo_box.clear()
        query = QSqlQuery(self.db)
        query.exec("SELECT id_peminjam, nama FROM peminjam ORDER BY nama")
        combo_box.addItem("Pilih Peminjam", None) 
        while query.next():
            combo_box.addItem(query.value(1), query.value(0)) 

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

        self.cicilan_fields['id_pinjaman'].addItem("Pilih Pinjaman", None) 
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
        self.cancel_button.clicked.connect(self.reject) 

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(button_layout)

    def change_form_by_name(self, table_name_str):
        
        if table_name_str in self.table_to_index:
            index = self.table_to_index[table_name_str]
            self.change_form(index)
        else:
            QMessageBox.critical(self, "Error", f"Invalid table type selected: {table_name_str}")

    def change_form(self, index):
        self.stacked_widget.setCurrentIndex(index)
        
        if index == 0: 
            self.setFixedSize(400, 300)
        elif index == 1: 
            self.setFixedSize(500, 350)
        elif index == 2: 
            self.setFixedSize(500, 400)


    def save_data(self):
        current_form_index = self.stacked_widget.currentIndex()

        if current_form_index == 0: 
            self._save_peminjam()
        elif current_form_index == 1: 
            self._save_pinjaman()
        elif current_form_index == 2: 
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
            self.accept() 
        else:
            QMessageBox.critical(self, "Error", f"Gagal menambahkan Peminjam: {query.lastError().text()}")

    def _save_pinjaman(self):
        id_peminjam = self.pinjaman_fields['id_peminjam'].currentData()
        jumlah_pinjaman = self.pinjaman_fields['jumlah_pinjaman'].get_numeric_value()

        if id_peminjam is None:
            QMessageBox.warning(self, "Input Error", "Peminjam harus dipilih.")
            return
        if jumlah_pinjaman <= 0: 
            QMessageBox.warning(self, "Input Error", "Jumlah Pinjaman harus berupa angka positif.")
            return

        tanggal_pinjam = self.pinjaman_fields['tanggal_pinjam'].date().toString("yyyy-MM-dd")
        tanggal_selesai = self.pinjaman_fields['tanggal_selesai'].date().toString("yyyy-MM-dd")
        status = self.pinjaman_fields['status'].currentText()

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
        jumlah_cicilan = self.cicilan_fields['jumlah_cicilan'].get_numeric_value()

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
        if jumlah_cicilan <= 0: 
            QMessageBox.warning(self, "Input Error", "Jumlah Cicilan harus berupa angka positif.")
            return

        tanggal_bayar = self.cicilan_fields['tanggal_bayar'].date().toString("yyyy-MM-dd")
        status_bayar = self.cicilan_fields['status_bayar'].currentText()

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