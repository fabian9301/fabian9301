import streamlit as st
import numpy as np
import scipy.stats as stats
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Análisis de Confiabilidad Weibull", layout="wide")

# 📌 Título de la aplicación
st.title("📊 Análisis de Confiabilidad Weibull")

# 🔹 Entrada de datos en la barra lateral
st.sidebar.header("🔧 Ingresar Datos del Equipo")
equipo = st.sidebar.text_input("Nombre del equipo", "Motor")
marca = st.sidebar.text_input("Marca", "Siemens")
modelo = st.sidebar.text_input("Modelo", "X2000")
horas_actuales = st.sidebar.number_input("Horas de operación actuales", min_value=0.0, step=1.0)
tpf_input = st.sidebar.text_area("Tiempos Para Falla (TPF) en horas (separados por comas)", "100,200,300,400")
periodo_confiabilidad = st.sidebar.number_input("Período de análisis", min_value=0.0, step=1.0)

# Función de Análisis Weibull
def weibull_analysis(tpf_values, period, horas_actuales):
    tpf_values = np.sort(tpf_values)
    n = len(tpf_values)
    median_rank = (np.arange(1, n + 1) - 0.3) / (n + 0.4)

    ln_tpf = np.log(tpf_values)
    ln_ln_1_mr = np.log(np.log(1 / (1 - median_rank)))

    beta, ln_eta = np.polyfit(ln_tpf, ln_ln_1_mr, 1)
    eta = np.exp(-ln_eta / beta)

    def reliability(t): return np.exp(-(t / eta) ** beta)

    t_vals = np.linspace(0, period, 100)
    reliability_vals = reliability(t_vals)

    confiabilidad_actual = reliability(horas_actuales) * 100

    return beta, eta, t_vals, reliability_vals, confiabilidad_actual

# 🟢 Botón para ejecutar el análisis
if st.sidebar.button("Ejecutar Análisis"):
    try:
        tpf_values = np.array([float(x.strip()) for x in tpf_input.split(',') if x.strip()])
        beta, eta, t_vals, reliability_vals, confiabilidad_actual = weibull_analysis(tpf_values, periodo_confiabilidad, horas_actuales)

        st.subheader("📌 Resultados del Análisis")
        st.write(f"🔹 **Parámetro de forma (β):** {beta:.2f}")
        st.write(f"🔹 **Parámetro de escala (η):** {eta:.2f} horas")
        st.write(f"🔹 **Confiabilidad del equipo a {horas_actuales:.2f} horas:** {confiabilidad_actual:.2f}%")

        # 🟢 Gráfico de confiabilidad Weibull
        st.subheader("📈 Gráfico de Confiabilidad Weibull")
        fig, ax = plt.subplots()
        ax.plot(t_vals, reliability_vals * 100, label="Confiabilidad (%)", color="blue")
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Confiabilidad (%)")
        ax.set_title("Función de Confiabilidad Weibull")
        ax.grid()
        st.pyplot(fig)

    except ValueError:
        st.error("⚠️ Error: Asegúrate de ingresar solo números separados por comas.")

