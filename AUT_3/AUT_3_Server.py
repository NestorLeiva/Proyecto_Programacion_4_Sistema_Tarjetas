import socket
import json
import threading
from datetime import datetime
from mysql.connector import Error
from AUT_3_MySQL import Conexion  # clase de conexión MySQL

host = "localhost"
port = 9090


class AUT3Server:

    def __init__(self):
        # Conexión a la base de datos
        if not Conexion.conectar():
            raise RuntimeError("No se pudo conectar a la BD MySQL")

    # ===========================================
    #   validar datos y cambiar el PIN
    # ===========================================
    def validar_y_cambiar_pin(self, datos):
        cursor = None
        try:
            cursor = Conexion.conn.cursor()

            # campos obligatorios
            obligatorios = (
                "numero_tarjeta",
                "pin_actual",
                "pin_nuevo",
                "fecha_vencimiento",
                "cvv",
                "id_cajero"
            )

            for campo in obligatorios:
                if not datos.get(campo):
                    return {"estado": "ERROR", "mensaje": f"Falta el campo {campo}"}

            # buscar tarjeta
            cursor.execute("""
                SELECT id_tarjeta, pin, fecha_vencimiento, cvv, estado
                FROM tarjeta
                WHERE numero_tarjeta = %s
            """, (datos["numero_tarjeta"],))

            fila = cursor.fetchone()
            if not fila:
                return {"estado": "ERROR", "mensaje": "Tarjeta no existe"}

            id_tarjeta, pin_db, fecha_db, cvv_db, estado = fila

            if estado != "ACTIVA":
                return {"estado": "ERROR", "mensaje": "Tarjeta inactiva"}

            # validar PIN
            if pin_db.hex() != datos["pin_actual"]:
                return {"estado": "ERROR", "mensaje": "*** PIN INCORRECTO ***"}

            # validar fecha vencimiento
            if fecha_db != datos["fecha_vencimiento"]:
                return {"estado": "ERROR", "mensaje": "*** FECHA VENCIMIENTO INCORRECTA ***"}

            # validar CVV
            if cvv_db.hex() != datos["cvv"]:
                return {"estado": "ERROR", "mensaje": "*** CVV INCORRECTO ***"}

            # validar cajero
            cursor.execute(
                "SELECT id_cajero FROM cajero WHERE id_cajero = %s",
                (datos["id_cajero"],)
            )
            if not cursor.fetchone():
                return {"estado": "ERROR", "mensaje": "*** CAJERO INVÁLIDO ***"}

            # actualizar PIN
            cursor.execute("""
                UPDATE tarjeta
                SET pin = UNHEX(%s)
                WHERE id_tarjeta = %s
            """, (datos["pin_nuevo"], id_tarjeta))

            # registrar autorización
            codigo = f"PIN{datetime.now().strftime('%y%m%d%H%M%S')}"

            cursor.execute("""
                INSERT INTO autorizacion
                (codigo_autorizacion, id_tarjeta, id_tipo_transaccion,
                 monto, estado, fecha_solicitud, fecha_respuesta, respuesta)
                VALUES (%s, %s, %s, 0, 'APROBADA', NOW(), NOW(), 'OK')
            """, (codigo, id_tarjeta, datos["id_cajero"]))

            Conexion.conn.commit()

            return {
                "estado": "OK",
                "codigo_autorizacion": codigo
            }

        except Error as e:
            if Conexion.conn:
                Conexion.conn.rollback()
            return {"estado": "ERROR", "mensaje": f"Error BD: {e}"}

        finally:
            if cursor:
                cursor.close()

    # ===========================================
    #   manejar clientes
    # ===========================================
    def manejar_cliente(self, sock, addr):
        print(f"[CONECTADO] {addr}")
        try:
            data = sock.recv(4096).decode("utf-8")
            if not data:
                return

            trama = json.loads(data)
            respuesta = self.validar_y_cambiar_pin(trama)

            sock.send(json.dumps(respuesta).encode("utf-8"))

        except Exception as e:
            sock.send(json.dumps({
                "estado": "ERROR",
                "mensaje": str(e)
            }).encode("utf-8"))

        finally:
            sock.close()
            print(f"[DESCONECTADO] {addr}")

    # ===========================================
    #   iniciar servidor
    # ===========================================
    def iniciar_servidor(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)

        print(f"\n AUT3 corriendo en {host}:{port}")
        print(" Esperando cajeros... (Ctrl+C para detener)")

        try:
            while True:
                client, addr = server_socket.accept()
                thread = threading.Thread(
                    target=self.manejar_cliente,
                    args=(client, addr),
                    daemon=True
                )
                thread.start()

        except KeyboardInterrupt:
            print("\n Servidor detenido")

        finally:
            server_socket.close()
            Conexion.desconectar()


# ===========================================
#   MAIN
# ===========================================
if __name__ == "__main__":
    servidor = AUT3Server()
    servidor.iniciar_servidor()
