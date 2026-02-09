import socket
import json

""" ###################################
    Datos de Prueba de las Tarjetas

('4111-1111-1111-1111', '1234', '2027-12-31', '123', 'CREDITO', 'ACTIVA', 'CC001234567', '1-2345-6789', 500000.00, 450000.00),
('4111-2222-2222-2222', '5678', '2026-06-30', '456', 'DEBITO', 'ACTIVA', 'DB987654321', '2-3456-7890', 200000.00, 180000.00),
('4111-3333-3333-3333', '9999', '2025-03-31', '789', 'CREDITO', 'VENCIDA', 'CC112233445', '3-4567-8901', 300000.00, 0.00),
('4111-4444-4444-4444', '4321', '2028-09-30', '321', 'DEBITO', 'INACTIVA', 'DB556677889', '4-5678-9012', 150000.00, 150000.00),
('4111-5555-5555-5555', '8888', '2027-11-30', '654', 'CREDITO', 'ACTIVA', 'CC998877665', '5-6789-0123', 800000.00, 700000.00);

""" ###################################

# =========================================
#           Objeto Json
# =========================================


datos_prueba_tarjetas = [
    {
        "numero_tarjeta": "4111-1111-1111-1111",
        "pin": "1234",
        "pin_actual": "1234",
        "pin_nuevo": "0000",
        "fecha_vencimiento": "2027-12-30",
        "cvv": "123",
        "id_cajero": 1
    }
]

for i, tarjeta in enumerate(datos_prueba_tarjetas, 1):
    print(f"\n PRUEBA {i}: {tarjeta['numero_tarjeta'][:4]}****")
    
    sock = socket.socket()
    sock.connect(("localhost", 9090))
    sock.send(json.dumps(tarjeta).encode())
    

    print("Enviando Respuesta ***")
    
    respuesta = sock.recv(4096).decode()

    print("Respuesta del Servidor:")
    print(f"{respuesta}")
    
    sock.close()
    print("Prueba Completada con Exito")
