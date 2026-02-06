import socket
import mysql.connector
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import random # Para generar el código de autorización

# --- PARTE A: SEGURIDAD (AES) ---
class SecurityHelper:
    KEY = b'LlaveMaestra1234' # 16 bytes

    @staticmethod
    def cifrar(texto):
        cipher = AES.new(SecurityHelper.KEY, AES.MODE_ECB)
        ct_bytes = cipher.encrypt(pad(texto.encode(), 16))
        return base64.b64encode(ct_bytes).decode()

    @staticmethod
    def descifrar(texto_cifrado):
        det_bytes = base64.b64decode(texto_cifrado)
        cipher = AES.new(SecurityHelper.KEY, AES.MODE_ECB)
        return unpad(cipher.decrypt(det_bytes), 16).decode()

# --- PARTE B: COMUNICACIÓN CON JAVA ---
def enviar_a_core_java(trama):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 5000)) # IP y Puerto de tu Core Java
            s.sendall((trama + "\n").encode('utf-8'))
            return s.recv(1024).decode('utf-8').strip()
    except Exception as e:
        return f"ERROR_CONEXION"

# --- PARTE C: LÓGICA PRINCIPAL (AUT1 y AUT2) ---
def procesar_transaccion(n_tarjeta, pin_ingresado, monto, tipo_trans):
    try:
        # 1. Conexión a MySQL
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="admin",
            database="sistema_tarjetas"
        )
        cursor = db.cursor(dictionary=True)

        # 2. Buscar tarjeta con tus columnas exactas
        query = "SELECT pin, estado, numero_cuenta FROM tarjeta WHERE numero_tarjeta = %s"
        cursor.execute(query, (n_tarjeta,))
        tarjeta = cursor.fetchone()

        if not tarjeta:
            return "ERROR: Tarjeta inexistente"
        
        if tarjeta['estado'] != 'Activa':
            return "ERROR: Tarjeta bloqueada"

        # 3. Validar PIN (Descifrar el que está en la base de datos)
        pin_db = SecurityHelper.descifrar(tarjeta['pin'])
        if pin_ingresado != pin_db:
            return "ERROR: PIN incorrecto"

        # 4. Preparar trama para Java (CORE1)
        # Cuenta(10) + Tarjeta(19) + Monto(8)
        cuenta_str = str(tarjeta['numero_cuenta']).ljust(10)
        t_enmascarada = f"{n_tarjeta[:4]} {n_tarjeta[4:6]}** **** {n_tarjeta[12:]}".ljust(19)
        monto_str = str(int(float(monto) * 100)).zfill(8)
        
        trama_core = f"{tipo_trans}{cuenta_str}{t_enmascarada}{monto_str}"

        # 5. Llamar al Core en Java
        respuesta_core = enviar_a_core_java(trama_core)

        # 6. Lógica de AUT1 (Retiro): Si el core dice OK, generar código de 8 dígitos
        if tipo_trans == "1" and respuesta_core == "OK":
            codigo_auth = str(random.randint(10000000, 99999999))
            return f"APROBADA - COD: {codigo_auth}"
        
        return respuesta_core # Para consulta (AUT2) devolverá el saldo: OK000...

    except Exception as e:
        return f"ERROR: {str(e)}"
    finally:
        if 'db' in locals(): db.close()

        # --- PRUEBA DEL FLUJO COMPLETO ---
if __name__ == "__main__":
    # Prueba de Consulta (Tipo 2)
    print("Probando Autorizador...")
    res = procesar_transaccion("4567890123456789", "1234", 0, "2")
    print(f"Respuesta final: {res}")