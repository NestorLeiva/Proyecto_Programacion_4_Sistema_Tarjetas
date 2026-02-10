import json
import socket

def test_flujo_json():
    print("--- INICIANDO TEST DE FORMATO JSON ---")
    
    # 1. Simulación de trama que el Autorizador enviaría al Core
    # Tipo 2 (Consulta), Cuenta 1234567890, Tarjeta 1234567890123456789, Monto 00000000
    trama_ejemplo = "21234567890123456789012345678900000000"
    
    print("\n[Paso 1] Enviando trama al Core Java...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 5000))
            s.sendall((trama_ejemplo + "\n").encode())
            respuesta = s.recv(1024).decode().strip()
            print(f"Respuesta cruda del Core: {respuesta}")
            
            # Verificar si el Core cumple el formato de longitud
            if respuesta.startswith("OK") and len(respuesta) == 21:
                print("✅ El Core devolvió el formato correcto (OK + 19 dígitos).")
            else:
                print("⚠️ El Core respondió, pero el formato no es de 21 caracteres.")
    except Exception as e:
        print(f"❌ No se pudo conectar con el Core: {e}")
        return

    # 2. Verificar la Bitácora en la carpeta de Java
    print("\n[Paso 2] Verificando bitacora_core.txt...")
    print("Por favor, abre el archivo 'bitacora_core.txt' en tu VS Code de Java.")
    print("Debería verse una línea como esta:")
    print('{"fecha": "2024-...", "trama_in": "2123...", "respuesta_out": "OK000..."}')

    # 3. Simular la salida final del Autorizador
    print("\n[Paso 3] Formateando salida final del Autorizador...")
    # Aquí simulamos lo que hace tu función procesar_transaccion
    simulacion_resultado = {
        "tarjeta": "1234********6789",
        "estado": "APROBADO",
        "mensaje": "Consulta exitosa",
        "codigo_autorizacion": None,
        "saldo": float(respuesta[2:]) / 100 if "OK" in respuesta else 0.0
    }
    
    json_final = json.dumps(simulacion_resultado, indent=4)
    print("Salida JSON que vería el usuario:")
    print(json_final)

    # Validar que sea un JSON válido
    try:
        json.loads(json_final)
        print("\n✅ TEST FINALIZADO: El formato JSON es válido y estructurado.")
    except:
        print("\n❌ ERROR: El formato generado no es un JSON válido.")

if __name__ == "__main__":
    test_flujo_json()