import requests

r = requests.get('http://127.0.0.1:5000/get_state', params={'uuid': '1234'})
print(r.text)