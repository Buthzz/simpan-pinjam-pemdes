from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTableView, QLabel, QLineEdit, QComboBox,
                             QStyledItemDelegate, QStyleOptionViewItem)
from PyQt6.QtCore import Qt, QModelIndex, QLocale
from PyQt6.QtSql import QSqlQueryModel, QSqlQuery, QSqlDatabase 



class EditableSqlQueryModel(QSqlQueryModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = QSqlDatabase.database() 

    def flags(self, index):
        
        
        if index.column() == 1: 
            return super().flags(index) | Qt.ItemFlag.ItemIsEditable
        return super().flags(index)

    def setData(self, index, value, role):
        if index.column() == 1 and role == Qt.ItemDataRole.EditRole:
            if not self._db.isOpen():
                print("Database not open in EditableSqlQueryModel.setData")
                return False

            
            id_pinjaman_index = self.index(index.row(), 0) 
            id_pinjaman = self.data(id_pinjaman_index)

            
            new_id_peminjam = value 

            
            query = QSqlQuery(self._db)
            query.prepare("UPDATE pinjaman SET id_peminjam = ? WHERE id_pinjaman = ?")
            query.addBindValue(new_id_peminjam)
            query.addBindValue(id_pinjaman)

            if query.exec():
                
                self.setQuery(self.query().lastQuery()) 
                return True
            else:
                print(f"Failed to update pinjaman.id_peminjam: {query.lastError().text()}")
                return False
        return super().setData(index, value, role)

    def select(self):
        
        self.setQuery(self.query().lastQuery())



class PeminjamDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = QSqlDatabase.database() 
        self._peminjam_data = self._load_peminjam_data()

    def _load_peminjam_data(self):
        
        data = {}
        query = QSqlQuery(self._db)
        query.exec("SELECT id_peminjam, nama FROM peminjam ORDER BY nama")
        while query.next():
            data[query.value(1)] = query.value(0) 
        return data

    def createEditor(self, parent, option, index):
        if index.column() == 1: 
            editor = QComboBox(parent)
            editor.addItems(sorted(self._peminjam_data.keys()))
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if index.column() == 1: 
            current_name = index.model().data(index, Qt.ItemDataRole.EditRole)
            if current_name in self._peminjam_data:
                editor.setCurrentText(current_name)
            else:
                editor.setCurrentIndex(0) 
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == 1: 
            selected_name = editor.currentText()
            selected_id = self._peminjam_data.get(selected_name)
            if selected_id is not None:
                
                model.setData(index, selected_id, Qt.ItemDataRole.EditRole)
            else:
                print(f"Warning: Selected name '{selected_name}' not found in peminjam data.")
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)



class CurrencyDelegate(QStyledItemDelegate):

    def displayText(self, value, qt_locale):
        try:
            
            num = float(str(value))

            
            indonesian_locale = QLocale(QLocale.Language.Indonesian, QLocale.Country.Indonesia)

            
            formatted_string = indonesian_locale.toString(num, 'f', 0)
            return f"Rp {formatted_string}"

        except Exception as e:
            
            
            
            print(f"DEBUG: Error in CurrencyDelegate for value '{value}': {e}") 
            return str(value)



class TableViewWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        
        filter_layout = QHBoxLayout()

        
        filter_layout.addWidget(QLabel("Filter Peminjam:"))
        self.filter_peminjam = QLineEdit()
        self.filter_peminjam.setPlaceholderText("Ketik nama peminjam...")
        self.filter_peminjam.textChanged.connect(self.update_query)
        filter_layout.addWidget(self.filter_peminjam)

        
        filter_layout.addWidget(QLabel("Filter Status:"))
        self.filter_status = QComboBox()
        self.filter_status.addItems(["Semua", "Aktif", "Lunas", "Belum Bayar"])
        self.filter_status.currentTextChanged.connect(self.update_query)
        filter_layout.addWidget(self.filter_status)

        layout.addLayout(filter_layout)

        
        self.table = QTableView()
        self.table.setSortingEnabled(True)

        
        self.peminjam_delegate = PeminjamDelegate(self)
        
        self.table.setItemDelegateForColumn(1, self.peminjam_delegate)

        
        self.currency_delegate = CurrencyDelegate()
        
        self.table.setItemDelegateForColumn(3, self.currency_delegate)
        self.table.setItemDelegateForColumn(8, self.currency_delegate)

        layout.addWidget(self.table)

        
        self.model = EditableSqlQueryModel()
        self.table.setModel(self.model)

        self.setLayout(layout)
        self.update_query()

    def update_query(self):
        nama_filter = self.filter_peminjam.text()
        status_filter = self.filter_status.currentText()

        
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

        
        if nama_filter:
            query_str += f" AND peminjam.nama LIKE '%{nama_filter}%'"

        
        if status_filter != "Semua":
            if status_filter in ["Aktif", "Lunas"]:
                query_str += f" AND pinjaman.status = '{status_filter}'"
            else:
                query_str += f" AND cicilan.status_bayar = '{status_filter}'"

        query_str += " ORDER BY pinjaman.id_pinjaman, cicilan.cicilan_ke"

        self.model.setQuery(query_str)

        
        
        
