import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mi Wallet BTC", layout="wide")
db_file = 'historial_btc.csv'

# --- LÓGICA DE PRECIO EN VIVO ---
# Usamos session_state para forzar que el precio cambie de verdad
if 'precio_fresco' not in st.session_state:
    st.session_state.precio_fresco = 0.0

def obtener_precio_real():
    try:
        # Usamos un parámetro timestamp para que la API no nos de un resultado guardado (cache)
        ts = int(datetime.now().timestamp())
        url = f"https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT&_={ts}"
        response = requests.get(url, timeout=5)
        precio = float(response.json()['price'])
        st.session_state.precio_fresco = precio
        return precio
    except:
        return st.session_state.precio_fresco if st.session_state.precio_fresco > 0 else 0.0

def cargar_datos():
    if os.path.exists(db_file):
        df = pd.read_csv(db_file)
        df['Fecha'] = df['Fecha'].astype(str)
        return df
    return pd.DataFrame(columns=['Fecha', 'Tipo', 'Precio_USD', 'Monto_BTC'])

# --- PROCESAMIENTO ---
df = cargar_datos()

# Si es la primera vez o el usuario pulsa el botón, buscamos precio
if st.session_state.precio_fresco == 0:
    precio_actual = obtener_precio_real()
else:
    precio_actual = st.session_state.precio_fresco

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
m2.metric("Precio Promedio", f"${promedio:,.2f}")
m3.metric("Inversión Total", f"${inversion_total:,.2f}")

st.divider()

# BLOQUE DE MERCADO
st.subheader(f"🚀 Mercado en Vivo (Precio: ${precio_actual:,.2f})")
c1, c2, c3 = st.columns(3)

color_delta = "normal" if ganancia_usd >= 0 else "inverse"

c1.metric("Valor de tu Wallet HOY", f"${valor_actual_wallet:,.2f}")
c2.metric("Ganancia/Pérdida Total", f"${ganancia_usd:,.2f}", delta=f"${ganancia_usd:,.2f}", delta_color=color_delta)
c3.metric("Rendimiento", f"{porcentaje:.2f}%", delta=f"{porcentaje:.2f}%", delta_color=color_delta)

# EL BOTÓN DE ACTUALIZAR AHORA SÍ O SÍ RECARGA EL PRECIO
if st.button("🔄 ACTUALIZAR PRECIO AHORA"):
    obtener_precio_real()
    st.rerun()

st.divider()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📝 Nueva Operación")
    with st.form("registro_form", clear_on_submit=True):
        tipo = st.selectbox("Tipo", ["Compra", "Retiro"])
        fecha = st.date_input("Fecha", datetime.now())
        precio_f = st.number_input("Precio USD", value=precio_actual, format="%.2f")
        # Aquí permitimos 8 decimales en la entrada
        monto_f = st.number_input("Monto BTC", min_value=0.0, format="%.8f", step=0.00000001)
        
        if st.form_submit_button("🚀 Guardar Registro"):
            if monto_f > 0:
                nueva_fila = pd.DataFrame([[str(fecha), tipo, precio_f, monto_f]], columns=df.columns)
                df_final = pd.concat([df, nueva_fila], ignore_index=True)
                df_final.to_csv(db_file, index=False)
                st.success("✅ Guardado")
                st.rerun()

    st.divider()
    if st.button("🗑️ Borrar última fila"):
        if not df.empty:
            df = df[:-1]
            df.to_csv(db_file, index=False)
            st.rerun()

# --- HISTORIAL (CORREGIDO PARA EVITAR EL ERROR DE LA IMAGEN) ---
st.subheader("📜 Historial Detallado")
if not df.empty:
    df_visible = df.iloc[::-1].copy()
    # En lugar de usar .style (que da error), usamos una configuración simple de Streamlit
    st.dataframe(
        df_visible, 
        use_container_width=True,
        column_config={
            "Monto_BTC": st.column_config.NumberColumn("Monto BTC", format="%.8f"),
            "Precio_USD": st.column_config.NumberColumn("Precio USD", format="$%.2f")
        }
    )
else:
    st.info("Sin registros.")
