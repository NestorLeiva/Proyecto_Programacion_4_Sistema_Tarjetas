import socket
import json
import datetime
from _mysql_connector import error
from AUT_3_MySQL import Conexion
# importo la clase Conexion de MySQL

host = "localhost"
port = 9090


# ===========================================
#   funcion para conectar a la Base de Datos
# ===========================================
class AUT3Server:
    def __init__(self):
        """uso la clase principal de Conexion a BD_MySQL"""
    if not Conexion.conectar():
        raise RuntimeError("No se pudo Conectar a la BD MySQL")
    """ hace un alto si existe un problema"""

# ===========================================
#       funcion para cambiar el pin
# ===========================================

def validar_y_cambiar_pin(self, datos):

    """
    Datos: dict con
    - numero_tarjeta (texto plano / hexadecimal)
    - pin_actual (hex del pin actual)
    - pin_nuevo (hex del nuevo pin)
    - fecha_vencimiento (YYYY-MM-DD)
    - CVV (hex)
    - id_cajero (int)
    """

    try:
        cursor = Conexion.conn.cursor()
        # valido los campos
        obligatorio = ("numero_tarjeta", "pin_actual", "pin_nuevo", "fecha_venciiento", "cvv", "id_cajero")

        for campo in obligatorio :
            if not datos.get(campo):
                return {"estado": "ERROR", "mensaje": f"Falta {campo}"}
        
        # busco la tarjeta activa
        cursor.execute(""" SELECT id_tarjeta, pin, fecha_vencimiento, cvv, estado FROM tarjeta WHERE numero_tarjeta = %s """, (datos["numero_tarjeta"],))
        fila = cursor.fetchone()
        if not fila:
            return{"estado": "ERROR", "mensaje": "Tarjeta NO Existe"}
        
        id_tarjeta, pin_db, fecha_db, cvv_db, estado = fila
        if estado != "ACTIVA":
            return {"estado": "ERROR", "mensaje": "Tarjeta Inactiva"}
        
        # valido el PIN actual 
        if pin_db.hex != datos["pin_actual"]:
            return {"estado": "ERROR", "mensaje": "***PIN INCORRECTO***"}
        
        # Valido la Fecha de vencimiento
        if cvv_db.hex() != datos["fecha_vencimiento"]:
            return {"estado": "ERROR", "mensaje": "***Fecha Vencimiento Incorrecta***"}
        
        # valido CVV

        if cvv_db.hex() != datos["cvv"]:
            return{"estado": "ERROR", "mensaje": "***CVV Incorrecto***"}
        
        # Valido el # de Cajero
        cursor.execute("SELECT id_cajero FROM cajero WHERE id_cajero = %s", (datos["id_cajero"],))
        if not cursor.fechtone():
            return{"estado": "ERROR", "mensaje": "***Cajero Invalido***"}

        # Actualizo el PIN
        cursor.execute(
            "UPDATE tarjeta SET pin = UNHEX(%s) WHERE id_tarjeta = %s", (datos["pin_nuevo"], id_tarjeta))
        
        # Registo la Autorizacion de Cambio de PIN
        codigo = f"PIN{datetime.now().strftime('%y%m%d%H%M%S')}"
        cursor.execute(""" INSERT INTO autorizacion (codigo_autorizacion, id_tarjeta, id_tipo_transaccion, monto, estado, fecha_solicitud, fecha_respuesta, respuesta) VALUES (%s,%s,%s, 3,0 'APROVADA', NOW(), NOW(), 'OK')
        """, (codigo, id_tarjeta,datos["id_cajero"]))

        Conexion.conn.commit()
        return {"estado": "OK", "codigo_autorizacion": codigo}
    
    except error as e:
        Conexion.conectar.rollback()
        return {"estado": "ERROR", "mensaje": f"ERROR Base Datos: {e}"}
    finally:
        cursor.close()


# ===========================================
#       funcion manejar los clientes 
# ===========================================


def manejar_cliente (self, sock, addr):
    print(f"[CONETADO] {addr}")
    try:
        data = sock.recv(4049).decode("utf-8")
        if not data:
            return
        trama = json.loads(data)                            # JSON que proviene del cajero
        respuesta = self.validar_y_cambiar_pin(trama)       # llama al metodo, valida y Genera la Respuesta
        sock.send(json.dumps(respuesta).encode("utf-8"))    # convierte la Respuesta Json, la codifica y la envia por el Socket
    except Exception as e:
        sock.send (json.dumps({"estado": "ERROR", "mensaje": str(e).encode("utf-8")}))
    finally:
        sock.close()
        print(f"[DESCONECTADO] {addr}")
        
