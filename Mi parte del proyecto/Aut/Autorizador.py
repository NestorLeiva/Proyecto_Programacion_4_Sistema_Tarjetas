import socket
import json
import random
import threading
import mysql.connector
import base64
from queue import Queue
from datetime import datetime
from mysql.connector import Error
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad

# =========================================================================
# CONFIGURACIÓN GLOBAL
# =========================================================================
KEY = b'1234567890123456' 
DATABASE = "sistema_tarjetas"
SERVER = "localhost"
PASSWORD = "admin" 
USUARIO = "root"
RUTA_BITACORA = "bitacora_AUT4.txt"

class Conexion:
    conn = None 
    @staticmethod
    def conectar():
        try:
            if Conexion.conn is None or not Conexion.conn.is_connected():
                Conexion.conn = mysql.connector.connect(
                    host=SERVER, port=3306, user=USUARIO, 
                    password=PASSWORD, database=DATABASE
                )
            return True
        except Error as e:
            print(f"ERROR DB: {e}")
            return False

# =========================================================================
# MÓDULO: AUT 4 - BITÁCORA ASÍNCRONA
# =========================================================================
cola_bitacora = Queue()

def enmascarar_tarjeta(numero_tarjeta: str) -> str:
    if isinstance(numero_tarjeta, bytes):
        numero_tarjeta = numero_tarjeta.decode('utf-8', errors='ignore')
    digitos = ''.join(c for c in numero_tarjeta if c.isdigit())
    if len(digitos) >= 16:
        return f"{digitos[:4]} {digitos[4:6]}** **** {digitos[-4:]}"
    return "**** **** **** ****"

def worker_bitacora():
    while True:
        linea = cola_bitacora.get()
        try:
            with open(RUTA_BITACORA, "a", encoding="utf-8") as f:
                f.write(linea + "\n")
        finally:
            cola_bitacora.task_done()

def registrar_evento_aut4(tarjeta, cajero, tipo, monto=None):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    registro = {
        "tarjeta": enmascarar_tarjeta(tarjeta),
        "cajero": cajero,
        "tipo": tipo,
        "monto": f"{monto:.2f}" if monto else "0.00"
    }
    linea = f"{fecha}: {json.dumps(registro)}"
    cola_bitacora.put(linea)

# =========================================================================
# HERRAMIENTAS DE SEGURIDAD (Ajustadas para VARBINARY/Bytes)
# =========================================================================
def descifrar_pin(pin_binario):
    try:
        cipher = AES.new(KEY, AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(pin_binario), AES.block_size)
        return decrypted.decode('utf-8')
    except Exception as e:
        return None

def cifrar_pin(pin_plano):
    cipher = AES.new(KEY, AES.MODE_ECB)
    return cipher.encrypt(pad(pin_plano.encode(), AES.block_size))

# =========================================================================
# MÓDULO: AUT 1 Y 2 - RETIROS Y CONSULTAS (TRAMA DINÁMICA)
# =========================================================================
def procesar_retiro_consulta(trama):
    cursor = None
    try:
        tipo = trama[0:1]
        n_tarjeta = trama[1:20].strip()
        monto_raw = trama[20:28]
        pin_ingresado = trama[28:32]
        monto_f = float(monto_raw) / 100.0

        if not Conexion.conectar(): return {"estado": "ERROR", "mensaje": "DB Error"}
        cursor = Conexion.conn.cursor(dictionary=True)
        
        # Validar PIN y obtener cuenta
        cursor.execute("SELECT id_tarjeta, numero_cuenta, pin FROM tarjeta WHERE numero_tarjeta = %s", (n_tarjeta,))
        fila = cursor.fetchone()

        if not fila: return {"estado": "RECHAZADO", "mensaje": "Tarjeta No Existe"}
        if descifrar_pin(fila["pin"]) != pin_ingresado:
            registrar_evento_aut4(n_tarjeta, 1, "PIN_INCORRECTO", monto_f)
            return {"estado": "RECHAZADO", "mensaje": "PIN INCORRECTO"}

        # Llamada a Core Java
        cod_auth = str(random.randint(10000000, 99999999))
        trama_java = f"{tipo}{fila['numero_cuenta'].strip().ljust(23)}{n_tarjeta.ljust(19)}{cod_auth}{monto_raw}"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_java:
            s_java.connect(('127.0.0.1', 5000))
            s_java.sendall((trama_java + "\n").encode())
            resp_core = s_java.recv(1024).decode().strip()

        if "OK" in resp_core:
            # CORE 2: Registro en MySQL emparejado con tu script
            if tipo == "1":
                cursor.execute("""INSERT INTO movimiento_tarjeta 
                    (id_tarjeta, codigo_autorizacion, tipo_movimiento, monto, estado, fecha_movimiento) 
                    VALUES (%s, %s, 'RETIRO_EFECTIVO', %s, 'APROBADO', NOW())""",
                    (fila["id_tarjeta"], cod_auth, monto_f))
                Conexion.conn.commit()

            registrar_evento_aut4(n_tarjeta, 1, "TRANSACCION_EXITOSA", monto_f)
            res = {"estado": "APROBADO", "codigo_autorizacion": cod_auth}
            if tipo == "2": res["saldo"] = float(resp_core[2:]) / 100.0
            return res
        
        return {"estado": "RECHAZADO", "mensaje": resp_core}
    except Exception as e:
        return {"estado": "ERROR", "mensaje": str(e)}
    finally:
        if cursor: cursor.close()

# =========================================================================
# MÓDULO: AUT 3 - CAMBIO DE PIN
# =========================================================================
def procesar_cambio_pin(datos):
    n_tarjeta = datos.get("numero_tarjeta", "")
    cursor = None
    try:
        if not Conexion.conectar(): return {"estado": "ERROR", "mensaje": "DB Error"}
        cursor = Conexion.conn.cursor(dictionary=True)
        cursor.execute("SELECT id_tarjeta, pin FROM tarjeta WHERE numero_tarjeta = %s", (n_tarjeta,))
        fila = cursor.fetchone()
        
        if not fila or descifrar_pin(fila["pin"]) != datos["pin_actual"]:
            return {"estado": "RECHAZADO", "mensaje": "PIN INCORRECTO"}

        cursor.execute("UPDATE tarjeta SET pin = %s WHERE id_tarjeta = %s", (cifrar_pin(datos["pin_nuevo"]), fila["id_tarjeta"]))
        Conexion.conn.commit()
        registrar_evento_aut4(n_tarjeta, datos["id_cajero"], "CAMBIO_PIN_EXITOSO")
        return {"estado": "OK", "mensaje": "PIN actualizado"}
    except Exception as e:
        return {"estado": "ERROR", "mensaje": str(e)}
    finally:
        if cursor: cursor.close()

# =========================================================================
# SERVIDOR
# =========================================================================
def manejar_cliente(conn, addr):
    try:
        data = conn.recv(4096).decode('utf-8').strip()
        if not data: return
        respuesta = procesar_cambio_pin(json.loads(data)) if data.startswith('{') else procesar_retiro_consulta(data)
        conn.sendall(json.dumps(respuesta).encode('utf-8'))
    finally:
        conn.close()

def iniciar_servidor():
    threading.Thread(target=worker_bitacora, daemon=True).start()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 5001))
    server.listen(10)
    print("AUTORIZADOR ACTIVO - PUERTO 5001")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    iniciar_servidor()