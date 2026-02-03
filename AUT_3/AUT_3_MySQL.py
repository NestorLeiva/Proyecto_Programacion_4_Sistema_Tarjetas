import time
import mysql.connector
from mysql.connector import Error

database = "Sistema_Tarjetas"
server = "localhost"
password = "Nstrl0436Mysql*"
usuario = "root"

class Conexion:
    conn = None 
    
    @staticmethod
    def conectar():
        try:
            print("Intentando conectar...")  
            Conexion.conn = mysql.connector.connect(
                host=server,
                port=3306,
                user=usuario,
                password=password,
                database=database
            )
            print("*** CONEXION EXITOSA! ***")  
            print(f"   Base de datos: {database}")
            print(f"   Servidor: {server}:3306")
            return True
        except Error as e:
            print(f"ERROR DE CONEXION: {e}")
            return False
        # metodo para conectar a la base de datos
    
    @staticmethod
    def desconectar():
        try:
            if Conexion.conn and Conexion.conn.is_connected():
                Conexion.conn.close()
                print("*** CONEXION CERRADA! ***")  
            else:
                print("No habia conexion activa")
        except:
            print("Error al cerrar conexion")
        # metodo para desconectar de la base de datos

# ==============================
#       PRUEBA DE CONEXION    
# ==============================
if __name__ == "__main__":
    print("INICIANDO PROGRAMA...\n")
    
    if Conexion.conectar():
        time.sleep(2)
        Conexion.desconectar()
    else:
        print("No se pudo conectar")
    
    print("Programa terminado.")  