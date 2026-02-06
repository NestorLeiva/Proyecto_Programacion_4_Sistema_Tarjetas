import socket

def probar_core():
    # Configuración del servidor (Tu programa en Java)
    HOST = '127.0.0.1'  # localhost
    PORT = 5000         # El puerto que pusiste en el ServerSocket de Java

    # TRAMA DE PRUEBA (Tipo 2 - Consulta de Saldo)
    # Estructura: Tipo(1) + Cuenta(10) + Tarjeta(19) + Monto(8)
    # Total: 38 caracteres
    tipo = "2"
    cuenta = "1234567890".ljust(10)  # Ajusta a 10 espacios
    tarjeta = "4567 89****** 1234".ljust(19)
    monto = "00000000" # En consulta el monto va en ceros
    
    trama_envio = tipo + cuenta + tarjeta + monto

    try:
        # 1. Crear el socket y conectar
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print(f"Conectando al Core en {HOST}:{PORT}...")
            s.connect((HOST, PORT))
            
            # 2. Enviar la trama (importante el \n al final para que Java lea la línea)
            s.sendall((trama_envio + "\n").encode('utf-8'))
            
            # 3. Recibir respuesta
            data = s.recv(1024)
            print(f"Trama enviada:  [{trama_envio}]")
            print(f"Respuesta Core: [{data.decode('utf-8').strip()}]")

    except ConnectionRefusedError:
        print("Error: No se pudo conectar. ¿Está corriendo el programa Java?")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    probar_core()