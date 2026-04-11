import streamlit as st
import pandas as pd
from supabase import create_client, Client
import requests
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="BTC Command Center", layout="wide", page_icon="🧡")

# Conexión a Supabase
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Revisa las llaves en los Secrets de Streamlit.")

# --- FUNCIONES ---
def obtener_precio_btc():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        return float(r.json()['bitcoin']['usd'])
    except:
        return 0.0

def cargar_datos():
    try:
        res = supabase.table('historial_btc').select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame(columns=['id', 'Fecha', 'Tipo', 'Precio_USD', 'Monto_BTC'])

# --- LÓGICA ---
df = cargar_datos()
precio_mercado = obtener_precio_btc()

# Inicializamos valores por si la tabla está vacía
total_btc = 0.0
promedio_compra = 0.0
inversion_total = 0.0

if not df.empty:
    compras = df[df['Tipo'] == 'Compra']
    retiros = df[df['Tipo'] == 'Retiro']
    total_btc = compras['Monto_BTC'].sum() - retiros['Monto_BTC'].sum()
    inversion_total = (compras['Precio_USD'] * compras['Monto_BTC']).sum()
    if not compras.empty and compras['Monto_BTC'].sum() > 0:
        promedio_compra = inversion_total / compras['Monto_BTC'].sum()

valor_actual = total_btc * precio_mercado
ganancia_neta = valor_actual - (total_btc * promedio_compra) if total_btc > 0 else 0
rendimiento_pct = ((precio_mercado - promedio_compra) / promedio_compra * 100) if promedio_compra > 0 else 0

# --- INTERFAZ ---
st.title("🧡 Mi Centro de Mando BTC")

t1, t2, t3 = st.tabs(["📊 Dashboard", "📜 Historial", "➕ Registro"])

with t1:
    # Métricas Principales
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Saldo Wallet", f"{total_btc:.8f} BTC")
    col_b.metric("Precio Promedio", f"${promedio_compra:,.2f}")
    col_c.metric("Inversión Total", f"${inversion_total:,.2f}")
    
    st.divider()
    
    # Mercado en Vivo
    st.subheader(f"🚀 Mercado (Precio Actual: ${precio_mercado:,.2f})")
    col_x, col_y, col_z = st.columns(3)
    color_flecha = "normal" if ganancia_neta >= 0 else "inverse"
    
    col_x.metric("Valor Hoy", f"${valor_actual:,.2f}")
    col_y.metric("Ganancia/Pérdida", f"${ganancia_neta:,.2f}", delta=f"${ganancia_neta:,.2f}", delta_color=color_flecha)
    col_z.metric("Rendimiento", f"{rendimiento_pct:.2f}%", delta=f"{rendimiento_pct:.2f}%", delta_color=color_flecha)

with t2:
    st.subheader("📜 Movimientos en la Nube")
    if not df.empty:
        # Mostramos la tabla sin formatos raros para evitar errores
        st.dataframe(
            df.sort_values('id', ascending=False),
            use_container_width=True,
            column_config={
                "Monto_BTC": st.column_config.NumberColumn(format="%.8f"),
                "Precio_USD": st.column_config.NumberColumn(format="$%.2f")
            }
        )
        if st.button("🗑️ Borrar último registro"):
            id_a_borrar = int(df['id'].max())
            supabase.table('historial_btc').delete().eq('id', id_a_borrar).execute()
            st.rerun()
    else:
        st.info("No hay datos en Supabase.")

with t3:
    st.subheader("📝 Nueva Transacción")
    with st.form("form_registro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        tipo_op = c1.selectbox("Tipo", ["Compra", "Retiro"])
        fecha_op = c1.date_input("Fecha", datetime.now())
        precio_op = c2.number_input("Precio USD", value=precio_mercado, format="%.2f")
        monto_op = c2.number_input("Monto BTC", format="%.8f", step=0.00000001)
        
        if st.form_submit_button("💾 Guardar en Supabase"):
            if monto_op > 0:
                nueva_data = {
                    "Fecha": str(fecha_op),
                    "Tipo": tipo_op,
                    "Precio_USD": float(precio_op),
                    "Monto_BTC": float(monto_op)
                }
                supabase.table('historial_btc').insert(nueva_data).execute()
                st.success("¡Guardado correctamente!")
                st.rerun()
