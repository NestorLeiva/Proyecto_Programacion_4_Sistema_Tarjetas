package com.core;

import java.io.*;
import java.net.*;
import java.sql.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class CoreBancario {

<<<<<<< Updated upstream
    private static final String DB_URL = "jdbc:sqlserver://localhost:1433;databaseName=core_bancario;encrypt=false;trustServerCertificate=true;";
    private static final String USER = "rodri";
    private static final String PASS = "1234";
=======
  // USAR TU CADENA DE CONEXIÓN AQUÍ (LA QUE YA TE FUNCIONA)
  private static final String DB_URL = "jdbc:sqlserver://localhost:1433;databaseName=core_bancario;encrypt=false;trustServerCertificate=true;";
  private static final String USER = "nestor_p6";
  private static final String PASS = "12345678";
>>>>>>> Stashed changes

    public static void main(String[] args) {
        int puerto = 5000;
        ExecutorService pool = Executors.newFixedThreadPool(10);

        try (ServerSocket server = new ServerSocket(puerto)) {
            System.out.println("==========================================");
            System.out.println("   CORE BANCARIO - SERVIDOR INICIADO");
            System.out.println("   Puerto: " + puerto + " | Pool: 10 hilos");
            System.out.println("==========================================");

            while (true) {
                Socket socket = server.accept();
                System.out.println("\n[CONEXIÓN] Cliente detectado desde: " + socket.getInetAddress().getHostAddress());
                pool.execute(() -> manejarCliente(socket));
            }
        } catch (IOException e) {
            System.err.println("Error en el servidor: " + e.getMessage());
        } finally {
            pool.shutdown();
        }
    }

    private static void manejarCliente(Socket socket) {
        try (socket;
             BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
             PrintWriter out = new PrintWriter(socket.getOutputStream(), true)) {

            String trama = in.readLine();
            if (trama != null) {
                // PROCESAMIENTO
                String respuesta = procesarEnBaseDatos(trama);
                
                // RESPUESTA AL AUTORIZADOR
                out.println(respuesta);
                
                // AUDITORÍA
                registrarEnBitacora(trama, respuesta);

                System.out.println("[" + Thread.currentThread().getName() + "] Trama: " + trama);
                System.out.println("[" + Thread.currentThread().getName() + "] Respuesta: " + respuesta);
            }
        } catch (Exception e) {
            System.err.println("Error procesando cliente: " + e.getMessage());
        }
    }

    /* =========================================================================
     * MÓDULO: CORE1 - PROCESAMIENTO DE TRANSACCIONES (DÉBITO)
     * Descripción: Maneja el acceso a SQL Server, validación de saldos 
     * y actualización de cuentas de ahorro/corriente.
     * ========================================================================= */

    private static String procesarEnBaseDatos(String trama) {
        try (Connection conn = DriverManager.getConnection(DB_URL, USER, PASS)) {
            String tipo = trama.substring(0, 1);
            String cuenta = trama.substring(1, 11).trim();

            if (tipo.equals("2")) { // CONSULTA DE SALDO
                return consultarSaldo(conn, cuenta);
            } else if (tipo.equals("1")) { // RETIRO DE EFECTIVO
                double monto = Double.parseDouble(trama.substring(30, 38)) / 100.0;
                return aplicarRetiro(conn, cuenta, monto);
            }
        } catch (Exception e) {
            return "ERROR_DB";
        }
        return "TIPO_INVALIDO";
    }

    private static String consultarSaldo(Connection conn, String cuenta) throws SQLException {
        String sql = "SELECT saldo_disponible FROM dbo.cuenta WHERE numero_cuenta = ?";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, cuenta);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    double saldo = rs.getDouble("saldo_disponible");
                    // Retorno reglamentario: OK + 19 dígitos
                    return "OK" + String.format("%019d", (long) (saldo * 100));
                }
            }
        }
        return "CUENTA_NO_EXISTE";
    }

    private static String aplicarRetiro(Connection conn, String cuenta, double monto) throws SQLException {
        String sqlCheck = "SELECT saldo_disponible FROM dbo.cuenta WHERE numero_cuenta = ?";
        try (PreparedStatement ps = conn.prepareStatement(sqlCheck)) {
            ps.setString(1, cuenta);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    double saldo = rs.getDouble("saldo_disponible");
                    if (saldo >= monto) {
                        String sqlUp = "UPDATE dbo.cuenta SET saldo_disponible = saldo_disponible - ? WHERE numero_cuenta = ?";
                        try (PreparedStatement psUp = conn.prepareStatement(sqlUp)) {
                            psUp.setDouble(1, monto);
                            psUp.setString(2, cuenta);
                            psUp.executeUpdate();
                            return "OK";
                        }
                    } else return "SALDO_INSUFICIENTE";
                }
            }
        }
        return "CUENTA_NO_EXISTE";
    }

    /* =========================================================================
     * MÓDULO: CORE3 - BITÁCORA DE AUDITORÍA (JSON)
     * Descripción: Registra todas las tramas entrantes y salientes en un 
     * archivo de texto plano con formato estructurado JSON.
     * ========================================================================= */

    private static void registrarEnBitacora(String tramaIn, String respuestaOut) {
        String fecha = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        String jsonLog = String.format("{\"fecha\": \"%s\", \"trama_in\": \"%s\", \"respuesta_out\": \"%s\"}", 
                         fecha, tramaIn, respuestaOut);
        
        try (FileWriter fw = new FileWriter("bitacora_core.txt", true);
             BufferedWriter bw = new BufferedWriter(fw);
             PrintWriter out = new PrintWriter(bw)) {
            out.println(jsonLog);
        } catch (IOException e) {
            System.err.println("Error Bitácora: " + e.getMessage());
        }
    }
}