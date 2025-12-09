import sqlite3


def create_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS peminjam
                   (
                       id_peminjam
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       nama
                       TEXT
                       NOT
                       NULL,
                       alamat
                       TEXT
                       NOT
                       NULL,
                       no_telp
                       TEXT
                       NOT
                       NULL,
                       email
                       TEXT
                       NOT
                       NULL
                   )
                   ''')

    
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS pinjaman
                   (
                       id_pinjaman
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       id_peminjam
                       INTEGER
                       NOT
                       NULL,
                       jumlah_pinjaman
                       REAL
                       NOT
                       NULL,
                       tanggal_pinjam
                       TEXT
                       NOT
                       NULL,
                       tanggal_selesai
                       TEXT
                       NOT
                       NULL,
                       status
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       id_peminjam
                   ) REFERENCES peminjam
                   (
                       id_peminjam
                   )
                       )
                   ''')

    
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS cicilan
                   (
                       id_cicilan
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       id_pinjaman
                       INTEGER
                       NOT
                       NULL,
                       cicilan_ke
                       INTEGER
                       NOT
                       NULL,
                       jumlah_cicilan
                       REAL
                       NOT
                       NULL,
                       tanggal_bayar
                       TEXT,
                       status_bayar
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       id_pinjaman
                   ) REFERENCES pinjaman
                   (
                       id_pinjaman
                   )
                       )
                   ''')

    
    peminjam_data = [
        ('Budi Santoso', 'Jl. Merdeka No. 10, Surabaya', '081234567890', 'budi@email.com'),
        ('Siti Nurhaliza', 'Jl. Pahlawan No. 25, Surabaya', '081234567891', 'siti@email.com'),
        ('Ahmad Dahlan', 'Jl. Pemuda No. 5, Surabaya', '081234567892', 'ahmad@email.com'),
        ('Dewi Lestari', 'Jl. Diponegoro No. 15, Surabaya', '081234567893', 'dewi@email.com'),
        ('Eko Prasetyo', 'Jl. Sudirman No. 30, Surabaya', '081234567894', 'eko@email.com')
    ]
    cursor.executemany('INSERT INTO peminjam (nama, alamat, no_telp, email) VALUES (?, ?, ?, ?)', peminjam_data)

    
    pinjaman_data = [
        (1, 5000000, '2024-01-15', '2024-07-15', 'Aktif'),
        (1, 3000000, '2024-03-01', '2024-09-01', 'Lunas'),
        (2, 10000000, '2024-02-10', '2024-08-10', 'Aktif'),
        (3, 7500000, '2024-01-20', '2024-07-20', 'Aktif'),
        (4, 4000000, '2024-03-15', '2024-09-15', 'Lunas'),
        (5, 6000000, '2024-02-25', '2024-08-25', 'Aktif')
    ]
    cursor.executemany(
        'INSERT INTO pinjaman (id_peminjam, jumlah_pinjaman, tanggal_pinjam, tanggal_selesai, status) VALUES (?, ?, ?, ?, ?)',
        pinjaman_data)

    
    cicilan_data = [
        
        (1, 1, 833333, '2024-02-15', 'Lunas'),
        (1, 2, 833333, '2024-03-15', 'Lunas'),
        (1, 3, 833333, '2024-04-15', 'Lunas'),
        (1, 4, 833333, None, 'Belum Bayar'),
        (1, 5, 833333, None, 'Belum Bayar'),
        (1, 6, 833335, None, 'Belum Bayar'),
        
        (2, 1, 500000, '2024-04-01', 'Lunas'),
        (2, 2, 500000, '2024-05-01', 'Lunas'),
        (2, 3, 500000, '2024-06-01', 'Lunas'),
        (2, 4, 500000, '2024-07-01', 'Lunas'),
        (2, 5, 500000, '2024-08-01', 'Lunas'),
        (2, 6, 500000, '2024-09-01', 'Lunas'),
        
        (3, 1, 1666667, '2024-03-10', 'Lunas'),
        (3, 2, 1666667, '2024-04-10', 'Lunas'),
        (3, 3, 1666667, None, 'Belum Bayar'),
        (3, 4, 1666667, None, 'Belum Bayar'),
        (3, 5, 1666667, None, 'Belum Bayar'),
        (3, 6, 1666665, None, 'Belum Bayar'),
        
        (4, 1, 1250000, '2024-02-20', 'Lunas'),
        (4, 2, 1250000, '2024-03-20', 'Lunas'),
        (4, 3, 1250000, '2024-04-20', 'Lunas'),
        (4, 4, 1250000, None, 'Belum Bayar'),
        (4, 5, 1250000, None, 'Belum Bayar'),
        (4, 6, 1250000, None, 'Belum Bayar')
    ]
    cursor.executemany(
        'INSERT INTO cicilan (id_pinjaman, cicilan_ke, jumlah_cicilan, tanggal_bayar, status_bayar) VALUES (?, ?, ?, ?, ?)',
        cicilan_data)

    conn.commit()
    conn.close()
    print("Database berhasil dibuat: database.db")


if __name__ == "__main__":
    create_database()