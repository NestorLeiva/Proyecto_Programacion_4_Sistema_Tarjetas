import socket
import json
import threading
from queue import Queue
from datetime import datetime
import os

# =========================================
# BITÁCORA AUT4 - INTEGRADA AL AUT3
# =========================================
# se crea una cola
cola_bitacora = Queue()
RUTA_BITACORA = "bitacora_AUT4.txt"
# archivo donde se guarda todas las transacciones

def enmascarar_tarjeta(numero_tarjeta: str) -> str:
    """Enmascara: 4111 11** **** 1111 / (4 primeros + 2 segundos + **** + 4 últimos)"""
    digitos = ''.join(c for c in numero_tarjeta if c.isdigit())
    if len(digitos) >= 16:
        parte1 = digitos[:4]      # 4111
        parte2 = digitos[4:6]     # 11
        parte3 = digitos[-4:]     # 1111
        return f"{parte1} {parte2}** **** {parte3}"
    return "**** **** **** ****"

def construir_registro_bitacora(tarjeta: str, cajero: int, cliente: str, tipo: str, monto: float = None):
    """
    Creo linea EXACTA del formato AUT4 
    "09/02/2026: {"tarjeta": "4111 11** **** 1111", "cajero": 1, "cliente": "CLI-123456", "tipo": "Retiro"}"
    """
    fecha = datetime.now().strftime("%d/%m/%Y")
    registro = {
        "tarjeta": enmascarar_tarjeta(tarjeta),
        "cajero": cajero,
        "cliente": cliente,
        "tipo": tipo
    }
    if monto is not None:
        registro["monto"] = f"{monto:.2f}"
    linea = f"{fecha}: {json.dumps(registro)}"
    return linea

def worker_bitacora():
    """Hilo en 2do plano para escribir bitacora 
    lee la cola y escribe secuencialmente al archivo """
    while True:
        linea = cola_bitacora.get()
        try:
            with open(RUTA_BITACORA, "a", encoding="utf-8") as f:
                f.write(linea + "\n")
        finally:
            cola_bitacora.task_done()

def registrar_bitacora(numero_tarjeta: str, id_cajero: int, id_cliente: str, tipo_transaccion: str, monto: float = None):
    """Encola bitacora (NO BLOQUEA servidor principal) 
    Se llama desde el manejador de CLientes
    """
    linea = construir_registro_bitacora(numero_tarjeta, id_cajero, id_cliente, tipo_transaccion, monto)
    cola_bitacora.put(linea)

# =========================================
# TU SERVIDOR AUT3 + BITACORA AUT4
# =========================================
def manejar_cliente(conn, addr):
    try:
        data = conn.recv(4096).decode('utf-8')
        datos = json.loads(data)
        print(f"[SERVIDOR] Recibido de {addr}: {datos}")
        
        numero_tarjeta = datos.get("numero_tarjeta", "")
        id_cajero = datos.get("id_cajero", 0)
        
        # ========================================
        # REGISTRAR BITACORA ANTES de cualquier validación (AUT4)
        # ========================================
        registrar_bitacora(
            numero_tarjeta=numero_tarjeta,
            id_cajero=id_cajero,
            id_cliente="Sistema_Tarjetas",  # Conexion con la BD
            tipo_transaccion="AUTORIZACION_INICIAL"
        )
        
        # ========================================
        #       VALIDACIONES AUT3 
        # ========================================
        if not datos.get("pin"):
            respuesta = {"estado": "ERROR", "mensaje": "Falta el campo pin_nuevo"}
            conn.send(json.dumps(respuesta).encode('utf-8'))
            return
            
        if not datos.get("pin_nuevo"):
            respuesta = {"estado": "ERROR", "mensaje": "Falta el campo pin_nuevo"}
            conn.send(json.dumps(respuesta).encode('utf-8'))
            return
        
        # Datos de prueba ORIGINALES que ya tenías funcionando
        datos_prueba = {
            "4111-1111-1111-1111": {"pin": "1234"},
            "4111-2222-2222-2222": {"pin": "5678"},
            "4111-3333-3333-3333": {"pin": "9999"},
            "4111-4444-4444-4444": {"pin": "4321"},
            "4111-5555-5555-5555": {"pin": "8888"}
        }
        
        pin = datos["pin"]
        if numero_tarjeta in datos_prueba and datos_prueba[numero_tarjeta]["pin"] == pin:
            # ¡ÉXITO! Registrar bitácora de éxito
            registrar_bitacora(
                numero_tarjeta=numero_tarjeta,
                id_cajero=id_cajero,
                id_cliente="CLI-123456",
                tipo_transaccion="AUTORIZACION_EXITOSA"
            )
            respuesta = {"estado": "OK", "codigo_autorizacion": "AUTH001"}
        else:
            # PIN incorrecto - registrar en bitácora
            registrar_bitacora(
                numero_tarjeta=numero_tarjeta,
                id_cajero=id_cajero,
                id_cliente="CLI-123456",
                tipo_transaccion="PIN_INCORRECTO"
            )
            respuesta = {"estado": "ERROR", "mensaje": "*** PIN INCORRECTO ***"}
        
        conn.send(json.dumps(respuesta).encode('utf-8'))
        print(f"[SERVIDOR] Respuesta: {respuesta}")
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        conn.send(json.dumps({"estado": "ERROR", "mensaje": error_msg}).encode('utf-8'))
    finally:
        conn.close()

def servidor_aut3_aut4():
    # ========================================
    # INICIALIZAR BITACORA AUT4
    # ========================================
    if not os.path.exists(RUTA_BITACORA):
        with open(RUTA_BITACORA, "w") as f:
            f.write("BITACORA AUT4 INICIADA\n")
    
    hilo_bitacora = threading.Thread(target=worker_bitacora, daemon=True)
    hilo_bitacora.start()
    print(" [AUT3+AUT4] Servidor con BITACORA activa en 'bitacora.txt'")
    
    # ========================================
    # TU SERVIDOR SOCKET ORIGINAL (AUT3)
    # ========================================
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 9090))
    server.listen(5)
    
    print(" [AUT3+AUT4] Escuchando en localhost:9090")
    print(" [AUT4] Bitacora registrando TODAS las transacciones")
    
    while True:
        conn, addr = server.accept()
        threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    servidor_aut3_aut4()
