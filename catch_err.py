import traceback

try:
    from backend.main import app
    print("Success")
except Exception as e:
    with open("err.txt", "w") as f:
        f.write(traceback.format_exc())
    print("Error written to err.txt")
