import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'indian_airports.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('PRAGMA integrity_check')
print('Integrity Check:', cur.fetchone()[0])

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = cur.fetchall()
print('\nTable Counts:')
for (t,) in tables:
    cur.execute(f'SELECT count(1) FROM "{t}"')
    cnt = cur.fetchone()[0]
    print(f'  {t}: {cnt:,}')

cur.execute('SELECT count(1) FROM bookings WHERE user_id NOT IN (SELECT id FROM users)')
orphan_bookings = cur.fetchone()[0]
print(f'\nOrphan Bookings: {orphan_bookings} (Must be 0)')

conn.close()

sz = os.path.getsize(db_path)
print(f'\nFinal File Size: {sz:,} bytes ({sz / 1024 / 1024:.2f} MB)')
