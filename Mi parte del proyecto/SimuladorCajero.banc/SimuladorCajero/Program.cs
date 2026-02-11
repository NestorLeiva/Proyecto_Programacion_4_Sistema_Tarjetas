using System;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

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
                    Console.WriteLine("3. Cambio de PIN (AUT3)");
                    Console.WriteLine("4. Salir");
                    Console.WriteLine("========================================");
                    Console.Write("Seleccione una opción: ");

                    string opcion = Console.ReadLine();
                    switch (opcion)
                    {
                        case "1": await PantallaConsulta(); break;
                        case "2": await PantallaRetiro(); break;
                        case "3": await PantallaCambioPin(); break;
                        case "4": salir = true; break;
                        default:
                            Console.WriteLine("Opción no válida.");
                            await Task.Delay(1000);
                            break;
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"\n[Error]: {ex.Message}");
                    Console.ReadKey();
                }
            }
        }

        static async Task PantallaConsulta()
        {
            Console.Clear();
            Console.WriteLine("--- CONSULTA DE SALDO ---");
            Console.Write("Cuenta (23 dígitos): ");
            string cuenta = Console.ReadLine();
            Console.Write("Tarjeta (16 dígitos): ");
            string tarjeta = Console.ReadLine();
            Console.Write("PIN: ");
            string pin = Console.ReadLine();

            // Trama: Tipo(1) + Cuenta(22) + Tarjeta(19) + Monto(8) + PIN(4) = 54 caracteres
            string trama = "2" +
                           cuenta.PadRight(23).Substring(0, 23) +
                           tarjeta.PadRight(19).Substring(0, 19) +
                           "00000000" +
                           pin.PadLeft(4, '0').Substring(0, 4);

            await EjecutarTransaccion(trama, "Consultando saldo...");
        }

        static async Task PantallaRetiro()
        {
            Console.Clear();
            Console.WriteLine("--- RETIRO DE EFECTIVO ---");
            Console.Write("Cuenta (23 dígitos): ");
            string cuenta = Console.ReadLine();
            Console.Write("Tarjeta (16 dígitos): ");
            string tarjeta = Console.ReadLine();
            Console.Write("PIN: ");
            string pin = Console.ReadLine();
            Console.Write("Monto a retirar: ");
            double monto = double.Parse(Console.ReadLine());

            string montoFormateado = (monto * 100).ToString().PadLeft(8, '0');

            // Trama: Tipo(1) + Cuenta(22) + Tarjeta(19) + Monto(8) + PIN(4)
            string trama = "1" +
                           cuenta.PadRight(23).Substring(0, 23) +
                           tarjeta.PadRight(19).Substring(0, 19) +
                           montoFormateado +
                           pin.PadLeft(4, '0').Substring(0, 4);

            await EjecutarTransaccion(trama, "Procesando retiro...");
        }

        static async Task PantallaCambioPin()
        {
            Console.Clear();
            Console.WriteLine("--- CAMBIO DE PIN (AUT3) ---");
            Console.Write("Número de tarjeta: ");
            string tarjeta = Console.ReadLine();
            Console.Write("PIN Actual: ");
            string pinActual = Console.ReadLine();
            Console.Write("PIN Nuevo: ");
            string pinNuevo = Console.ReadLine();

            var datosPin = new
            {
                numero_tarjeta = tarjeta,
                pin_actual = pinActual,
                pin_nuevo = pinNuevo,
                id_cajero = 1
            };

            string jsonTrama = JsonConvert.SerializeObject(datosPin);
            await EjecutarTransaccion(jsonTrama, "Cambiando PIN...");
        }

        static async Task EjecutarTransaccion(string trama, string mensaje)
        {
            Console.WriteLine($"\n[Hilo Secundario] {mensaje}");
            string respuesta = await Task.Run(() => EnviarAlAutorizador(trama));
            Console.WriteLine("\nRESULTADO:");
            Console.WriteLine(respuesta);
            Console.WriteLine("\nPresione cualquier tecla para continuar...");
            Console.ReadKey();
        }

        static string EnviarAlAutorizador(string trama)
        {
            try
            {
                using (TcpClient client = new TcpClient("127.0.0.1", 5001))
                using (NetworkStream stream = client.GetStream())
                {
                    byte[] data = Encoding.ASCII.GetBytes(trama + "\n");
                    stream.Write(data, 0, data.Length);

                    byte[] buffer = new byte[2048];
                    int bytesRead = stream.Read(buffer, 0, buffer.Length);
                    return Encoding.ASCII.GetString(buffer, 0, bytesRead);
                }
            }
            catch (Exception ex)
            {
                return $"{{\"estado\": \"ERROR\", \"mensaje\": \"{ex.Message}\"}}";
            }
        }
    }
}