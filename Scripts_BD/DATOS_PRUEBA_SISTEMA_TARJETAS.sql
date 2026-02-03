-- =====================================================
-- DATOS DE PRUEBA - SISTEMA TARJETAS
-- =====================================================


use sistema_tarjetas;

-- 1. Tipos de transacción
INSERT INTO tipo_transaccion (codigo_tipo, descripcion) VALUES
('RETIRO', 'Retiro de efectivo'),
('SALDO', 'Consulta de saldo'),
('PAGO', 'Pago de servicios'),
('TRANSFERENCIA', 'Transferencia entre cuentas'),
('AJUSTE', 'Ajuste de saldo');

-- 2. Códigos de motivo de rechazo
INSERT INTO codigo_motivo (codigo, descripcion) VALUES
(1, 'Fondos insuficientes'),
(2, 'Tarjeta vencida'),
(3, 'PIN incorrecto'),
(4, 'Límite diario excedido'),
(5, 'Tarjeta bloqueada');

-- 3. Cajeros automáticos
INSERT INTO cajero (codigo_cajero, ubicacion, estado) VALUES
('ATM001', 'Sucursal Centro Comercial, San José', 'ACTIVO'),
('ATM002', 'Aeropuerto Internacional, Alajuela', 'ACTIVO'),
('ATM003', 'Universidad de Costa Rica, San Pedro', 'INACTIVO'),
('ATM004', 'Walmart Cartago', 'ACTIVO'),
('ATM005', 'Gasolinera San Rafael, Cartago', 'ACTIVO');

-- 4. Tarjetas (5 tarjetas de prueba)
INSERT INTO tarjeta (numero_tarjeta, pin, fecha_vencimiento, cvv, tipo_tarjeta, estado, numero_cuenta, identificacion_cliente, limite_adelanto_efectivo, disponible_adelanto_efectivo) VALUES
('4111-1111-1111-1111', '1234', '2027-12-31', '123', 'CREDITO', 'ACTIVA', 'CC001234567', '1-2345-6789', 500000.00, 450000.00),
('4111-2222-2222-2222', '5678', '2026-06-30', '456', 'DEBITO', 'ACTIVA', 'DB987654321', '2-3456-7890', 200000.00, 180000.00),
('4111-3333-3333-3333', '9999', '2025-03-31', '789', 'CREDITO', 'VENCIDA', 'CC112233445', '3-4567-8901', 300000.00, 0.00),
('4111-4444-4444-4444', '4321', '2028-09-30', '321', 'DEBITO', 'INACTIVA', 'DB556677889', '4-5678-9012', 150000.00, 150000.00),
('4111-5555-5555-5555', '8888', '2027-11-30', '654', 'CREDITO', 'ACTIVA', 'CC998877665', '5-6789-0123', 800000.00, 700000.00);

-- 5. Autorizaciones de prueba
INSERT INTO autorizacion (codigo_autorizacion, id_tarjeta, id_cajero, id_tipo_transaccion, monto, estado, fecha_solicitud, fecha_respuesta, respuesta, id_codigo_motivo) VALUES
('A1234567', 1, 1, 1, 50000.00, 'APROBADA', '2026-02-01 14:30:00', '2026-02-01 14:30:02', 'OK', NULL),
('B2345678', 2, 4, 1, 80000.00, 'RECHAZADA', '2026-02-01 15:15:00', '2026-02-01 15:15:01', 'NOK', 1),
('C3456789', 1, 2, 2, NULL, 'APROBADA', '2026-02-01 16:00:00', '2026-02-01 16:00:01', 'OK', NULL),
('D4567890', 3, 1, 1, 30000.00, 'RECHAZADA', '2026-02-01 16:30:00', '2026-02-01 16:30:01', 'NOK', 2),
('E5678901', 4, 5, 1, 25000.00, 'PENDIENTE', '2026-02-01 17:00:00', NULL, NULL, NULL);

-- 6. Movimientos de crédito
INSERT INTO movimiento_credito (id_tarjeta, codigo_autorizacion, tipo_movimiento, monto, estado) VALUES
(1, 'A1234567', 'RETIRO_EFECTIVO', 50000.00, 'APROBADO'),
(2, 'B2345678', 'RETIRO_EFECTIVO', 80000.00, 'RECHAZADO'),
(1, 'C3456789', 'CONSULTA_SALDO', 0.00, 'APROBADO');
