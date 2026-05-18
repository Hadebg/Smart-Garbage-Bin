import sqlite3

conn = sqlite3.connect("waste_data.db")
c = conn.cursor()

# Xóa tất cả bản ghi trong bảng
c.execute("DELETE FROM waste")

# Nếu muốn reset luôn id tự tăng:
c.execute("DELETE FROM sqlite_sequence WHERE name='waste'")

conn.commit()
conn.close()