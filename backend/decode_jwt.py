# backend/decode_jwt.py
"""
Utilitário de depuração: decodifica um JWT sem verificar assinatura
(e útil para inspecionar sub, iat e exp).
Uso: python backend/decode_jwt.py <TOKEN>
"""

import sys
import time
import jwt

def main():
    if len(sys.argv) < 2:
        print("Uso: python backend/decode_jwt.py <TOKEN>")
        sys.exit(1)
    token = sys.argv[1]
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        print("payload:", payload)
        print("now:", int(time.time()), "exp:", payload.get("exp"))
    except Exception as e:
        print("decode error:", e)

if __name__ == "__main__":
    main()
