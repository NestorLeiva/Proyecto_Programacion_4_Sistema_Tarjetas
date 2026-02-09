package com.core;

import java.io.*;
import java.net.*;
import java.sql.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class CoreBancario {

  // USAR TU CADENA DE CONEXIÓN AQUÍ (LA QUE YA TE FUNCIONA)
  private static final String DB_URL = "jdbc:sqlserver://localhost:1433;databaseName=core_bancario;encrypt=false;trustServerCertificate=true;";
  private static final String USER = "rodri";
  private static final String PASS = "1234";

  public static void main(String[] args) {
    int puerto = 5000;

    try (ServerSocket server = new ServerSocket(puerto)) {
      System.out.println("========================================");
      System.out.println("   CORE BANCARIO INICIADO (PUERTO " + puerto + ")");
      System.out.println("========================================");

      while (true) {
        try (Socket socket = server.accept();
            BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            PrintWriter out = new PrintWriter(socket.getOutputStream(), true)) {

          String trama = in.readLine();
          if (trama != null) {
            System.out.println("\n Trama recibida: " + trama);

            // 1. Procesar en Base de Datos (CORE1)
            String respuesta = procesarEnBaseDatos(trama);

            // 2. Responder al Autorizador
            out.println(respuesta);
            System.out.println(" Respuesta enviada: " + respuesta);

            // 3. Registrar en Bitácora JSON (CORE3)
            registrarEnBitacora(trama, respuesta);
          }
        } catch (Exception e) {
          System.err.println(" Error en conexión: " + e.getMessage());
        }
      }
    } catch (IOException e) {
      e.printStackTrace();
    }
  }

  private static String procesarEnBaseDatos(String trama) {
    try (Connection conn = DriverManager.getConnection(DB_URL, USER, PASS)) {
      String tipo = trama.substring(0, 1);
      // Extraer cuenta (posiciones 1 a 11) y limpiar espacios
      String cuenta = trama.substring(1, 11).trim();

      if (tipo.equals("2")) { // CONSULTA (AUT2)
        return consultarSaldo(conn, cuenta);
      } else if (tipo.equals("1")) { // RETIRO (AUT1)
        // Extraer monto (posiciones 30 a 38) y convertir centavos a decimal
        double monto = Double.parseDouble(trama.substring(30, 38)) / 100.0;
        return aplicarRetiro(conn, cuenta, monto);
      }
    } catch (SQLException e) {
      System.err.println("Error SQL: " + e.getMessage());
      return "ERROR_BD";
    } catch (Exception e) {
      System.err.println("Error procesando trama: " + e.getMessage());
      return "ERROR_TRAMA";
    }
    return "TIPO_NO_SOPORTADO";
  }

  private static String consultarSaldo(Connection conn, String cuenta) throws SQLException {
    // Ajustado a tu tabla dbo.cuenta y columna saldo_disponible
    String sql = "SELECT saldo_disponible FROM dbo.cuenta WHERE numero_cuenta = ?";
    try (PreparedStatement ps = conn.prepareStatement(sql)) {
      ps.setString(1, cuenta);
      ResultSet rs = ps.executeQuery();
      if (rs.next()) {
        double saldo = rs.getDouble("saldo_disponible");
        // Requisito CORE1: OK + 19 dígitos (relleno con ceros)
        return "OK" + String.format("%019d", (long) (saldo * 100));
      }
    }
    return "CUENTA_INEXISTENTE";
  }

  private static String aplicarRetiro(Connection conn, String cuenta, double monto) throws SQLException {
    String sqlCheck = "SELECT saldo_disponible FROM dbo.cuenta WHERE numero_cuenta = ?";
    try (PreparedStatement ps = conn.prepareStatement(sqlCheck)) {
      ps.setString(1, cuenta);
      ResultSet rs = ps.executeQuery();
      if (rs.next()) {
        double saldoActual = rs.getDouble("saldo_disponible");
        if (saldoActual >= monto) {
          String sqlUpdate = "UPDATE dbo.cuenta SET saldo_disponible = saldo_disponible - ? WHERE numero_cuenta = ?";
          try (PreparedStatement psUp = conn.prepareStatement(sqlUpdate)) {
            psUp.setDouble(1, monto);
            psUp.setString(2, cuenta);
            psUp.executeUpdate();
            return "OK";
          }
        } else {
          return "SALDO_INSUFICIENTE";
        }
      }
    }
    return "CUENTA_INEXISTENTE";
  }

  private static void registrarEnBitacora(String tramaIn, String respuestaOut) {
    String fecha = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
    // Formato JSON para el archivo de bitácora (CORE3)
    String jsonLog = String.format(
        "{\"fecha\": \"%s\", \"trama_recibida\": \"%s\", \"respuesta_enviada\": \"%s\"}",
        fecha, tramaIn, respuestaOut);

    try (FileWriter fw = new FileWriter("bitacora_core.txt", true);
        BufferedWriter bw = new BufferedWriter(fw);
        PrintWriter out = new PrintWriter(bw)) {
      out.println(jsonLog);
      System.out.println("CORE3: Registro guardado en bitacora_core.txt");
    } catch (IOException e) {
      System.err.println("Error escribiendo bitácora: " + e.getMessage());
    }
  }
}