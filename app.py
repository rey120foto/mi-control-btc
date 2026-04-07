import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mi Wallet BTC", layout="wide")
db_file = 'historial_btc.csv'

# --- LÓGICA DE ACTUALIZACIÓN ---
if 'count' not in st.session_state:
    st.session_state.count = 0

def forzar_actualizacion():
    st.session_state.count += 1
    st.rerun()

def obtener_precio_btc():
    try:
        # Añadimos un parámetro aleatorio para evitar que el navegador guarde el precio viejo
        url = f"https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT&cb={st.session_state.count}"
        response = requests.get(url, timeout=5)
        return float(response.json()['price'])
    except:
        return 0.0

def cargar_datos():
    if os.path.exists(db_file):
        df = pd.read_csv(db_file)
        df['Fecha'] = df['Fecha'].astype(str)
        return df
    return pd.DataFrame(columns=['Fecha', 'Tipo', 'Precio_USD', 'Monto_BTC'])

# --- CÁLCULOS ---
df = cargar_datos()
precio_actual = obtener_precio_btc()

compras_df = df[df['Tipo']=='Compra']
retiros_df = df[df['Tipo']=='Retiro']

total_btc = compras_df['Monto_BTC'].sum() - retiros_df['Monto_BTC'].sum()
inversion_total = (compras_df['Precio_USD'] * compras_df['Monto_BTC']).sum()
promedio = inversion_total / compras_df['Monto_BTC'].sum() if not compras_df.empty else 0

valor_actual_wallet = total_btc * precio_actual
ganancia_usd = valor_actual_wallet - (total_btc * promedio) if total_btc > 0 else 0
porcentaje = ((precio_actual - promedio) / promedio * 100) if promedio > 0 else 0

# --- INTERFAZ ---
st.title("📊 Mi Centro de Mando BTC")

m1, m2, m3 = st.columns(3)
m1.metric("Saldo Real en Wallet", f"{total_btc:.8f} BTC")
m2.metric("Precio Promedio de Compra", f"${promedio:,.2f}")
m3.metric("Inversión Neta Actual", f"${inversion_total:,.2f}")

st.divider()

# RENDIMIENTO EN VIVO
st.subheader(f"🚀 Mercado en Vivo (Precio Actual: ${precio_actual:,.2f})")
c1, c2, c3 = st.columns(3)

# Definir color del delta
delta_color = "normal" if ganancia_usd >= 0 else "inverse"

c1.metric("Valor de tu Wallet HOY", f"${valor_actual_wallet:,.2f}")
c2.metric("Ganancia/Pérdida Total", f"${ganancia_usd:,.2f}", delta=f"${ganancia_usd:,.2f}", delta_color=delta_color)
c3.metric("Rendimiento del Portafolio", f"{porcentaje:.2f}%", delta=f"{porcentaje:.2f}%", delta_color=delta_color)

if st.button("🔄 ACTUALIZAR PRECIO AHORA"):
    forzar_actualizacion()

st.divider()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📝 Nueva Operación")
    with st.form("registro_form", clear_on_submit=True):
        tipo = st.selectbox("Tipo", ["Compra", "Retiro"])
        fecha = st.date_input("Fecha", datetime.now())
        precio_f = st.number_input("Precio USD", value=precio_actual, format="%.2f")
        monto_f = st.number_input("Monto BTC (8 decimales)", min_value=0.0, format="%.8f", step=0.00000001)
        
        if st.form_submit_button("🚀 Guardar Registro"):
            if monto_f > 0:
                nueva_fila = pd.DataFrame([[str(fecha), tipo, precio_f, monto_f]], columns=df.columns)
                df_final = pd.concat([df, nueva_fila], ignore_index=True)
                df_final.to_csv(db_file, index=False)
                st.success("✅ Guardado")
                st.rerun()
            else:
                st.error("El monto debe ser mayor a 0")

    st.divider()
    st.header("⚠️ Zona de Edición")
    if st.button("🗑️ Borrar última fila"):
        if not df.empty:
            df = df[:-1]
            df.to_csv(db_file, index=False)
            st.warning("Fila eliminada")
            st.rerun()

# --- HISTORIAL CON PRECISIÓN ---
st.subheader("📜 Historial Detallado")
if not df.empty:
    # Formateamos la tabla para que muestre todos los decimales de BTC
    df_mostrar = df.iloc[::-1].copy()
    st.dataframe(
        df_mostrar.style.format({
            'Monto_BTC': '{:.8f}',
            'Precio_USD': '${:,.2;f}'
        }),
        use_container_width=True
    )
else:
    st.info("Sin registros.")
