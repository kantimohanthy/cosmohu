import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

res = requests.get("https://www.pldspace.com", headers={"User-Agent": "Mozilla/5.0"}, verify=False, timeout=10)
print(f"PLD Space Status: {res.status_code} | Length: {len(res.text)}")
