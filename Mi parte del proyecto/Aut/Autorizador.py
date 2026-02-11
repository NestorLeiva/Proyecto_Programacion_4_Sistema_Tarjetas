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
    # Si viene como bytes de la DB, lo decodificamos
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
        # Si el PIN ya es binario (de la DB), no necesitamos b64decode
        cipher = AES.new(KEY, AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(pin_binario), AES.block_size)
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"Error descifrado: {e}")
        return None

def cifrar_pin(pin_plano):
    cipher = AES.new(KEY, AES.MODE_ECB)
    return cipher.encrypt(pad(pin_plano.encode(), AES.block_size))

# =========================================================================
# MÓDULO: AUT 1 Y 2 - RETIROS Y CONSULTAS (TRAMA 50 CHARS)
# =========================================================================
def procesar_retiro_consulta(trama):
    try:
        # 1. RECEPCIÓN Y DESGLOSE (Índices para cuenta de 23 dígitos)
        # Trama C#: Tipo(1) + Cuenta(23) + Tarjeta(19) + Monto(8) + PIN(4)
        tipo = trama[0:1]
        n_cuenta = trama[1:24].strip()      # 23 caracteres
        n_tarjeta = trama[24:43].strip()    # 19 caracteres
        monto_raw = trama[43:51]            # 8 caracteres
        pin_raw = trama[51:55]              # 4 caracteres

        # DEFINICIÓN DE MONTO_F (Para uso en bitácora y lógica)
        monto_f = float(monto_raw) / 100.0  # Se define aquí para que esté disponible abajo
        
        # Registro inicial en bitácora (AUT4)
        registrar_evento_aut4(n_tarjeta, 1, f"SOLICITUD_{'RETIRO' if tipo=='1' else 'CONSULTA'}", monto_f)

        # 2. PREPARACIÓN PARA CORE JAVA (Sincronizado con Java Substring 1, 24)
        cod_auth = str(random.randint(10000000, 99999999))
        
        # Estructura que Java espera: Tipo(1) + Cuenta(23) + Tarjeta(19) + Auth(8) + Monto(8)
        trama_java = f"{tipo}{n_cuenta.ljust(23)}{n_tarjeta.ljust(19)}{cod_auth}{monto_raw}"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_java:
            s_java.connect(('127.0.0.1', 5000))
            s_java.sendall((trama_java + "\n").encode())
            resp_core = s_java.recv(1024).decode().strip()

        # 3. PROCESAMIENTO DE RESPUESTA
        if "OK" in resp_core:
            registrar_evento_aut4(n_tarjeta, 1, "TRANSACCION_EXITOSA", monto_f)
            res = {"estado": "APROBADO", "codigo_autorizacion": cod_auth}
            
            # Si es consulta, extraemos el saldo que devuelve Java
            if tipo == "2": 
                # Java devuelve "OK" + 19 dígitos de saldo
                res["saldo"] = float(resp_core[2:]) / 100.0
            return res
        
        # Si el Core Java rechaza (ej. CUENTA_NO_EXISTE)
        registrar_evento_aut4(n_tarjeta, 1, f"RECHAZADO_{resp_core}")
        return {"estado": "RECHAZADO", "mensaje": resp_core}

    except Exception as e:
        print(f"Error en procesamiento: {e}")
        return {"estado": "ERROR", "mensaje": str(e)}

# =========================================================================
# MÓDULO: AUT 3 - CAMBIO DE PIN (SOPORTE VARBINARY)
# =========================================================================
def procesar_cambio_pin(datos):
    n_tarjeta = datos.get("numero_tarjeta", "")
    registrar_evento_aut4(n_tarjeta, datos.get("id_cajero", 0), "SOLICITUD_CAMBIO_PIN")
    
    cursor = None
    try:
        if not Conexion.conectar(): return {"estado": "ERROR", "mensaje": "DB Error"}
        cursor = Conexion.conn.cursor(dictionary=True)

        # Usamos BINARY para la comparación si es necesario
        query = "SELECT id_tarjeta, pin FROM tarjeta WHERE numero_tarjeta = %s"
        cursor.execute(query, (n_tarjeta,))
        fila = cursor.fetchone()
        
        if not fila: return {"estado": "ERROR", "mensaje": "No existe tarjeta"}
        
        # El PIN en DB es VARBINARY, viene como objeto de bytes
        pin_db_binario = fila["pin"]
        
        if descifrar_pin(pin_db_binario) != datos["pin_actual"]:
            registrar_evento_aut4(n_tarjeta, datos["id_cajero"], "CAMBIO_PIN_FALLIDO_PIN_INC")
            return {"estado": "ERROR", "mensaje": "PIN actual incorrecto"}

        nuevo_pin_binario = cifrar_pin(datos["pin_nuevo"])
        cursor.execute("UPDATE tarjeta SET pin = %s WHERE id_tarjeta = %s", (nuevo_pin_binario, fila["id_tarjeta"]))
        
        codigo_p = f"PIN{datetime.now().strftime('%H%M%S')}"
        # Ajuste: El id_tipo_transaccion para cambios suele ser distinto, usamos el que tengas en DB
        cursor.execute("""INSERT INTO autorizacion 
            (codigo_autorizacion, id_tarjeta, id_cajero, id_tipo_transaccion, monto, estado, fecha_solicitud, respuesta) 
            VALUES (%s, %s, %s, (SELECT id_tipo_transaccion FROM tipo_transaccion WHERE codigo_tipo='RETIRO' LIMIT 1), 0, 'APROBADA', NOW(), 'OK')""", 
            (codigo_p, fila["id_tarjeta"], datos["id_cajero"]))
        
        Conexion.conn.commit()
        registrar_evento_aut4(n_tarjeta, datos["id_cajero"], "CAMBIO_PIN_EXITOSO")
        return {"estado": "OK", "mensaje": "PIN actualizado correctamente", "codigo_autorizacion": codigo_p}
    except Exception as e:
        return {"estado": "ERROR", "mensaje": f"Error interno: {str(e)}"}
    finally:
        if cursor: cursor.close()

# =========================================================================
# SERVIDOR
# =========================================================================
def manejar_cliente(conn, addr):
    try:
        data = conn.recv(4096).decode('utf-8').strip()
        if not data: return
        
        if data.startswith('{'): 
            respuesta = procesar_cambio_pin(json.loads(data))
        else: 
            respuesta = procesar_retiro_consulta(data)
            
        conn.sendall(json.dumps(respuesta).encode('utf-8'))
    except Exception as e:
        print(f"Error manejando cliente: {e}")
    finally:
        conn.close()

def iniciar_servidor():
    threading.Thread(target=worker_bitacora, daemon=True).start()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 5001))
    server.listen(10)
    
    print("====================================================")
    print("  SERVIDOR AUTORIZADOR INTEGRADO ACTIVO")
    print("   Puerto Escucha (C#): 5001")
    print("   Puerto Core (Java): 5000")
    print("====================================================")
    
    while True:
        conn, addr = server.accept()
        threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    iniciar_servidor()