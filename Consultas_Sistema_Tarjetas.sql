-- =====================================================
-- CONSULTAS - SISTEMA TARJETAS
-- =====================================================

USE sistema_tarjetas;
-- Ver autorizaciones del cajero 
SELECT * FROM autorizacion WHERE id_cajero = 4;

-- Tarjetas activas con saldo disponible
SELECT numero_tarjeta, disponible_adelanto_efectivo 
FROM tarjeta 
WHERE estado = 'ACTIVA' AND disponible_adelanto_efectivo > 0;

-- Últimas autorizaciones
SELECT a.codigo_autorizacion, t.numero_tarjeta, c.ubicacion, a.monto, a.estado
FROM autorizacion a
JOIN tarjeta t ON a.id_tarjeta = t.id_tarjeta
JOIN cajero c ON a.id_cajero = c.id_cajero
ORDER BY a.fecha_solicitud DESC LIMIT 5;
