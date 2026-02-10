import socket
import mysql.connector
import sys

def probar_diagnostico():
    print("=== INICIANDO DIAGNÓSTICO DE CONEXIONES ===")

    # 1. PRUEBA DE CONEXIÓN A MYSQL (Sistema de Tarjetas)
    print("\n[1/3] Probando conexion a MySQL...")
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",      # Cambia por tu usuario de MySQL
            password="Nstrl0436Mysql*", # Cambia por tu contraseña de MySQL
            database="Sistema_Tarjetas"
        )
        if db.is_connected():
            print(" EXITO: Conexion a MySQL establecida.")
            db.close()
    except Exception as e:
        print(f" ERROR en MySQL: {e}")

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
            print(f" EXITO: El Core Java esta escuchando en el puerto {PORT}.")
        else:
            print(f" ERROR: El puerto {PORT} no responde. ¿Ejecutaste el programa Java?")
            test_socket.close()
            return # Si no hay socket, no podemos probar el paso 3
        test_socket.close()
    except Exception as e:
        print(f" ERROR al intentar conectar al socket: {e}")

    # 3. PRUEBA DE TRAMA COMPLETA (Autorizador -> Java -> SQL Server)
    print("\n[3/3] Enviando trama de prueba al Core para consulta en SQL Server...")
    # Trama: Tipo(1) + Cuenta(10) + Tarjeta(19) + Monto(8)
    trama_test = "2" + "1234567890".ljust(10) + "4567890123456789".ljust(19) + "00000000"
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall((trama_test + "\n").encode('utf-8'))
            respuesta = s.recv(1024).decode('utf-8').strip()
            
            print(f"   > Trama enviada: [{trama_test}]")
            print(f"   > Respuesta recibida: [{respuesta}]")
            
            if "OK" in respuesta:
                print(" ÉXITO TOTAL: Java pudo consultar SQL Server y devolver el saldo.")
            elif "ERROR" in respuesta:
                print("  AVISO: Java respondió, pero dio ERROR al conectar a SQL Server.")
                print("   (Revisa los permisos de Windows Authentication o los nombres de las columnas en Java)")
            else:
                print(f" RESPUESTA INESPERADA: {respuesta}")
                
    except Exception as e:
        print(f" ERROR durante la comunicación: {e}")


def probar_CORE2_retiro():
    """  PRUEBA ESPECIFICA CORE2 - RETIRO  """
    print("\n" + "="*60)
    print("  PRUEBA CORE2 - REGISTRO DE RETIROS ")
    print("="*60)
    
    HOST = '127.0.0.1'
    PORT = 5000
    
    #  TRAMA EXACTA CORE2 (46 caracteres) 
    # 1(1) + 45678909-3(10) + 4567 89** **** 1234(19) + 12345678(8) + 15000000(8)
    trama_CORE2 = "145678909-34567 89** **** 12341234567815000000"
    
    print(f"[1/3] Enviando trama CORE2 de RETIRO:")
    print(f"    Tipo: 1 (Retiro)")
    print(f"    Cuenta: 45678909-3")
    print(f"    Tarjeta: 4567 89** **** 1234")
    print(f"    Código: 12345678")
    print(f"    Monto: 150000.00 (15000000 en trama)")
    print(f"    Trama completa: [{trama_CORE2}] (len={len(trama_CORE2)})")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall((trama_CORE2 + "\n").encode('utf-8'))
            respuesta = s.recv(1024).decode('utf-8').strip()
            
            print(f"\n[2/3] Respuesta del CORE2: [{respuesta}]")
            
            if respuesta == "OK":
                print("  ¡EXITO CORE2! Retiro registrado correctamente:")
                print("    ✓ Saldo rebajado")
                print("    ✓ Movimiento guardado en movimiento_tarjeta")
                print("    ✓ Descripcion: 'Retiro # 4567 89** **** 1234 y Codigo autorizacion 12345678'")
            elif "ERROR" in respuesta:
                print("  ERROR en CORE2. Posibles causas:")
                print("    - Cuenta 45678909-3 no existe")
                print("    - Tarjeta 4567 89** **** 1234 no esta asignada")
                print("    - Saldo insuficiente (< ₡150000)")
                print("    - Error de conexión SQL Server")
            else:
                print(f"  Respuesta inesperada: {respuesta}")
                
    except ConnectionRefusedError:
        print("  ERROR: Core Java no esta ejecutandose (puerto 5000)")
    except Exception as e:
        print(f"  ERROR de comunicacion: {e}")


if __name__ == "__main__":
    probar_diagnostico()  
    print("\n" + "-"*60)
    probar_CORE2_retiro()  




