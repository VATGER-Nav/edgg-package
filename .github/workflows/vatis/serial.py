import json
from datetime import datetime
import sys

def main():
    file_path = "EDGG/ATIS/vATIS Profile - EDGG D-ATIS.json"

    with open(file_path, "r") as f:
        data = json.load(f)

    current_serial = int(data.get("updateSerial", 0))
    today = datetime.now().strftime("%Y%m%d")
    current_date = int(str(current_serial)[:8])
    current_count = int(str(current_serial)[8:])

    if current_date == int(today):
        if current_count >= 99:
            print("Error: Daily counter has reached its maximum value of 99.")
            sys.exit(1)
        new_serial = current_serial + 1
    else:
        new_serial = int(today) * 100 + 1

    data["updateSerial"] = new_serial

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Updated Serial to {new_serial}")

if __name__ == "__main__":
    main()