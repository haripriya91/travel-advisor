import time
from src.database import get_connection

start = time.perf_counter()

with get_connection() as connection:
    connected = time.perf_counter()

    connection.execute("SELECT 1").fetchone()
    queried = time.perf_counter()

print(f"Connection time: {connected - start:.3f} seconds")
print(f"Query time: {queried - connected:.3f} seconds")
print(f"Total time: {queried - start:.3f} seconds")