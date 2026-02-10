import socket
import json
import random
import mysql.connector
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

# --- CONFIGURACIÓN AES ---
KEY = b'1234567890123456' 

def descifrar_pin(pin_cifrado_base64):
    try:
        datos = base64.b64decode(pin_cifrado_base64)
        cipher = AES.new(KEY, AES.MODE_ECB)
        return unpad(cipher.decrypt(datos), AES.block_size).decode('utf-8')
    except: return None

# --- LÓGICA PRINCIPAL (TU CÓDIGO MEJORADO) ---
def procesar_transaccion(trama_desde_csharp):
    try:
        # 1. Descomponer la trama que viene de C#
        # C# envía: Tipo(1) + Cuenta(10) + Tarjeta(19) + Monto(8)
        tipo_trans = trama_desde_csharp[0:1]
        n_cuenta = trama_desde_csharp[1:11].strip()
        n_tarjeta = trama_desde_csharp[11:30].strip()
        monto_raw = trama_desde_csharp[30:38]
        monto_float = float(monto_raw) / 100

        # 2. Conexión MySQL (AUT1/AUT2)
        db = mysql.connector.connect(
            host="localhost", 
            user="root", 
            password="admin", 
            database="sistema_tarjetas"
        )
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT pin, estado FROM tarjeta WHERE numero_tarjeta = %s", (n_tarjeta,))
        tarjeta_db = cursor.fetchone()
        
        if not tarjeta_db:
            return json.dumps({"estado": "RECHAZADO", "mensaje": "Tarjeta no existe"})
        
        if tarjeta_db['estado'] != 'Activa':
            return json.dumps({"estado": "RECHAZADO", "mensaje": "Tarjeta bloqueada"})

        # 3. Validar PIN (Aquí podrías pedir el PIN desde C# y enviarlo en la trama si gustas)
        # Por ahora, para que el flujo siga, asumimos que el PIN es validado 
        # o puedes extraerlo de la trama si decides enviarlo desde C#.

        # 4. Re-construir trama para el CORE (Java)
        # Enviamos la misma trama que recibimos hacia el puerto 5000
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_java:
            s_java.connect(('127.0.0.1', 5000))
            s_java.sendall((trama_desde_csharp + "\n").encode())
            resp_core = s_java.recv(1024).decode().strip()

        # 5. Formatear Respuesta Final JSON para C#
        resultado = {
            "tarjeta": f"{n_tarjeta[:4]}********{n_tarjeta[-4:]}",
            "codigo_autorizacion": None,
            "saldo": None,
            "estado": "RECHAZADO"
        }

        if "OK" in resp_core:
            resultado["estado"] = "APROBADO"
            if tipo_trans == "1": # Retiro
                resultado["codigo_autorizacion"] = str(random.randint(10000000, 99999999))
                resultado["mensaje"] = "Retiro Exitoso"
            else: # Consulta
                resultado["saldo"] = float(resp_core[2:]) / 100
                resultado["mensaje"] = "Consulta Exitosa"
        else:
            resultado["mensaje"] = resp_core # Mensaje de error de Java

        return json.dumps(resultado, indent=4)

    except Exception as e:
        return json.dumps({"estado": "ERROR", "mensaje": str(e)})

# --- SERVIDOR PUENTE (EL QUE ESCUCHA A C#) ---
def iniciar_puente():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Escucha en el puerto 5001 (donde apunta tu C#)
    server_socket.bind(('127.0.0.1', 5001))
    server_socket.listen(5)
    
    print("PUENTE PYTHON: Escuchando a C# en el puerto 5001...")
    print("Conectado al CORE JAVA en el puerto 5000...")
    
    while True:
        conn, addr = server_socket.accept()
        with conn:
            data = conn.recv(1024).decode().strip()
            if data:
                print(f"Trama recibida de C#: {data}")
                # Llamamos a tu lógica de procesamiento
                respuesta_json = procesar_transaccion(data)
                # Enviamos el JSON de vuelta a C#
                conn.sendall(respuesta_json.encode())
                print(f"Respuesta enviada a C#.")

if __name__ == "__main__":
    iniciar_puente()