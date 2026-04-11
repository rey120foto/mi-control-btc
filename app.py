import streamlit as st
import pandas as pd
from supabase import create_client, Client
import requests
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="BTC Command Center Pro", layout="wide", page_icon="🧡")

# Conexión a Supabase (Caja Fuerte)
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNCIONES DE DATOS ---
def obtener_precio_btc():
    try:
        url_api = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        return float(requests.get(url_api, timeout=10).json()['bitcoin']['usd'])
    except:
        return 0.0

def cargar_datos_supabase():
    # Traemos los datos de la nube de Supabase
    response = supabase.table('historial_btc').select("*").execute()
    return pd.DataFrame(response.data)

# --- PROCESAMIENTO ---
df = cargar_datos_supabase()
precio_actual = obtener_precio_btc()

if not df.empty:
    compras_df = df[df['Tipo']=='Compra']
    retiros_df = df[df['Tipo']=='Retiro']
    total_btc = compras_df['Monto_BTC'].sum() - retiros_df['Monto_BTC'].sum()
    inversion_total = (compras_df['Precio_USD'] * compras_df['Monto_BTC']).sum()
    promedio = inversion_total / compras_df['Monto_BTC'].sum() if not compras_df.empty else 0
else:
    total_btc, inversion_total, promedio = 0.0, 0.0, 0.0

valor_actual_wallet = total_btc * precio_actual
ganancia_usd = valor_actual_wallet - (total_btc * promedio) if total_btc > 0 else 0
porcentaje = ((precio_actual - promedio) / promedio * 100) if promedio > 0 else 0

# --- INTERFAZ ---
st.title("🧡 BTC Pro Dashboard (Supabase Edition)")

tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "📋 Historial", "➕ Registrar"])

with tab1:
    m1, m2, m3 = st.columns(3)
    m1.metric("Saldo en Wallet", f"{total_btc:.8f} BTC")
    m2.metric("Precio Promedio", f"${promedio:,.2f}")
    m3.metric("Inversión Total", f"${inversion_total:,.2f}")
    st.divider()
    c1, c2, c3 = st.columns(3)
    color_delta = "normal" if ganancia_usd >= 0 else "inverse"
    c1.metric("Valor Actual ($)", f"${valor_actual_wallet:,.2f}")
    c2.metric("Ganancia/Pérdida", f"${ganancia_usd:,.2f}", delta=f"${ganancia_usd:,.2f}", delta_color=color_delta)
    c3.metric("Rendimiento %", f"{porcentaje:.2f}%", delta=f"{porcentaje:.2f}%", delta_color=color_delta)

with tab2:
    if not df.empty:
        st.dataframe(df.sort_values('id', ascending=False), use_container_width=True,
                     column_config={"Monto_BTC": st.column_config.NumberColumn(format="%.8f"),
                                    "Precio_USD": st.column_config.NumberColumn(format="$%.2f")})
        if st.button("🗑️ Borrar ÚLTIMA entrada"):
            last_id = df['id'].max()
            supabase.table('historial_btc').delete().eq('id', last_id).execute()
            st.rerun()

with tab3:
    with st.form("registro_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        tipo = col_a.selectbox("Operación", ["Compra", "Retiro"])
        fecha = col_a.date_input("Fecha", datetime.now())
        precio_f = col_b.number_input("Precio USD", value=precio_actual, format="%.2f")
        monto_f = col_b.number_input("Monto BTC", min_value=0.0, format="%.8f", step=0.00000001)
        
        if st.form_submit_button("✅ Guardar en Supabase"):
            data = {"Fecha": str(fecha), "Tipo": tipo, "Precio_USD": precio_f, "Monto_BTC": monto_f}
            supabase.table('historial_btc').insert(data).execute()
            st.success("¡Datos blindados en la nube!")
            st.rerun()
