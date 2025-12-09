from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox,
                             QDateEdit, QDataWidgetMapper, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, pyqtProperty, QLocale
from PyQt6.QtSql import QSqlTableModel, QSqlQuery, QSqlRelationalTableModel, QSqlRelation, QSqlDatabase
from PyQt6.QtGui import QDoubleValidator # Add this import
from add_data_dialog import AddDataDialog # Add this import


# Custom ComboBox for QDataWidgetMapper to handle currentData property
class MappingComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def _get_current_data_property(self):
        return self.currentData()

    def _set_current_data_property(self, value):
        # Find the index of the item that has 'value' as its userData
        index = self.findData(value)
        if index >= 0:
            self.setCurrentIndex(index)
        # If value is None and combo has placeholder, set to placeholder
        elif value is None and self.count() > 0 and self.itemData(0) is None:
            self.setCurrentIndex(0)

    # Expose currentData as a read/write PyQt property
    # Changed 'object' to 'int' to resolve TypeError
    currentData_property = pyqtProperty(int, _get_current_data_property, _set_current_data_property, user=True)


class CurrencyLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Allow numbers and one decimal point. Max 15 digits before decimal, 2 after.
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
            # Format using QLocale, with 'f' format (fixed point) and 0 decimal places.
            # Add "Rp " prefix.
            return f"Rp {self.indonesian_locale.toString(num, 'f', 0)}"
        except (ValueError, TypeError):
            return ""

    def _get_numeric_from_display_text(self, text):
        # Remove "Rp " prefix, then use QLocale to parse the number
        cleaned_text = text.replace("Rp ", "").strip()
        try:
            # QLocale's toDouble handles thousands/decimal separators based on locale
            num, ok = self.indonesian_locale.toDouble(cleaned_text)
            if ok:
                return num
            else:
                return 0.0
        except (ValueError, TypeError):
            return 0.0

    def get_numeric_value(self):
        # Return the internally stored numeric value
        return self._numeric_value

    def set_numeric_value(self, value):
        if value is None:
            value = 0.0
        new_numeric_value = float(value)
        if self._numeric_value != new_numeric_value:
            self._numeric_value = new_numeric_value
            # Update the displayed text with the formatted numeric value
            super().setText(self._format_value_for_display(self._numeric_value))

    # This is the property QDataWidgetMapper will use to get/set the numeric value
    numeric_value = pyqtProperty(float, get_numeric_value, set_numeric_value, user=True)

    def _on_editing_finished(self):
        # When editing finishes, parse the current display text, update internal numeric value,
        # then reformat the display text to ensure consistency (e.g., if user types 1000 without separators)
        current_display_text = self.text()
        parsed_value = self._get_numeric_from_display_text(current_display_text)
        self.set_numeric_value(parsed_value) # This will re-trigger setText via the property setter


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
        self.btn_save = QPushButton("Simpan")
        self.btn_cancel = QPushButton("Batal")

        self.btn_add.clicked.connect(self.add_record)
        self.btn_delete.clicked.connect(self.delete_record)
        self.btn_save.clicked.connect(self.save_record)
        self.btn_cancel.clicked.connect(self.cancel_edit)

        action_layout.addWidget(self.btn_add)
        action_layout.addWidget(self.btn_delete)
        action_layout.addWidget(self.btn_save)
        action_layout.addWidget(self.btn_cancel)
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
            # Revert to QSqlRelationalTableModel as it provides proper data for id_pinjaman
            self.model = QSqlRelationalTableModel()
            self.model.setTable(table_name)
            # Define relation for id_pinjaman to pinjaman to allow QDataWidgetMapper to get the ID
            # Although we'll use MappingComboBox for display, this ensures the model is correct
            self.model.setRelation(1, QSqlRelation("pinjaman", "id_pinjaman", "id_pinjaman"))
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

    def _load_pinjaman_with_peminjam_names_to_combo(self, combo_box):
        """Helper to load pinjaman IDs with peminjam names into a QComboBox."""
        combo_box.clear()
        combo_box.addItem("Pilih Pinjaman", None) # Add a placeholder
        query = QSqlQuery(QSqlDatabase.database())
        query.exec("SELECT p.id_pinjaman, p.jumlah_pinjaman, pm.nama FROM pinjaman p JOIN peminjam pm ON p.id_peminjam = pm.id_peminjam ORDER BY p.id_pinjaman")
        
        while query.next():
            loan_id = query.value(0)
            amount = query.value(1)
            peminjam_name = query.value(2)
            display_text = f"ID: {loan_id} - {peminjam_name} (Rp {amount:,.0f})"
            combo_box.addItem(display_text, loan_id) # text=descriptive string, data=id_pinjaman

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
            
            # Special handling for id_pinjaman in cicilan table
            elif self.current_table == "cicilan" and col_name and col_name.lower() == 'id_pinjaman':
                field = MappingComboBox() # Use custom MappingComboBox
                self._load_pinjaman_with_peminjam_names_to_combo(field)
                self.fields[col_name] = field
                self.form_layout.addRow("ID Pinjaman (Peminjam):", field)
                self.mapper.addMapping(field, i, b"currentData_property") # Map to custom property
            
            # Foreign key id_peminjam - tampilkan sebagai ComboBox dengan nama
            elif col_name and col_name.lower() == 'id_peminjam':
                field = QComboBox()
                # Load data peminjam
                query = QSqlQuery(QSqlDatabase.database())
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
                field = CurrencyLineEdit()
                self.fields[col_name] = field
                self.form_layout.addRow(col_name + ":", field)
                self.mapper.addMapping(field, i, b"numeric_value")

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
        """Membuka dialog untuk menambah record baru, sesuai dengan tabel yang sedang aktif"""
        dialog = AddDataDialog(self, table_type=self.current_table) # Pass current_table
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
            self.model.setData(self.model.index(current_row, 1), id_peminjam) # Column 1 is id_peminjam

        # Handle save for id_pinjaman in cicilan table
        elif self.current_table == "cicilan" and 'id_pinjaman' in self.fields:
            combo = self.fields['id_pinjaman']
            id_pinjaman = combo.currentData()
            current_row = self.mapper.currentIndex()
            # Assuming id_pinjaman is column 1 in the cicilan table for data mapping
            self.model.setData(self.model.index(current_row, 1), id_pinjaman)


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