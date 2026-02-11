import socket
import mysql.connector
import sys

def probar_diagnostico():
    print("=== INICIANDO DIAGNÓSTICO DE CONEXIONES ===")

    # 1. PRUEBA DE CONEXIÓN A MYSQL (Sistema de Tarjetas)
    print("\n[1/3] Probando conexión a MySQL...")
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",      # Cambia por tu usuario de MySQL
            password="admin", # Cambia por tu contraseña de MySQL
            database="sistema_tarjetas"
        )
        if db.is_connected():
            print("✅ ÉXITO: Conexión a MySQL establecida.")
            db.close()
    except Exception as e:
        print(f"❌ ERROR en MySQL: {e}")

    # 2. PRUEBA DE DISPONIBILIDAD DEL CORE (Socket Java)
    print("\n[2/3] Probando puerto del Core Java (Socket)...")
    HOST = '127.0.0.1'
    PORT = 5000
    try:
        # Intentamos abrir el socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(2) # 2 segundos de espera
        result = test_socket.connect_ex((HOST, PORT))
        
        if result == 0:
            print(f"✅ ÉXITO: El Core Java está escuchando en el puerto {PORT}.")
        else:
            print(f"❌ ERROR: El puerto {PORT} no responde. ¿Ejecutaste el programa Java?")
            test_socket.close()
            return # Si no hay socket, no podemos probar el paso 3
        test_socket.close()
    except Exception as e:
        print(f"❌ ERROR al intentar conectar al socket: {e}")

    # 3. PRUEBA DE TRAMA COMPLETA (Autorizador -> Java -> SQL Server)
    print("\n[3/3] Enviando trama de prueba al Core para consulta en SQL Server...")
    # Trama: Tipo(1) + Cuenta(10) + Tarjeta(19) + Monto(8)
    trama_test = "2" + "'CC001234567'".ljust(10) + "4111-1111-1111-1111".ljust(19) + "00000000"
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall((trama_test + "\n").encode('utf-8'))
            respuesta = s.recv(1024).decode('utf-8').strip()
            
            print(f"   > Trama enviada: [{trama_test}]")
            print(f"   > Respuesta recibida: [{respuesta}]")
            
            if "OK" in respuesta:
                print("✅ ÉXITO TOTAL: Java pudo consultar SQL Server y devolver el saldo.")
            elif "ERROR" in respuesta:
                print("⚠️  AVISO: Java respondió, pero dio ERROR al conectar a SQL Server.")
                print("   (Revisa los permisos de Windows Authentication o los nombres de las columnas en Java)")
            else:
                print(f"❓ RESPUESTA INESPERADA: {respuesta}")
                
    except Exception as e:
        print(f"❌ ERROR durante la comunicación: {e}")

if __name__ == "__main__":
    probar_diagnostico()