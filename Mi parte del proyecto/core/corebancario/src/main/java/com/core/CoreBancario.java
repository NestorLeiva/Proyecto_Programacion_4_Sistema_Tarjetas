package com.core;

import java.io.*;
import java.net.*;
import java.sql.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class CoreBancario {
    private static final String DB_URL = "jdbc:sqlserver://localhost:1433;databaseName=core_bancario;encrypt=false;trustServerCertificate=true;";
    private static final String USER = "rodri";
    private static final String PASS = "1234";

    public static void main(String[] args) {
        try (ServerSocket server = new ServerSocket(5000)) {
            System.out.println("==========================================");
            System.out.println("   CORE JAVA ESCUCHANDO EN PUERTO 5000");
            System.out.println("==========================================");

            while (true) {
                try (Socket socket = server.accept();
                        BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                        PrintWriter out = new PrintWriter(socket.getOutputStream(), true)) {

                    String trama = in.readLine();
                    if (trama != null) {
                        // =====================================================
                        // CORE 1: RECEPCIÓN Y DESGLOSE
                        // =====================================================
                        String tipo = trama.substring(0, 1);
                        String cuenta = trama.substring(1, 24).trim();
                        String tarjeta = trama.substring(24, 43).trim();
                        String auth = trama.substring(43, 51).trim();
                        double monto = Double.parseDouble(trama.substring(51, 59)) / 100.0;

                        // =====================================================
                        // CORE 2: PROCESAMIENTO Y REGISTRO MOVIMIENTOS
                        // =====================================================
                        String respuesta = "ERROR";
                        try (Connection conn = DriverManager.getConnection(DB_URL, USER, PASS)) {
                            if (tipo.equals("1")) { // Retiro
                                respuesta = ejecutarRetiro(conn, cuenta, tarjeta, auth, monto);
                            } else if (tipo.equals("2")) { // Consulta
                                respuesta = ejecutarConsulta(conn, cuenta);
                            }
                        }

                        // =====================================================
                        // CORE 3: RESPUESTA AL AUTORIZADOR Y BITÁCORA
                        // =====================================================
                        out.println(respuesta);
                        registrarEnBitacora(trama, respuesta);
                    }
                } catch (Exception e) {
                    System.err.println("Error en conexión individual: " + e.getMessage());
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // LÓGICA CORE 2: RETIRO
    private static String ejecutarRetiro(Connection conn, String cuenta, String tarjeta, String auth, double monto)
            throws SQLException {
        conn.setAutoCommit(false);
        try {
            // Validar saldo en SQL Server
            PreparedStatement ps = conn
                    .prepareStatement("SELECT id_cuenta, saldo_disponible FROM cuenta WHERE numero_cuenta = ?");
            ps.setString(1, cuenta);
            ResultSet rs = ps.executeQuery();

            if (rs.next()) {
                long idC = rs.getLong("id_cuenta");
                double saldoA = rs.getDouble("saldo_disponible");

                if (saldoA >= monto) {
                    double saldoN = saldoA - monto;

                    // Actualizar saldo en SQL Server
                    PreparedStatement up = conn
                            .prepareStatement("UPDATE cuenta SET saldo_disponible = ? WHERE id_cuenta = ?");
                    up.setDouble(1, saldoN);
                    up.setLong(2, idC);
                    up.executeUpdate();

                    // Registro en Tabla movimiento_tarjeta (SQL Server)
                    PreparedStatement mov = conn.prepareStatement(
                            "INSERT INTO movimiento_tarjeta (id_cuenta, numero_tarjeta, codigo_autorizacion, tipo_movimiento, monto, saldo_anterior, saldo_nuevo, estado) "
                                    +
                                    "VALUES (?, ?, ?, 'RETIRO_EFECTIVO', ?, ?, ?, 'PROCESADO')");
                    mov.setLong(1, idC);
                    mov.setString(2, tarjeta);
                    mov.setString(3, auth);
                    mov.setDouble(4, monto);
                    mov.setDouble(5, saldoA);
                    mov.setDouble(6, saldoN);
                    mov.executeUpdate();

                    conn.commit();
                    return "OK";
                }
                return "FONDOS_INSUFICIENTES";
            }
            return "CUENTA_NO_EXISTE";
        } catch (Exception e) {
            conn.rollback();
            return "ERROR_DB_SQL";
        } finally {
            conn.setAutoCommit(true);
        }
    }

    // LÓGICA CORE 2: CONSULTA
    private static String ejecutarConsulta(Connection conn, String cuenta) throws SQLException {
        PreparedStatement ps = conn.prepareStatement("SELECT saldo_disponible FROM cuenta WHERE numero_cuenta = ?");
        ps.setString(1, cuenta);
        ResultSet rs = ps.executeQuery();
        if (rs.next()) {
            return "OK" + String.format("%019d", (long) (rs.getDouble("saldo_disponible") * 100));
        }
        return "CUENTA_NO_EXISTE";
    }

    // LÓGICA CORE 3: BITÁCORA DE TRANSACCIONES
    private static void registrarEnBitacora(String tramaIn, String respuestaOut) {
        String fecha = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        String registro = String.format("[%s] TRAMA_RECIBIDA: %s | RESPUESTA_CORE: %s", fecha, tramaIn, respuestaOut);

        try (FileWriter fw = new FileWriter("bitacora_core_java.txt", true);
                PrintWriter pw = new PrintWriter(new BufferedWriter(fw))) {
            pw.println(registro);
        } catch (IOException e) {
            System.err.println("Error escribiendo bitácora: " + e.getMessage());
        }
    }
}