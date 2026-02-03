-- =====================================================
-- DATOS DE PRUEBA - CORE BANCARIO (5 REGISTROS)
-- =====================================================

USE core_bancario;
GO

-- =====================================================
-- 1. CLIENTES (5 clientes costarricenses)
-- =====================================================
INSERT INTO cliente (nombre, identificacion) VALUES
('Juan Pérez', '1-2345-6789'),
('María González', '2-3456-7890'),
('Carlos Ramírez', '3-4567-8901'),
('Ana Martínez', '4-5678-9012'),
('Luis Hernández', '5-6789-0123');
GO

USE core_bancario;
GO

-- =====================================================
-- 2. CUENTAS (5 cuentas para los clientes)
-- =====================================================
INSERT INTO cuenta (numero_cuenta, id_cliente, saldo_disponible, estado) VALUES
('CC001234567890123456789', 1, 1500000.00, 'ACTIVA'),
('DB987654321098765432109', 2, 850000.00, 'ACTIVA'),
('CC112233445566778899001', 3, 2200000.00, 'ACTIVA'),
('DB556677889900112233445', 4, 450000.00, 'BLOQUEADA'),
('CC998877665544332211000', 5, 1750000.00, 'ACTIVA');

SELECT * FROM cuenta;
GO

-- =====================================================
-- 3. TARJETAS (5 tarjetas vinculadas)
-- =====================================================
INSERT INTO tarjeta_cuenta (numero_tarjeta, id_cuenta, estado) VALUES
('4111-1111-1111-1111', 1, 'ACTIVA'),
('4111-2222-2222-2222', 2, 'ACTIVA'),
('4111-3333-3333-3333', 3, 'VENCIDA'),
('4111-4444-4444-4444', 1, 'ACTIVA'),
('4111-5555-5555-5555', 5, 'ACTIVA');
SELECT * FROM tarjeta_cuenta;
GO

-- =====================================================
-- 4. MOVIMIENTOS (5 transacciones reales)
-- =====================================================
INSERT INTO movimiento_tarjeta (id_cuenta, numero_tarjeta, codigo_autorizacion, tipo_movimiento, monto, saldo_anterior, saldo_nuevo, descripcion, estado) VALUES
(1, '4111-1111-1111-1111', 'A1234567', 'RETIRO_EFECTIVO', 50000.00, 1550000.00, 1500000.00, 'Retiro ATM Walmart Cartago', 'PROCESADO'),
(2, '4111-2222-2222-2222', 'B2345678', 'PAGO_SERVICIOS', 30000.00, 880000.00, 850000.00, 'Pago luz ICE', 'PROCESADO'),
(3, '4111-3333-3333-3333', 'C3456789', 'DEPOSITO', 200000.00, 2000000.00, 2200000.00, 'Nómina BAC San José', 'PROCESADO'),
(1, '4111-4444-4444-4444', 'D4567890', 'TRANSFERENCIA', 100000.00, 1500000.00, 1400000.00, 'Transferencia a Ana Martínez', 'PENDIENTE'),
(5, '4111-5555-5555-5555', 'E5678901', 'COMPRA_TIENDA', 75000.00, 1825000.00, 1750000.00, 'Auto Mercado San Rafael', 'PROCESADO');
SELECT * FROM movimiento_tarjeta;
GO