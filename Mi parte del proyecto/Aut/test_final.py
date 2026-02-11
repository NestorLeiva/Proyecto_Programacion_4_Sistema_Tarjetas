import socket
import json

def test_transaccion_real():
    # CONFIGURACIÓN DE LA TRAMA (22 dígitos para cuenta)
    tipo = "1"                                      # 1 para Retiro
    cuenta = "CC00123456789012345678".ljust(22)      # 22 caracteres exactos
    tarjeta = "4111111111111111".ljust(19)           # 19 caracteres exactos
    monto = "00005000"                               # 50.00 (8 dígitos)
    
    # Trama final que enviaría el Simulador C# (50 caracteres en total)
    trama_simulador = f"{tipo}{cuenta}{tarjeta}{monto}"
    
    print(f"--- ENVIANDO TRAMA AL AUTORIZADOR (5001) ---")
    print(f"Trama: [{trama_simulador}]")
    print(f"Longitud: {len(trama_simulador)} caracteres")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 5001))
            s.sendall(trama_simulador.encode())
            
            data = s.recv(4096).decode()
            respuesta = json.loads(data)
            
            print("\n--- RESPUESTA RECIBIDA ---")
            print(json.dumps(respuesta, indent=4))
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Asegúrate de que Python (5001) y Java (5000) estén corriendo.")

if __name__ == "__main__":
    test_transaccion_real()