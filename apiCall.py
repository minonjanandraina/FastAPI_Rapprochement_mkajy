import http.client
import json





def transformTangoTransaction(date):
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    payload = json.dumps({
    "requestDate": date
    })
    headers = {
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/transformTangoTransaction", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
    
def transformPicoTransaction(date):
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    payload = json.dumps({
    "requestDate": date
    })
    headers = {
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/transformPicoTransaction", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

def transformOMTransaction(date):
    conn = http.client.HTTPConnection("127.0.0.1", 8000) 
    payload = json.dumps({
    "requestDate": date
    })
    headers = {
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/transformOMTransaction", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
    
def transformAMS(date):
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    payload = json.dumps({
    "requestDate": date
    })
    headers = {
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/transformAMS", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8")) 
    
def generateOM(date):
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    payload = json.dumps({
    "requestDate": date
    })
    headers = {
    'Content-Type': 'application/json'
    }
    print(payload)
    conn.request("POST", "/generateOMMapping", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
    
def generateFRONT(date):
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    payload = json.dumps({
    "requestDate": date
    })
    headers = {
    'Content-Type': 'application/json'
    }
    print(payload)
    conn.request("POST", "/generateFrontTrx", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

def generateGL(date):
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    payload = json.dumps({
    "requestDate": date
    })
    headers = {
    'Content-Type': 'application/json'
    }
    print(payload)
    conn.request("POST", "/generateGLTrx", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


def reconcile(date):
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    payload = json.dumps({
    "requestDate": date
    })
    headers = {
    'Content-Type': 'application/json',
    }
    print(payload)
    conn.request("POST", "/reconcile", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
    
                                      
                                      
list_date=['2026-04-11'
           ]



for d in list_date:
    print("\n" + "=" * 60)
    print(f"📅 TRAITEMENT DATE : {d}")

    print("=" * 60)
    
    print(f"🔄 transformTangoTransaction → {d}")
    transformTangoTransaction(d)

    print(f"🔄 transformPicoTransaction → {d}")
    transformPicoTransaction(d)
    
    print(f"🔄 transformOMTransaction → {d}")
    transformOMTransaction(d)
   
    print(f"🔄 transformAMS → {d}")
    transformAMS(d)
    
    print(f"📤 reconciliation start → {d}")

    reconcile(d)

    print(f"✅ FIN DATE : {d}")



