import subprocess
import json


def get_staff_data_from_safari():
    script = r'''
tell application "Safari"
    tell front document
        return do JavaScript "
            (() => {
                const element = document.getElementById('staffListData');

                if (!element) {
                    return 'NOT_FOUND';
                }

                return element.textContent;
            })()
        "
    end tell
end tell
'''

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout.strip()


raw = get_staff_data_from_safari()

if raw == "NOT_FOUND":
    print("❌ staffListData not found")
    raise SystemExit(1)

print("Raw data length:", len(raw))

try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    print("❌ Could not parse JSON")
    print(e)
    print()
    print(raw[:500])
    raise SystemExit(1)

print("✅ staffListData found!")
print()
print("Title:", data.get("title"))
print()
print("Menus:")

for menu in data.get("menus", []):
    print(" -", menu.get("name"))