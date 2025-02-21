import streamlit as st
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import pandas as pd

# 🟢 Configuración de la Página
st.set_page_config(page_title="Análisis de Confiabilidad Weibull", layout="wide")

# 🟢 Título
st.title("📊 Análisis de Confiabilidad Weibull")

# 🟢 Entrada de Datos en la Barra Lateral
st.sidebar.header("🔧 Ingresar Datos del Equipo")
equipo = st.sidebar.text_input("Nombre del equipo", "Motor")
marca = st.sidebar.text_input("Marca", "Siemens")
modelo = st.sidebar.text_input("Modelo", "X2000")
horas_actuales = st.sidebar.number_input("Horas de operación actuales", min_value=0.0, step=1.0)
tpf_values = st.sidebar.text_area("Tiempos Para Falla (TPF) en horas (separados por comas)", "100,200,300,400")
periodo_confiabilidad = st.sidebar.number_input("Período de análisis", min_value=0.0, step=1.0)

# 🟢 Función de Análisis Weibull
def weibull_analysis(tpf_values, period, horas_actuales):
    tpf_values = np.sort(tpf_values)
    n = len(tpf_values)
    median_rank = (np.arange(1, n + 1) - 0.3) / (n + 0.4)

    ln_tpf = np.log(tpf_values)
    ln_ln_1_mr = np.log(np.log(1 / (1 - median_rank)))

    beta, ln_eta = np.polyfit(ln_tpf, ln_ln_1_mr, 1)
    eta = np.exp(-ln_eta / beta)
# 📌 Análisis del Parámetro Beta
    if beta < 1:
        interpretacion_beta = "⚠️ Fallas tempranas - Infant Mortality (Problemas de fabricación o instalación)"
    elif 1 <= beta < 3:
        interpretacion_beta = "🔄 Fallas aleatorias - Tasa de falla constante (Errores de operación o condiciones variables)"
    else:
        interpretacion_beta = "⏳ Fallas por desgaste - Fase de deterioro (Desgaste natural del equipo)"
    def reliability(t): return np.exp(-(t / eta) ** beta)

    t_vals = np.linspace(0, period, 100)
    reliability_vals = reliability(t_vals)
    probability_failure = 1 - reliability_vals

    confiabilidad_actual = reliability(horas_actuales) * 100

    confiabilidad_niveles = [85, 80, 72, 60, 55, 50]
    horas_confiabilidad = {c: eta * (-np.log(c / 100)) ** (1 / beta) for c in confiabilidad_niveles}
    
    recomendaciones = {
        85: "Prueba funcional",
        80: "Inspección CBM - PdM",
        72: "Prueba funcional",
        60: "Inspección CBM",
        55: "Prueba funcional",
        50: "Mantenimiento Preventivo"
    }

    df_recomendaciones = pd.DataFrame({
        'Confiabilidad (%)': confiabilidad_niveles,
        'Horas de operación': [horas_confiabilidad[c] for c in confiabilidad_niveles],
        'Recomendación': [recomendaciones[c] for c in confiabilidad_niveles]
    })

    df_weibull = pd.DataFrame({
        'TPF': tpf_values,
        'RM (%)': median_rank * 100,
        'ln(Hora de falla)': ln_tpf,
        'ln(ln(1/(1-MR)))': ln_ln_1_mr
    })

    return beta, eta, confiabilidad_actual, df_recomendaciones, df_weibull, t_vals, reliability_vals, probability_failure

# 🟢 Ejecutar el Análisis con un Botón
if st.sidebar.button("Ejecutar Análisis"):
    try:
        tpf_values = np.array([float(x.strip()) for x in tpf_values.split(',') if x.strip()])
        beta, eta, confiabilidad_actual, df_recomendaciones, df_weibull, t_vals, reliability_vals, probability_failure = weibull_analysis(tpf_values, periodo_confiabilidad, horas_actuales)

        # 📌 Mostrar Resultados
        st.subheader("📌 Resultados del Análisis")
        st.write(f"🔹 **Parámetro de forma (β):** {beta:.2f}")
        st.write(f"🔹 **Parámetro de escala (η):** {eta:.2f} horas")
        st.write(f"🔹 **Confiabilidad del equipo a {horas_actuales:.2f} horas:** {confiabilidad_actual:.2f}%")

        # 📊 Tabla de Recomendaciones
        st.subheader("📊 Recomendaciones de Mantenimiento")
        st.dataframe(df_recomendaciones)

        # 📊 Tabla de Cálculo de Weibull
        st.subheader("📊 Datos de Cálculo Weibull")
        st.dataframe(df_weibull)

        # 📈 Gráfico de Confiabilidad Weibull
        st.subheader("📈 Gráfico de Confiabilidad Weibull")
        fig, ax = plt.subplots()
        ax.plot(t_vals, reliability_vals * 100, label="Confiabilidad (%)", color="blue")
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Confiabilidad (%)")
        ax.set_title("Función de Confiabilidad Weibull")
        ax.grid()
        st.pyplot(fig)

        # 📈 Gráfico de Probabilidad de Falla
        st.subheader("📈 Gráfico de Probabilidad de Falla")
        fig2, ax2 = plt.subplots()
        ax2.plot(t_vals, probability_failure * 100, label="Probabilidad de Falla (%)", color="red")
        ax2.set_xlabel("Tiempo")
        ax2.set_ylabel("Probabilidad de Falla (%)")
        ax2.set_title("Función de Probabilidad de Falla")
        ax2.grid()
        st.pyplot(fig2)

    except ValueError:
        st.error("⚠️ Error: Asegúrate de ingresar solo números separados por comas.")

