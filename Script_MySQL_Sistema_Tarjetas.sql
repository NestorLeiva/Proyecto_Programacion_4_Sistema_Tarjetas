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
