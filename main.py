#!/bin/python3

from getpass import getpass
import sys
import threading
import time
import logging
import sympy as sym
import matplotlib.pyplot as plt

# Variables globales
data_od_value = []
data_ramp_value = []
data_time = []
exit = False
rpm = 0

def scpa(c_max: float, c_min: float, tau: float, rpm_max: float):
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

    # Variable de tiempo
    t_t = 0.01

    # Sistema
    A_s = a / s
    C_s = k / (T * s + 1)
    U_s = 0

    G_t = sym.inverse_laplace_transform(C_s * U_s + A_s, s, t)
    U_t = sym.inverse_laplace_transform(U_s, s, t)

    # Variable de seguimiento
    current_rpm = rpm

    while(not exit):
        # Si las rpm cambiaron se ajusta el sistema
        if rpm != current_rpm:
            t_t = 0.01
            c_min = c_t

            if rpm > current_rpm:
                U1_s = (rpm / rpm_max) / (0.20 * s**2)
                U2_s = 1 - sym.exp(-0.20 * s)

                U_s = U1_s * U2_s

                G_t = sym.inverse_laplace_transform(C_s * U_s + A_s, s, t)
                U_t = sym.inverse_laplace_transform(U_s, s, t)

            else:
                U1_s = -(rpm / rpm_max) / (0.20 * s**2)
                U2_s = 1 - sym.exp(-0.20 * s)

                U_s = U1_s * U2_s

                G_t = sym.inverse_laplace_transform(C_s * U_s + A_s, s, t)
                U_t = sym.inverse_laplace_transform(U_s, s, t)

            current_rpm = rpm

        # Se sustituyen los valores
        c_t = sym.exp.subs(G_t, ([a, c_min], [k, c_max - c_min], [T, tau], [t, t_t]))
        
        u_t = sym.exp.subs(U_t, ([t, t_t], ))

        logging.info("OD = %f", c_t)

        # Se guarda para graficar
        data_od_value.append(c_t)
        data_ramp_value.append(u_t)
        data_time.append(len(data_time))

        t_t += 0.01

        time.sleep(0.05)

    logging.info("Cerrando")

def capture():
    global exit
    global rpm

    logging.info("Iniciando")

    while (not exit):
        inputValue = getpass("")

        if inputValue == "exit":
            exit = True

        else:
            rpm = float(inputValue)

            logging.info("rpm = %f", rpm)

    logging.info("Cerrando")

def main(args: list[str]=[]) -> int:
    global data_od_value
    global data_ramp_value
    global data_time

    # Logging
    logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(threadName)s: %(message)s', level=logging.INFO)

    logging.info("Ejecución iniciada")

    # Constantes del modelo
    c_max = None        # Valor máximo de OD
    c_min = None        # Valor mínimo de OD
    tau = None          # Constante de tiempo
    rpm_max = None      # Revoluciones por minuto maximas del sistema

    for i in args:
        if i.find("-c_max=") == 0:
            c_max = float(i.strip("-c_max="))

        if i.find("-c_min=") == 0:
            c_min = float(i.strip("-c_min="))

        if i.find("-tau=") == 0:
            tau = float(i.strip("-tau="))

        if i.find("-rpm_max=") == 0:
            rpm_max = float(i.strip("-rpm_max="))

    if (c_max is None) or (c_min is None) or (tau is None) or (rpm_max is None):
        logging.fatal("Tiene que especificar las constantes del sistema")

        return -1

    logging.info("c_max = %f", c_max)
    logging.info("c_min = %f", c_min)
    logging.info("tau = %f", tau)
    logging.info("rpm_max = %f", rpm_max)

    # Inicio de la simulación
    threadSCPA = threading.Thread(name="SCPA", target=scpa, args=(c_max, c_min, tau, rpm_max))
    threadSCPA.start()

    # Inicio la captura de las teclas
    threadCapture = threading.Thread(name="Capture", target=capture)
    threadCapture.start()

    # Se espera a que termine los hilos
    threadSCPA.join()
    threadCapture.join()

    # Nivel de OD en funcion del tiempo
    plt.figure(1)
    plt.plot(data_time, data_od_value)
    plt.savefig("od.png")

    # Nivel de la entrada en funcion al tiempo
    plt.figure(2)
    plt.plot(data_time, data_ramp_value)
    plt.savefig("input.png")

    logging.info("Ejecución terminada")

if __name__ == "__main__":
    # Prueba
    sys.exit(main(["-c_max=3.86", "-c_min=0.6", "-tau=1", "-rpm_max=2800"]))
    
    # Real
    #sys.exit(main(sys.argv))
