import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# 🟢 Configuración de la Página
st.set_page_config(page_title="Análisis de Confiabilidad Weibull", layout="wide")

# 🟢 Función para Generar el PDF con Gráficas
def generate_pdf(equipo, marca, modelo, beta, interpretacion_beta, eta, horas_actuales, confiabilidad_actual, df_recomendaciones, df_weibull, fig_reliability, fig_failure, fig_weibull):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Título del informe
    elements.append(Paragraph("<b>Análisis de Confiabilidad de Equipo - Armada Nacional</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Información General
    elements.append(Paragraph(f"<b>Equipo:</b> {equipo}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Marca:</b> {marca}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Modelo:</b> {modelo}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Parámetro de forma (β):</b> {beta:.2f} - {interpretacion_beta}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Parámetro de escala (η):</b> {eta:.2f} horas", styles["Normal"]))
    elements.append(Paragraph(f"<b>Confiabilidad a {horas_actuales:.2f} horas:</b> {confiabilidad_actual:.2f}%", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Guardar las imágenes de las gráficas
    for fig, filename in zip([fig_reliability, fig_failure, fig_weibull], ["reliability.png", "failure.png", "weibull.png"]):
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format="png")
        img_buffer.seek(0)
        with open(filename, "wb") as f:
            f.write(img_buffer.getbuffer())
        elements.append(Image(filename, width=400, height=250))
        elements.append(Spacer(1, 12))

    # Guardar PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_pdf(equipo, marca, modelo, beta, interpretacion_beta, eta, horas_actuales, confiabilidad_actual, df_recomendaciones, df_weibull):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)

    # 📌 Información del Análisis
    c.drawString(100, 750, "Análisis de Confiabilidad Weibull")
    c.drawString(100, 730, f"Equipo: {equipo}, Marca: {marca}, Modelo: {modelo}")
    c.drawString(100, 710, f"β: {beta:.2f} - {interpretacion_beta}")
    c.drawString(100, 690, f"η: {eta:.2f} horas")
    c.drawString(100, 670, f"Confiabilidad a {horas_actuales} horas: {confiabilidad_actual:.2f}%")

    # 📊 Tabla de Recomendaciones
    c.drawString(100, 640, "Recomendaciones de Mantenimiento:")
    y_pos = 620
    for index, row in df_recomendaciones.iterrows():
        c.drawString(120, y_pos, f"Confiabilidad {row['Confiabilidad (%)']}% - {row['Horas de operación']:.2f}h: {row['Recomendación']}")
        y_pos -= 20

    c.save()
    buffer.seek(0)
    return buffer

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
        interpretacion_beta = "⚠️ Fallas tempranas - Problemas de fabricación"
    elif 1 <= beta < 3:
        interpretacion_beta = "🔄 Fallas aleatorias - Tasa de falla constante"
    else:
        interpretacion_beta = "⏳ Fallas por desgaste - Fase de deterioro"
  
    def reliability(t): return np.exp(-(t / eta) ** beta)

    t_vals = np.linspace(0, period, 100)
    reliability_vals = reliability(t_vals)
    probability_failure = 1 - reliability_vals

    confiabilidad_actual = reliability(horas_actuales) * 100

    confiabilidad_niveles = [85, 80, 72, 60, 55, 50]
    horas_confiabilidad = {c: eta * (-np.log(c / 100)) ** (1 / beta) for c in confiabilidad_niveles}

    df_recomendaciones = pd.DataFrame({
        'Confiabilidad (%)': confiabilidad_niveles,
        'Horas de operación': [horas_confiabilidad[c] for c in confiabilidad_niveles],
        'Recomendación': ["Prueba funcional", "Inspección CBM - PdM", "Prueba funcional",
                          "Inspección CBM", "Prueba funcional", "Mantenimiento Preventivo"]
    })

    df_weibull = pd.DataFrame({
        'TPF': tpf_values,
        'RM (%)': median_rank * 100,
        'ln(Hora de falla)': ln_tpf,
        'ln(ln(1/(1-Median Rank)))': ln_ln_1_mr
    })

    return beta, eta, confiabilidad_actual, interpretacion_beta, df_recomendaciones, df_weibull, t_vals, reliability_vals, probability_failure, ln_tpf, ln_ln_1_mr

# 🟢 Ejecutar el Análisis con un Botón
if st.sidebar.button("Ejecutar Análisis"):
    try:
        tpf_values = np.array([float(x.strip()) for x in tpf_values.split(',') if x.strip()])
        beta, eta, confiabilidad_actual, interpretacion_beta, df_recomendaciones, df_weibull, t_vals, reliability_vals, probability_failure, ln_tpf, ln_ln_1_mr = weibull_analysis(tpf_values, periodo_confiabilidad, horas_actuales)

        # 📌 Mostrar Resultados
        st.subheader("📌 Resultados del Análisis")
        st.write(f"🔹 **Parámetro de forma (β):** {beta:.2f}")
        st.write(f"📊 **Interpretación del β:** {interpretacion_beta}")
        st.write(f"🔹 **Parámetro de escala (η):** {eta:.2f} horas")
        st.write(f"🔹 **Confiabilidad a {horas_actuales:.2f} horas:** {confiabilidad_actual:.2f}%")

        # 📊 Tablas
        st.subheader("📊 Recomendaciones de Mantenimiento")
        st.dataframe(df_recomendaciones)

        st.subheader("📊 Datos del Cálculo Weibull")
        st.dataframe(df_weibull)

        # 📈 Gráficos
        fig, ax = plt.subplots()
        ax.scatter(ln_tpf, ln_ln_1_mr, color="purple", label="Ln(ln(1/(1-MR))) vs Ln(TPF)")
        ax.set_xlabel("Ln(TPF)")
        ax.set_ylabel("Ln(ln(1/(1-MR)))")
        ax.set_title("Gráfico de Verificación Weibull")
        ax.legend()
        ax.grid()
        st.pyplot(fig)

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
    
        # 🟢 Generar PDF
        pdf_buffer = generate_pdf(equipo, marca, modelo, beta, interpretacion_beta, eta, horas_actuales, confiabilidad_actual, df_recomendaciones, df_weibull)
        
        # 📄 Botón para Descargar el PDF
        st.download_button("📄 Descargar Informe en PDF", data=pdf_buffer, file_name="analisis_weibull.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"⚠️ Ocurrió un error inesperado: {str(e)}")
