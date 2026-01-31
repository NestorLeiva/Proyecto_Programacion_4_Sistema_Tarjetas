-- ============================================================
-- 		Script De Sistema de Tarjetas de Credito / Debito
-- Proyecto Programacion IV - Colegio Universitario de Cartago
-- ============================================================

-- creo la base de datos
create database if not exists sistema_tarjetas;
 
-- uso la base de datos
use sistema_tarjetas;

-- tabla tipos de tarjetas
create table if not exists Tarjeta (
id_tarjeta bigint primary key auto_increment,
numero_tarjeta VARBINARY(255) not null, -- 'AES cifrado'
pin VARBINARY(255) not null, -- 'AES cifrado - Obligatorio'
fecha_vencimiento date not null,
cvv VARBINARY(255) not null, -- 'AES cifrado'
tipo_tarjeta VARCHAR(10) not null CHECK (tipo_tarjeta IN ('DEBITO','CREDITO')),
estado VARCHAR(20) DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA','INACTIVA','VENCIDA')),
numero_cuenta CHAR(25), -- referencia logica al Core Bancario
identificacion_cliente NVARCHAR(20),
limite_adelanto_efectivo decimal(15,2) DEFAULT 0,
disponible_adelanto_efectivo DECIMAL(15,2) DEFAULT 0,
fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP on UPDATE CURRENT_TIMESTAMP
);

-- SHOW TABLES;
-- SHOW COLUMNS from Tarjeta;


-- tabla Cajero Automatico (opcional)
CREATE TABLE IF NOT EXISTS Cajero (
id_cajero bigint primary key auto_increment,
codigo_cajero NVARCHAR(20) UNIQUE NOT NULL,
ubicacion NVARCHAR(100),
estado NVARCHAR(20) DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO'))
);
-- SHOW TABLES

-- tabla de codigos de motivo rechazo
CREATE TABLE if not EXISTS codigo_motivo(
id_codigo_motivo INT PRIMARY KEY AUTO_INCREMENT,
codigo INT UNIQUE NOT NULL CHECK( codigo BETWEEN 1 AND 5),
descripcion NVARCHAR(100) NOT NULL
);

-- ALTER TABLE codigo_motivo RENAME Codigo_Motivo;
-- SHOW TABLES

-- tabla tipo de Transaccion

CREATE TABLE IF NOT EXISTS tipo_transaccion(
id_tipo_transaccion INT PRIMARY KEY AUTO_INCREMENT,
codigo_tipo NVARCHAR(30) UNIQUE NOT NULL,
descripcion NVARCHAR(100) NOT NULL
);
ALTER TABLE tipo_transaccion RENAME Tipo_Transaccion;
-- SHOW TABLES


-- tabla de AUTORIZACIONES (codigo de 8 digitos)

CREATE TABLE IF NOT EXISTS Autorizacion(
id_atorizacion BIGINT PRIMARY KEY AUTO_INCREMENT,
codigo_autorizacion CHAR(8) NOT NULL,
id_tarjeta BIGINT NOT NULL,
id_cajero BIGINT NOT NULL,
id_tipo_transaccion INT NOT NULL,
monto DECIMAL(15,2),
estado NVARCHAR(20) DEFAULT 'PENDIENTE' CHECK (estado IN (
'PENDIENTE', 'APROBADA', 'RECHAZADA', 'CONFIRMADA')),
fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
fecha_respuesta DATETIME NULL,
respuesta NVARCHAR(10),
id_codigo_motivo INT null
);

-- show tables

-- tabla movimiento tarjeta credito

CREATE TABLE IF NOT EXISTS Movimiento_credito(
id_movimiento BIGINT PRIMARY KEY AUTO_INCREMENT,
id_tarjeta BIGINT NOT NULL,
codigo_autorizacion CHAR(8) NOT NULL,
tipo_movimiento NVARCHAR(50) NOT NULL,
monto DECIMAL(15,2) NOT NULL,
estado NVARCHAR(20) DEFAULT 'PENDIENTE',CHECK (estado IN (
'PENDIENTE', 'APROBADO', 'RECHAZADO')),
fecha_movimiento DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE Movimiento_credito RENAME Movimiento_Credito;

SHOW TABLES;

-- =====================================
-- llaves foraneas fk
-- =====================================

ALTER TABLE autorizacion 
	ADD CONSTRAINT fk_autorizacion_tarjetas 
	FOREIGN KEY (id_tarjeta) REFERENCES tarjeta(id_tarjeta),
	ADD CONSTRAINT fk_autorizacion_cajero 
	FOREIGN KEY (id_cajero) REFERENCES cajero(id_cajero),
	ADD CONSTRAINT fk_autorizacion_tipo FOREIGN KEY (id_tipo_transaccion) 
	REFERENCES tipo_transaccion(id_tipo_transaccion),
	ADD CONSTRAINT fk_autorizacion_motivo FOREIGN KEY (id_codigo_motivo) 
	REFERENCES codigo_motivo(id_codigo_motivo);

ALTER TABLE Movimiento_Credito
	ADD CONSTRAINT fk_movimiento_credito_tarjeta FOREIGN KEY
	(id_tarjeta) REFERENCES tarjeta (id_tarjeta);

-- verifico el estado de las FK 1 Activas / 0 desactivadas

SELECT @@foreign_key_checks;


