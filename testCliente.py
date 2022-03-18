#!/bin/python3

import sys
import socket
import logging


HOST = "192.168.1.100"
PORT = 36001

def main() -> int:
    # Log
    logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(threadName)s: %(message)s', level=logging.INFO)

    # Creamos el cliente
    logging.info("Conectando")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
        clientSocket.connect((HOST, PORT))

        clientSocket.setblocking(False)

        with clientSocket:
            logging.info(f"Conectado a {HOST}")

            while True:
                # Envio de datos
                data = input(f"Ingrese datos para enviar a {HOST}: ")

                if data == "exit":
                    break

                else:
                    clientSocket.sendall(bytes(data, "utf-8"))

                # Lectura de datos
                try:
                    data = clientSocket.recv(1024)

                    if not data:
                        break

                    data = data.decode("utf-8")

                    logging.info(f"Datos desde {HOST}: {data}")

                except socket.error:
                    pass

        logging.info(f"Desconectado desde {HOST}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
