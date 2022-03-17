#!/bin/python3

import sympy as sym


class laplaceInput():
    # Atributos
    __U: list = None
    __U_k: list[list] = None

    def __init__(self, U_0 = 0) -> None:
        self.__U = [U_0]
        self.__U_k = [[0, 0, 0, 0, 0]]

    def addRampInput(self, t_i: float, k_f: float, m: float) -> None:
        # Simbolos
        s = sym.Symbol('s', complex=True)

        # Variables de la rampa anterior
        t_i_prev = self.__U_k[len(self.__U_k) - 1][0]
        t_f_prev = self.__U_k[len(self.__U_k) - 1][1]
        k_i_prev = self.__U_k[len(self.__U_k) - 1][2]
        k_f_prev = self.__U_k[len(self.__U_k) - 1][3]
        m_prev = self.__U_k[len(self.__U_k) - 1][4]

        # Si la nueva entrada inicia antes que termine la anterior
        if t_i < t_f_prev:
            # Recalculamos los tramos finales
            k_f_prev = (t_i - t_i_prev) * m_prev + k_i_prev

            k_i = k_f_prev

            t_f_prev = (k_f_prev - k_i_prev) / m_prev + t_i_prev

            # Borramos la rampa anterior y reajustamos
            self.__U.pop()
            self.__U_k.pop()

            # Calculamos la entrada
            # Rampa
            U_1 = (k_f_prev - k_i_prev) / ((t_f_prev - t_i_prev) * s**2)

            # Activacion
            U_2 = sym.exp(-t_i_prev * s) * U_1

            # Desactivacion
            U_3 = sym.exp(-t_f_prev * s) * U_1

            # Resultado
            self.__U.append(U_2 - U_3)
            self.__U_k.append([t_i_prev, t_f_prev, k_i_prev, k_f_prev, m_prev])

        else:
            k_i = k_f_prev

        # Si la ganancia final es menor a la inicial entonces la pendiente es negativa
        if k_f < k_i:
            m = -m

        t_f = (k_f - k_i) / m + t_i

        if (t_f - t_i) <= 0:
            return

        # Calculamos la entrada
        # Rampa
        U_1 = (k_f - k_i) / ((t_f - t_i) * s**2)

        # Activacion
        U_2 = sym.exp(-t_i * s) * U_1

        # Desactivacion
        U_3 = sym.exp(-t_f * s) * U_1

        # Resultado
        self.__U.append(U_2 - U_3)
        self.__U_k.append([t_i, t_f, k_i, k_f, m])

    def getInputs(self):
        return self.__U

    def getInput(self):
        U_f = 0

        for U_s in self.__U:
            U_f += U_s

        return U_f