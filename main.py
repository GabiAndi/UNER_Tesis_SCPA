#!/bin/python3

from getpass import getpass
import sys
import threading
import time
import logging
import sympy as sym
import matplotlib.pyplot as plt
import socket

from laplace import laplaceInput


# Constantes
HOST = ""
PORT = 36001

# Tiempo de resuesta del sensor
TIME_SENSOR = 1

# Tiempo de salto para cálculo del sensor
TIME_STEP = 0.1

# Variables globales
data_od_value = []
data_ramp_value = []
data_time = []
exit = False
rpm = 0

# Cliente
clientSocket:socket.socket = None

def scpa(c_max: float, c_min: float, tau: float, rpm_max: float, rpm_acel: float):
    global exit
    global rpm
    global data_od_value
    global data_ramp_value
    global data_time

    logging.info("Iniciando")

    # Simbolos de operacion
    t = sym.Symbol('t', real=True)
    s = sym.Symbol('s', complex=True)

    # Simbolos del sistema
    a = sym.Symbol('a', real=True)
    T = sym.Symbol('tau', real=True)
    k = sym.Symbol('k', real=True)

    p = sym.Symbol('p', real=True)

    # Variable de tiempo
    t_t = 0.01

    # Sistema
    A_s = a / s
    C_s = k / (T * s + 1)

    # Entrada
    U = laplaceInput()

    U_s = U.getInput()

    G_t = sym.inverse_laplace_transform(C_s * U_s + A_s, s, t)
    U_t = sym.inverse_laplace_transform(U_s, s, t)

    # Variables
    current_rpm = rpm
    t_delta = 0
    k_i_i = 0

    while not exit:
        # Si el tiempo de operación fue largo se recorta el vector de datos
        if t_t > (6.5 + t_delta):
            data_od_value.clear()
            data_ramp_value.clear()
            data_time.clear()

            t_delta = 0

            t_t = 0.01

            k_i_i = rpm / rpm_max

            U = laplaceInput((1 + 1 / s) * p, [0, 0, 0, k_i_i, 0])

            U_s = U.getInput()

            G_t = sym.inverse_laplace_transform(C_s * U_s + A_s, s, t)
            U_t = sym.inverse_laplace_transform(U_s, s, t)

        # Si las rpm cambiaron se ajusta el sistema
        if rpm != current_rpm:
            t_delta = t_t

            U.addRampInput(t_t, rpm / rpm_max, rpm_acel)

            U_s = U.getInput()

            G_t = sym.inverse_laplace_transform(C_s * U_s + A_s, s, t)
            U_t = sym.inverse_laplace_transform(U_s, s, t)
            
            current_rpm = rpm

        # Se sustituyen los valores
        c_t = sym.exp.subs(G_t, ([a, c_min], [k, c_max - c_min], [T, tau], [t, t_t], [p, k_i_i]))
        u_t = sym.exp.subs(U_t, ([t, t_t], [p, k_i_i]))

        logging.debug("t = %f, OD = %f", t_t, c_t)

        # Se guarda para graficar
        data_od_value.append(c_t)
        data_ramp_value.append(u_t)
        data_time.append(len(data_time))

        t_t += TIME_STEP

        time.sleep(TIME_SENSOR)

    logging.info("Cerrando")

def capture():
    global exit

    logging.info("Iniciando")

    while not exit:
        inputValue = getpass("")

        if inputValue == "exit":
            exit = True

    logging.info("Cerrando")

def server():
    global exit
    global rpm
    global clientSocket

    # Abrimos el servidor
    logging.info("Iniciando servidor")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSocket:
        serverSocket.bind((HOST, PORT))
        serverSocket.listen()

        logging.info(f"Iniciado por el puerto {PORT}")

        serverSocket.setblocking(False)

        while not exit:
            try:
                (clientSocket, address) = serverSocket.accept()

                clientSocket.setblocking(False)

                logging.info(f"Cliente desde {address}")

                disconnected = False

                while (not exit) or (not disconnected):
                    try:
                        data = clientSocket.recv(1024)

                        if not data:
                            break

                        data = data.decode('utf-8')

                        logging.info(f"Recibido desde {address}: {data}")

                        if data.find("od") != -1:
                            if len(data_od_value) > 0:
                                clientSocket.sendall(bytes(f"{data_od_value[len(data_od_value) - 1]}", "utf-8"))

                            data = data.strip("od")

                        if data.find("rpm=") != -1:
                            rpm = float(data.strip("rpm="))     

                    except socket.timeout:
                        pass

                    except socket.error:
                        disconnected = True

                logging.info(f"Cliente desconectado desde {address}")

            except socket.error:
                pass

        logging.info("Servidor cerrado")

def main(args: list[str]=[]) -> int:
    global data_od_value
    global data_ramp_value
    global data_time

    # Logging
    logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(threadName)s: %(message)s', level=logging.DEBUG)

    logging.info("Ejecución iniciada")

    # Constantes del modelo
    c_max = None        # Valor máximo de OD
    c_min = None        # Valor mínimo de OD
    tau = None          # Constante de tiempo
    rpm_max = None      # Revoluciones por minuto maximas del sistema
    rpm_acel = None     # Rampa de aceleracion del variador

    for i in args:
        if i.find("-c_max=") != -1:
            c_max = float(i.strip("-c_max="))

        if i.find("-c_min=") != -1:
            c_min = float(i.strip("-c_min="))

        if i.find("-tau=") != -1:
            tau = float(i.strip("-tau="))

        if i.find("-rpm_max=") != -1:
            rpm_max = float(i.strip("-rpm_max="))

        if i.find("-rpm_acel=") != -1:
            rpm_acel = float(i.strip("-rpm_acel="))

    if (c_max is None) or (c_min is None) or (tau is None) or (rpm_max is None) or (rpm_acel is None):
        logging.fatal("Tiene que especificar las constantes del sistema")

        return -1

    logging.info("c_max = %f", c_max)
    logging.info("c_min = %f", c_min)
    logging.info("tau = %f", tau)
    logging.info("rpm_max = %f", rpm_max)
    logging.info("rpm_acel = %f", rpm_acel)

    # Inicio de la simulación
    threadSCPA = threading.Thread(name="SCPA", target=scpa, args=(c_max, c_min, tau, rpm_max, rpm_acel))
    threadSCPA.start()

    # Inicio la captura de las teclas
    threadCapture = threading.Thread(name="Capture", target=capture)
    threadCapture.start()

    # Servidor de OD
    threadServer = threading.Thread(name="Server", target=server)
    threadServer.start()

    # Se espera a que termine los hilos
    threadSCPA.join()
    threadCapture.join()
    threadServer.join()

    # Nivel de OD en funcion del tiempo
    plt.figure(1)
    plt.plot(data_time, data_od_value)
    plt.savefig("graph/od.png")

    # Nivel de la entrada en funcion al tiempo
    plt.figure(2)
    plt.plot(data_time, data_ramp_value)
    plt.savefig("graph/input.png")

    logging.info("Ejecución terminada")

    return 0

if __name__ == "__main__":
    # Prueba
    sys.exit(main(["-c_max=3.86", "-c_min=0.6", "-tau=1", "-rpm_max=2800", "-rpm_acel=0.6"]))
    
    # Real
    #sys.exit(main(sys.argv))
