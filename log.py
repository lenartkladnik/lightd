import utime

def log(msg):
    try:
        timestamp = utime.time()
        ln = f"[{timestamp}] {msg}\n"

        print(ln.strip())

        with open("log", "a") as f:
            f.write(ln)

    except Exception as e:
        print(f"Failed to log '{e}'.")
