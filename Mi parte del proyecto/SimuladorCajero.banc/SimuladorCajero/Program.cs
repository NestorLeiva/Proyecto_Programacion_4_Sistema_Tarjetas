using System;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

namespace SimuladorCajero
{
    internal class Program
    {
        static async Task Main(string[] args)
        {
            bool salir = false;

            while (!salir)
            {
                try
                {
                    Console.Clear();
                    Console.WriteLine("========================================");
                    Console.WriteLine("       SIMULADOR CAJERO AUTOMÁTICO      ");
                    Console.WriteLine("========================================");
                    Console.WriteLine("1. Consultar Saldo (AUT2)");
                    Console.WriteLine("2. Retirar Efectivo (AUT1)");
                    Console.WriteLine("3. Adelanto de Efectivo (Crédito - CORE2)");
                    Console.WriteLine("4. Salir");
                    Console.WriteLine("========================================");
                    Console.Write("Seleccione una opción: ");

                    string opcion = Console.ReadLine();

                    switch (opcion)
                    {
                        case "1":
                            await PantallaConsulta();
                            break;
                        case "2":
                            await PantallaRetiro();
                            break;
                        case "3":
                            await PantallaCredito();
                            break;
                        case "4":
                            salir = true;
                            break;
                        default:
                            Console.WriteLine("Opción no válida. Intente de nuevo.");
                            System.Threading.Thread.Sleep(1000);
                            break;
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"\n[Error Crítico]: {ex.Message}");
                    Console.WriteLine("Presione cualquier tecla para reiniciar el menú...");
                    Console.ReadKey();
                }
            }
        }

        static async Task PantallaConsulta()
        {
            try
            {
                Console.Clear();
                Console.WriteLine("--- CONSULTA DE SALDO ---");
                Console.Write("Ingrese número de tarjeta (16 dígitos): ");
                string tarjeta = Console.ReadLine();

                if (string.IsNullOrEmpty(tarjeta) || tarjeta.Length < 10)
                    throw new Exception("Número de tarjeta inválido.");

                Console.Write("Ingrese PIN: ");
                string pin = Console.ReadLine();

                string trama = "2" + tarjeta.PadRight(10).Substring(0, 10) + tarjeta.PadRight(19) + "00000000";

                Console.WriteLine("\n[Hilo Secundario] Conectando con Autorizador...");
                string respuesta = await Task.Run(() => EnviarAlAutorizador(trama));

                Console.WriteLine("\nRESULTADO (JSON):");
                Console.WriteLine(respuesta);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n❌ Error en Consulta: {ex.Message}");
            }
            finally
            {
                Console.WriteLine("\nPresione cualquier tecla para volver...");
                Console.ReadKey();
            }
        }

        static async Task PantallaRetiro()
        {
            try
            {
                Console.Clear();
                Console.WriteLine("--- RETIRO DE EFECTIVO ---");
                Console.Write("Ingrese número de tarjeta: ");
                string tarjeta = Console.ReadLine();

                Console.Write("Ingrese monto a retirar: ");
                string inputMonto = Console.ReadLine();

                // Validación de entrada numérica
                if (!double.TryParse(inputMonto, out double monto))
                    throw new Exception("El monto debe ser un valor numérico.");

                string montoFormateado = (monto * 100).ToString().PadLeft(8, '0');
                string trama = "1" + tarjeta.PadRight(10).Substring(0, 10) + tarjeta.PadRight(19) + montoFormateado;

                Console.WriteLine("\n[Hilo Secundario] Procesando retiro...");
                string respuesta = await Task.Run(() => EnviarAlAutorizador(trama));

                Console.WriteLine("\nRESULTADO:");
                Console.WriteLine(respuesta);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n❌ Error en Retiro: {ex.Message}");
            }
            finally
            {
                Console.WriteLine("\nPresione cualquier tecla para volver...");
                Console.ReadKey();
            }
        }

        static async Task PantallaCredito()
        {
            Console.Clear();
            Console.WriteLine("--- ADELANTO DE CRÉDITO (CORE2) ---");
            Console.WriteLine("Esta opción utilizará la lógica de Tarjetas de Crédito.");
            Console.WriteLine("Próximamente estaremos integrando la tabla de SQL Server.");
            Console.WriteLine("\nPresione cualquier tecla para volver...");
            Console.ReadKey();
            await Task.CompletedTask;
        }

        // --- MÉTODO DE COMUNICACIÓN CON MANEJO DE EXCEPCIONES DE RED ---
        static string EnviarAlAutorizador(string trama)
        {
            try
            {
                using (TcpClient client = new TcpClient())
                {
                    // Timeout de 5 segundos para no quedarse esperando por siempre
                    var result = client.BeginConnect("127.0.0.1", 5001, null, null);
                    var success = result.AsyncWaitHandle.WaitOne(TimeSpan.FromSeconds(5));

                    if (!success) throw new Exception("Tiempo de espera agotado al conectar al Autorizador.");

                    client.EndConnect(result);

                    using (NetworkStream stream = client.GetStream())
                    {
                        byte[] data = Encoding.ASCII.GetBytes(trama + "\n");
                        stream.Write(data, 0, data.Length);

                        byte[] buffer = new byte[2048];
                        int bytesRead = stream.Read(buffer, 0, buffer.Length);
                        return Encoding.ASCII.GetString(buffer, 0, bytesRead);
                    }
                }
            }
            catch (SocketException)
            {
                return "{\"estado\": \"ERROR\", \"mensaje\": \"El servidor Autorizador (Python) no está activo.\"}";
            }
            catch (Exception ex)
            {
                return "{\"estado\": \"ERROR\", \"mensaje\": \"" + ex.Message + "\"}";
            }
        }
    }
}