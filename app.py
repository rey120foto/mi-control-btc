import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="BTC Command Center", layout="wide", page_icon="🧡")
db_file = 'historial_btc.csv'

# --- FUNCIÓN DE PRECIO ---
def obtener_precio_btc():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        return float(requests.get(url, timeout=10).json()['bitcoin']['usd'])
    except:
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            return float(requests.get(url, timeout=10).json()['price'])
        except:
            return 0.0

def cargar_datos():
    if os.path.exists(db_file):
        df = pd.read_csv(db_file)
        df['Fecha'] = df['Fecha'].astype(str)
        return df
    return pd.DataFrame(columns=['Fecha', 'Tipo', 'Precio_USD', 'Monto_BTC'])

# --- LÓGICA ---
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

# --- INTERFAZ (TABS) ---
st.title("🧡 Mi Centro de Mando BTC")

# Pestañas para organizar todo
tab1, tab2, tab3 = st.tabs(["📈 Dashboard Real", "📋 Historial", "➕ Registrar"])

with tab1:
    m1, m2, m3 = st.columns(3)
    m1.metric("Saldo en Wallet", f"{total_btc:.8f} BTC")
    m2.metric("Precio Promedio", f"${promedio:,.2f}")
    m3.metric("Inversión Total", f"${inversion_total:,.2f}")

    st.divider()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"🚀 Rendimiento (Precio: ${precio_actual:,.2f})")
        c1, c2, c3 = st.columns(3)
        color_delta = "normal" if ganancia_usd >= 0 else "inverse"
        c1.metric("Valor Actual ($)", f"${valor_actual_wallet:,.2f}")
        c2.metric("Ganancia/Pérdida", f"${ganancia_usd:,.2f}", delta=f"${ganancia_usd:,.2f}", delta_color=color_delta)
        c3.metric("Rendimiento %", f"{porcentaje:.2f}%", delta=f"{porcentaje:.2f}%", delta_color=color_delta)
    
    with col2:
        st.info("💡 Tip: Refresca el navegador para actualizar el precio del mercado.")

with tab2:
    st.subheader("📜 Movimientos Registrados")
    if not df.empty:
        # AQUÍ ESTÁ LA CORRECCIÓN DEL ERROR DE FORMATO (image_24dd65.png)
        st.dataframe(
            df.iloc[::-1], 
            use_container_width=True,
            column_config={
                "Monto_BTC": st.column_config.NumberColumn("Monto BTC", format="%.8f"),
                "Precio_USD": st.column_config.NumberColumn("Precio USD", format="$%.2f") # Corregido
            }
        )
        
        st.divider()
        if st.button("🗑️ Borrar ÚLTIMA entrada"):
            df[:-1].to_csv(db_file, index=False)
            st.rerun()
    else:
        st.write("No hay datos todavía.")

with tab3:
    st.subheader("📝 Nueva Transacción")
    with st.form("main_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            tipo = st.selectbox("Operación", ["Compra", "Retiro"])
            fecha = st.date_input("Fecha", datetime.now())
        with f2:
            precio_f = st.number_input("Precio al momento (USD)", value=precio_actual, format="%.2f")
            monto_f = st.number_input("Cantidad de BTC", min_value=0.0, format="%.8f", step=0.00000001)
        
        submit = st.form_submit_button("✅ Guardar en la Nube")
        
        if submit and monto_f > 0:
            nueva_fila = pd.DataFrame([[str(fecha), tipo, precio_f, monto_f]], columns=df.columns)
            pd.concat([df, nueva_fila], ignore_index=True).to_csv(db_file, index=False)
            st.success("¡Datos guardados!")
            st.rerun()
