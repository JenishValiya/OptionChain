import sqlite3
import pandas as pd

# Connect to DB
conn = sqlite3.connect("dashboard_data.db")

# View snapshot table
snapshot = pd.read_sql("SELECT * FROM nifty_snapshot", conn)
print("SNAPSHOT DATA:")
print(snapshot.tail())

# View option chain table
option_chain = pd.read_sql("SELECT * FROM option_chain LIMIT 10", conn)
print("\nOPTION CHAIN DATA:")
print(option_chain.tail())

conn.close()
