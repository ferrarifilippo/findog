import requests
payload = {'uuid': '0001', 'attribute':'state' }
page = "get_dog"
r = requests.post('http://172.20.10.13:5000/set_dog', data={'uuid': '0001', 'attribute': 'state', 'val': 'A'})
print(r.text)