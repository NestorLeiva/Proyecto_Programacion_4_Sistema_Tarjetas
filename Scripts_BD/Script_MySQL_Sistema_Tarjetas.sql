-- ============================================================
-- 		Script De Sistema de Tarjetas de Credito / Debito
-- Proyecto Programacion IV - Colegio Universitario de Cartago
-- ============================================================

CREATE DATABASE IF NOT EXISTS sistema_tarjetas 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE sistema_tarjetas;

-- Tabla de cajeros automaticos
CREATE TABLE cajero (
    id_cajero BIGINT PRIMARY KEY AUTO_INCREMENT,
    codigo_cajero VARCHAR(20) UNIQUE NOT NULL,
    ubicacion VARCHAR(100),
    estado VARCHAR(20) DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO'))
);

-- Tabla de codigos de motivo de rechazo (1-5)
CREATE TABLE codigo_motivo (
    id_codigo_motivo INT PRIMARY KEY AUTO_INCREMENT,
    codigo INT UNIQUE NOT NULL CHECK (codigo BETWEEN 1 AND 5),
    descripcion VARCHAR(100) NOT NULL
);

-- Tabla de tipos de transaccion
CREATE TABLE tipo_transaccion (
    id_tipo_transaccion INT PRIMARY KEY AUTO_INCREMENT,
    codigo_tipo VARCHAR(30) UNIQUE NOT NULL,
    descripcion VARCHAR(100) NOT NULL
);

-- Tabla principal de tarjetas
CREATE TABLE tarjeta (
    id_tarjeta BIGINT PRIMARY KEY AUTO_INCREMENT,
    numero_tarjeta VARCHAR(25) NOT NULL,   -- Simplificación temporal
    pin VARCHAR(10) NOT NULL,              -- Simplificación temporal
    fecha_vencimiento DATE NOT NULL,
    cvv VARCHAR(5) NOT NULL,               -- Simplificación temporal
    tipo_tarjeta VARCHAR(10) NOT NULL CHECK (tipo_tarjeta IN ('DEBITO', 'CREDITO')),
    estado VARCHAR(20) DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA', 'INACTIVA', 'VENCIDA')),
    numero_cuenta CHAR(25),
    identificacion_cliente VARCHAR(20),
    limite_adelanto_efectivo DECIMAL(15,2) DEFAULT 0,
    disponible_adelanto_efectivo DECIMAL(15,2) DEFAULT 0,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de autorizaciones
CREATE TABLE autorizacion (
    id_autorizacion BIGINT PRIMARY KEY AUTO_INCREMENT,
    codigo_autorizacion CHAR(8) NOT NULL,
    id_tarjeta BIGINT NOT NULL,
    id_cajero BIGINT NOT NULL,
    id_tipo_transaccion INT NOT NULL,
    monto DECIMAL(15,2),
    estado VARCHAR(20) DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA', 'CONFIRMADA')),
    fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_respuesta DATETIME NULL,
    respuesta VARCHAR(10),
    id_codigo_motivo INT NULL,
    CONSTRAINT fk_autorizacion_tarjeta FOREIGN KEY (id_tarjeta) REFERENCES tarjeta(id_tarjeta),
    CONSTRAINT fk_autorizacion_cajero FOREIGN KEY (id_cajero) REFERENCES cajero(id_cajero),
    CONSTRAINT fk_autorizacion_tipo FOREIGN KEY (id_tipo_transaccion) REFERENCES tipo_transaccion(id_tipo_transaccion),
    CONSTRAINT fk_autorizacion_motivo FOREIGN KEY (id_codigo_motivo) REFERENCES codigo_motivo(id_codigo_motivo)
);

-- Tabla de movimientos de credito
CREATE TABLE movimiento_credito (
    id_movimiento BIGINT PRIMARY KEY AUTO_INCREMENT,
    id_tarjeta BIGINT NOT NULL,
    codigo_autorizacion CHAR(8) NOT NULL,
    tipo_movimiento VARCHAR(50) NOT NULL,
    monto DECIMAL(15,2) NOT NULL,
    estado VARCHAR(20) DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'APROBADO', 'RECHAZADO')),
    fecha_movimiento DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_movimiento_credito_tarjeta FOREIGN KEY (id_tarjeta) REFERENCES tarjeta(id_tarjeta)
);

-- Indices para mejorar el rendimiento
CREATE INDEX idx_tarjeta_numero ON tarjeta(numero_tarjeta);
CREATE INDEX idx_tarjeta_pin ON tarjeta(pin);
CREATE INDEX idx_autorizacion_codigo ON autorizacion(codigo_autorizacion);
CREATE INDEX idx_autorizacion_fecha ON autorizacion(fecha_solicitud);
CREATE INDEX idx_cajero_codigo ON cajero(codigo_cajero);

-- ALTER TABLE

USE Sistema_Tarjetas;
ALTER TABLE tarjeta
MODIFY COLUMN numero_tarjeta VARBINARY(19) NOT NULL,
MODIFY COLUMN PIN VARBINARY(4) NOT NULL,
MODIFY COLUMN fecha_vencimiento VARBINARY(50) NOT NULL,
MODIFY COLUMN cvv VARBINARY(3) NOT NULL

SELECT * FROM tarjeta;















