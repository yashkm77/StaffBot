import requests

URL = "https://keyframe-staff-list.com/staff/my-hero-academia"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/26.0 Safari/605.1.15"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

response = requests.get(
    URL,
    headers=headers,
    timeout=30
)

print("Status:", response.status_code)
print("Length:", len(response.text))
print("Cloudflare:", "Just a moment..." in response.text)

if response.status_code == 200:
    print("SUCCESS - Python can access the page!")
else:
    print("Python was blocked.")