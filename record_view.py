from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox,
                             QDateEdit, QDataWidgetMapper, QMessageBox, QDialog) # Added QDialog
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlTableModel, QSqlQuery, QSqlRelationalTableModel, QSqlRelation
from add_data_dialog import AddDataDialog # Import the new dialog


class RecordViewWidget(QWidget):
    """Widget untuk CRUD menggunakan QDataWidgetMapper"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_table = "peminjam"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # === Table Selector ===
        table_layout = QHBoxLayout()
        table_layout.addWidget(QLabel("Pilih Tabel:"))
        self.table_selector = QComboBox()
        self.table_selector.addItems(["peminjam", "pinjaman", "cicilan"])
        self.table_selector.currentTextChanged.connect(self.change_table)
        table_layout.addWidget(self.table_selector)
        layout.addLayout(table_layout)

        # === Form Layout ===
        self.form_layout = QFormLayout()
        layout.addLayout(self.form_layout)

        # === Navigation Controls ===
        nav_layout = QHBoxLayout()

        self.btn_first = QPushButton("<<")
        self.btn_prev = QPushButton("<")
        self.lbl_position = QLabel("0/0")
        self.lbl_position.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_next = QPushButton(">")
        self.btn_last = QPushButton(">>")

        self.btn_first.clicked.connect(self.first_record)
        self.btn_prev.clicked.connect(self.prev_record)
        self.btn_next.clicked.connect(self.next_record)
        self.btn_last.clicked.connect(self.last_record)

        nav_layout.addWidget(self.btn_first)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.lbl_position)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addWidget(self.btn_last)
        layout.addLayout(nav_layout)

        # === Action Buttons (CRUD) ===
        action_layout = QHBoxLayout()

        self.btn_add = QPushButton("Tambah")
        self.btn_delete = QPushButton("Hapus")
        self.btn_save = QPushButton("Simpan") # Restored
        self.btn_cancel = QPushButton("Batal") # Restored

        self.btn_add.clicked.connect(self.add_record)
        self.btn_delete.clicked.connect(self.delete_record)
        self.btn_save.clicked.connect(self.save_record) # Restored
        self.btn_cancel.clicked.connect(self.cancel_edit) # Restored

        action_layout.addWidget(self.btn_add)
        action_layout.addWidget(self.btn_delete)
        action_layout.addWidget(self.btn_save) # Restored
        action_layout.addWidget(self.btn_cancel) # Restored
        layout.addLayout(action_layout)

        self.setLayout(layout)

        # Initialize QDataWidgetMapper
        self.mapper = QDataWidgetMapper()
        self.mapper.currentIndexChanged.connect(self.update_position)

        # Load initial table
        self.change_table("peminjam")

    def change_table(self, table_name):
        """Ganti tabel yang ditampilkan"""
        self.current_table = table_name

        # Clear form
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)

        # Setup model dengan relasi untuk foreign key
        if table_name == "pinjaman":
            # Gunakan QSqlRelationalTableModel untuk menampilkan nama peminjam
            self.model = QSqlRelationalTableModel()
            self.model.setTable(table_name)
            self.model.setRelation(1, QSqlRelation("peminjam", "id_peminjam", "nama"))
            self.model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        elif table_name == "cicilan":
            # Gunakan QSqlRelationalTableModel untuk menampilkan ID Pinjaman
            self.model = QSqlRelationalTableModel()
            self.model.setTable(table_name)
            # Untuk cicilan, tetap tampilkan id_pinjaman (tidak ada nama yang cocok)
            self.model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        else:
            # Tabel peminjam tidak perlu relasi
            self.model = QSqlTableModel()
            self.model.setTable(table_name)
            self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)

        self.model.select()

        # Setup QDataWidgetMapper
        self.mapper.setModel(self.model)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.SubmitPolicy.ManualSubmit)

        # Create form fields
        self.create_form_fields()

        # Navigate to first record
        if self.model.rowCount() > 0: # Check if there are records
            self.mapper.toFirst()
        self.update_position()

    def create_form_fields(self):
        """Buat form fields berdasarkan kolom tabel"""
        self.fields = {}

        for i in range(self.model.columnCount()):
            col_name = self.model.headerData(i, Qt.Orientation.Horizontal)

            # Primary key (read-only)
            if col_name and 'id_' in col_name.lower() and i == 0:
                field = QLineEdit()
                field.setReadOnly(True)
                self.fields[col_name] = field
                self.form_layout.addRow(col_name + ":", field)
                self.mapper.addMapping(field, i)

            # Foreign key id_peminjam - tampilkan sebagai ComboBox dengan nama
            elif col_name and col_name.lower() == 'id_peminjam':
                field = QComboBox()
                # Load data peminjam
                query = QSqlQuery()
                query.exec("SELECT id_peminjam, nama FROM peminjam ORDER BY nama")
                while query.next():
                    field.addItem(query.value(1), query.value(0))  # text=nama, data=id
                self.fields[col_name] = field
                self.form_layout.addRow("Peminjam:", field)
                self.mapper.addMapping(field, i)

            # Date fields
            elif col_name and 'tanggal' in col_name.lower():
                field = QDateEdit()
                field.setCalendarPopup(True)
                field.setDisplayFormat("yyyy-MM-dd")
                self.fields[col_name] = field
                self.form_layout.addRow(col_name + ":", field)
                self.mapper.addMapping(field, i)

            # Status fields (ComboBox)
            elif col_name and 'status' in col_name.lower():
                field = QComboBox()
                if 'pinjaman' in self.current_table:
                    field.addItems(["Aktif", "Lunas"])
                else:
                    field.addItems(["Belum Bayar", "Lunas"])
                self.fields[col_name] = field
                self.form_layout.addRow(col_name + ":", field)
                self.mapper.addMapping(field, i)

            # Jumlah/nominal fields - format dengan pemisah ribuan
            elif col_name and ('jumlah' in col_name.lower() or 'nominal' in col_name.lower()):
                field = QLineEdit()
                # Validator untuk angka saja
                self.fields[col_name] = field
                self.form_layout.addRow(col_name + ":", field)
                self.mapper.addMapping(field, i)

            # Regular text fields
            else:
                field = QLineEdit()
                self.fields[col_name] = field
                self.form_layout.addRow(col_name + ":", field)
                self.mapper.addMapping(field, i)

    def update_position(self):
        """Update label posisi record"""
        current = self.mapper.currentIndex() + 1
        total = self.model.rowCount()
        self.lbl_position.setText(f"{current}/{total}")

        # Enable/disable navigation buttons
        self.btn_first.setEnabled(current > 1)
        self.btn_prev.setEnabled(current > 1)
        self.btn_next.setEnabled(current < total)
        self.btn_last.setEnabled(current < total)

    # === Navigation Methods ===
    def first_record(self):
        self.mapper.toFirst()

    def prev_record(self):
        self.mapper.toPrevious()

    def next_record(self):
        self.mapper.toNext()
        # After navigating, if the current index is -1 (no records),
        # ensure the form fields are cleared. This handles cases
        # where the last record is deleted.
        if self.model.rowCount() > 0 and self.mapper.currentIndex() == -1:
            self.mapper.toFirst()
        elif self.model.rowCount() == 0:
            self.mapper.clearMapping()
            self.update_position()

    def last_record(self):
        self.mapper.toLast()

    # === CRUD Operations ===
    def add_record(self):
        """Membuka dialog untuk menambah record baru"""
        dialog = AddDataDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh the current table's data if a new record was added
            self.model.select()
            if self.model.rowCount() > 0:
                self.mapper.toLast() # Go to the newly added record
            else:
                self.mapper.clearMapping() # Clear form if no records left
            self.update_position()


    def delete_record(self):
        """Hapus record saat ini"""
        reply = QMessageBox.question(
            self,
            "Konfirmasi Hapus",
            "Yakin ingin menghapus record ini?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            current_index = self.mapper.currentIndex()
            if current_index >= 0:
                self.model.removeRow(current_index)
                if self.model.submitAll():
                    QMessageBox.information(self, "Sukses", "Data berhasil dihapus!")
                    self.model.select() # Re-select to refresh the view
                    if self.model.rowCount() > 0:
                        self.mapper.toFirst() # Go to first record if available
                    else:
                        self.mapper.clearMapping() # Clear form if no records left
                    self.update_position()
                else:
                    QMessageBox.critical(self, "Error",
                                         f"Gagal menghapus: {self.model.lastError().text()}")
                    self.model.revertAll()
            else:
                QMessageBox.warning(self, "Peringatan", "Tidak ada record untuk dihapus.")

    def save_record(self):
        """Simpan perubahan pada record yang sedang ditampilkan"""
        # Untuk pinjaman, konversi nama peminjam ke id_peminjam sebelum simpan
        if self.current_table == "pinjaman" and 'id_peminjam' in self.fields:
            combo = self.fields['id_peminjam']
            id_peminjam = combo.currentData()
            # Set nilai id_peminjam ke model
            current_row = self.mapper.currentIndex()
            self.model.setData(self.model.index(current_row, 1), id_peminjam)

        self.mapper.submit()

        if self.model.submitAll():
            QMessageBox.information(self, "Sukses", "Data berhasil disimpan!")
            self.model.select()
        else:
            QMessageBox.critical(self, "Error",
                                 f"Gagal menyimpan: {self.model.lastError().text()}")
            self.model.revertAll()

    def cancel_edit(self):
        """Batal dan revert perubahan pada record yang sedang ditampilkan"""
        self.model.revertAll()
        self.mapper.revert()