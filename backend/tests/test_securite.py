"""Test de securite et de charge. Lancez d abord le backend, puis :  python -m tests.test_securite"""
import json, threading, time, urllib.request, urllib.error, collections
B="http://127.0.0.1:8000"
def req(path, method="GET", body=None, headers=None):
    data = json.dumps(body).encode() if isinstance(body,(dict,list)) else body
    r = urllib.request.Request(B+path, data=data, method=method, headers={"Content-Type":"application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(r, timeout=30) as resp: return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()
print("1. Requete inconnue / mal formee")
print("   route inconnue          ->", req("/api/nimporte")[0])
print("   JSON invalide           ->", req("/api/inscription","POST",b"{pas du json")[0])
print("   champ manquant          ->", req("/api/inscription","POST",{"nom":"x"})[0])
print("   profil inconnu          ->", req("/api/inscription","POST",{"email":"a@b.co","profil":"hack"})[0])
print("   nom de 5000 caracteres  ->", req("/api/inscription","POST",{"nom":"x"*5000,"email":"a@b.co","profil":"dev"})[0])
print("   corps de 1 Mo           ->", req("/api/inscription","POST",b"x"*1_000_000)[0])
print("   id pas un nombre        ->", req("/api/offres/abc")[0])
s,b = req("/api/offres?q=%27%20OR%201%3D1%20--")
print("   injection SQL dans q    ->", s, "offres renvoyees:", len(json.loads(b)))
print("2. Desinscription")
print("   ancienne route par e-mail ->", req("/api/desinscription/a@b.co","DELETE")[0])
print("   faux token              ->", req("/api/desinscription?token=fauxfauxfauxfaux")[0])
print("3. Refresh")
print("   1er appel               ->", req("/api/refresh","POST")[0])
print("   2e appel tout de suite  ->", req("/api/refresh","POST")[0])
print("4. Anti-spam inscription (7 essais)")
print("   ", [req("/api/inscription","POST",{"email":f"u{i}@test.co","profil":"data-ia"})[0] for i in range(7)])
print("5. Charge : 400 requetes en parallele (50 threads)")
codes=collections.Counter(); t0=time.time()
def w():
    for _ in range(8): codes[req("/api/offres")[0]]+=1
ts=[threading.Thread(target=w) for _ in range(50)]; [t.start() for t in ts]; [t.join() for t in ts]
print("   ", dict(codes), f"en {time.time()-t0:.1f}s")
