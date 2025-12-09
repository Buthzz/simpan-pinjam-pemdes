from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTableView, QLabel, QLineEdit, QComboBox,
                             QStyledItemDelegate, QStyleOptionViewItem)
from PyQt6.QtCore import Qt, QModelIndex, QLocale
from PyQt6.QtSql import QSqlQueryModel, QSqlQuery, QSqlDatabase # Import QSqlDatabase for the delegate and model


# --- Custom Editable QSqlQueryModel --- 
class EditableSqlQueryModel(QSqlQueryModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = QSqlDatabase.database() # Get the default database connection

    def flags(self, index):
        # Make "Nama Peminjam" column editable
        # Column index for "Nama Peminjam" is 1 based on the current query
        if index.column() == 1: # Assuming "Nama Peminjam" is the second column (index 1)
            return super().flags(index) | Qt.ItemFlag.ItemIsEditable
        return super().flags(index)

    def setData(self, index, value, role):
        if index.column() == 1 and role == Qt.ItemDataRole.EditRole:
            if not self._db.isOpen():
                print("Database not open in EditableSqlQueryModel.setData")
                return False

            # Get the current ID Pinjaman for the row being edited
            id_pinjaman_index = self.index(index.row(), 0) # "ID Pinjaman" is the first column (index 0)
            id_pinjaman = self.data(id_pinjaman_index)

            # Get the new Peminjam ID from the selected 'value' (which is the Peminjam ID)
            new_id_peminjam = value # The delegate will pass the ID, not the name

            # Update the pinjaman table
            query = QSqlQuery(self._db)
            query.prepare("UPDATE pinjaman SET id_peminjam = ? WHERE id_pinjaman = ?")
            query.addBindValue(new_id_peminjam)
            query.addBindValue(id_pinjaman)

            if query.exec():
                # Refresh the model to show the updated data
                self.setQuery(self.query().lastQuery()) # Re-execute the original query
                return True
            else:
                print(f"Failed to update pinjaman.id_peminjam: {query.lastError().text()}")
                return False
        return super().setData(index, value, role)

    def select(self):
        # Re-execute the current query
        self.setQuery(self.query().lastQuery())


# --- Custom PeminjamDelegate --- 
class PeminjamDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = QSqlDatabase.database() # Get the default database connection
        self._peminjam_data = self._load_peminjam_data()

    def _load_peminjam_data(self):
        # Load all peminjam (id, nama) into a dictionary for quick lookup
        data = {}
        query = QSqlQuery(self._db)
        query.exec("SELECT id_peminjam, nama FROM peminjam ORDER BY nama")
        while query.next():
            data[query.value(1)] = query.value(0) # name: id
        return data

    def createEditor(self, parent, option, index):
        if index.column() == 1: # "Nama Peminjam" column
            editor = QComboBox(parent)
            editor.addItems(sorted(self._peminjam_data.keys()))
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if index.column() == 1: # "Nama Peminjam" column
            current_name = index.model().data(index, Qt.ItemDataRole.EditRole)
            if current_name in self._peminjam_data:
                editor.setCurrentText(current_name)
            else:
                editor.setCurrentIndex(0) # Default to first item
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == 1: # "Nama Peminjam" column
            selected_name = editor.currentText()
            selected_id = self._peminjam_data.get(selected_name)
            if selected_id is not None:
                # Pass the ID back to the model's setData method
                model.setData(index, selected_id, Qt.ItemDataRole.EditRole)
            else:
                print(f"Warning: Selected name '{selected_name}' not found in peminjam data.")
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# --- CurrencyDelegate (remains the same) --- 
class CurrencyDelegate(QStyledItemDelegate):
    """Delegate untuk format currency"""

    def displayText(self, value, qt_locale):
        try:
            # Ensure value is treated as a string before conversion, in case it's a QVariant or other object
            num = float(str(value))

            # Create a QLocale object for Indonesian (id_ID).
            indonesian_locale = QLocale(QLocale.Language.Indonesian, QLocale.Country.Indonesia)

            # Format as currency with no decimal digits.
            formatted_string = indonesian_locale.toString(num, 'f', 0)
            return f"Rp {formatted_string}"

        except Exception as e:
            # Fallback if conversion or formatting fails.
            # This is where "6e+06" would be returned if value was already that string
            # and the float conversion failed.
            print(f"DEBUG: Error in CurrencyDelegate for value '{value}': {e}") # Keep for debugging
            return str(value)


# --- TableViewWidget (modified) --- 
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

        # Set delegate for "Nama Peminjam" column
        self.peminjam_delegate = PeminjamDelegate(self)
        # Assuming "Nama Peminjam" is column index 1 (0-indexed)
        self.table.setItemDelegateForColumn(1, self.peminjam_delegate)

        # Set delegate untuk kolom currency
        self.currency_delegate = CurrencyDelegate()
        # Columns 3 and 8 for currency based on the query result
        self.table.setItemDelegateForColumn(3, self.currency_delegate)
        self.table.setItemDelegateForColumn(8, self.currency_delegate)

        layout.addWidget(self.table)

        # Model menggunakan EditableSqlQueryModel
        self.model = EditableSqlQueryModel()
        self.table.setModel(self.model)

        self.setLayout(layout)
        self.update_query()

    def update_query(self):
        """Update query berdasarkan filter - Signal textChanged"""
        nama_filter = self.filter_peminjam.text()
        status_filter = self.filter_status.currentText()

        # Query JOIN 3 tabel
        query_str = '''
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
            query_str += f" AND peminjam.nama LIKE '%{nama_filter}%'"

        # Terapkan filter status
        if status_filter != "Semua":
            if status_filter in ["Aktif", "Lunas"]:
                query_str += f" AND pinjaman.status = '{status_filter}'"
            else:
                query_str += f" AND cicilan.status_bayar = '{status_filter}'"

        query_str += " ORDER BY pinjaman.id_pinjaman, cicilan.cicilan_ke"

        self.model.setQuery(query_str)

        # Re-set delegates might be necessary if model is reset completely, but setQuery should be fine.
        # Ensure column indices are correct after any query changes if the order shifts.
        # For now, assuming fixed column indices.
