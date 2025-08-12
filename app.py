# app.py
import streamlit as st
import datetime
from config import CUENTAS_COBRO, JWT, COBRO_ENDPOINT
from utils import get_clientes, crear_recibo_pdf, guardar_log, enviar_cobro, obtener_numero_recibo_sos

# Helper para el formato de dinero en el front-end
def _fmt_money_app(n):
    try:
        return f"$ {float(n):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    except Exception:
        return str(n)

st.set_page_config(page_title="Recibo de Cobranzas - SOS", layout="centered")
st.title("🧾 Generar Recibo de Cobranza")

# --- Helpers de estado para medios de cobro ---
if "filas_medios" not in st.session_state:
    st.session_state.filas_medios = [
        {"cuenta": None, "monto": 0.0},
    ]

def agregar_fila_medio():
    st.session_state.filas_medios.append({"cuenta": None, "monto": 0.0})

def quitar_fila_medio(idx):
    if len(st.session_state.filas_medios) > 1:
        st.session_state.filas_medios.pop(idx)

# --- Helpers de estado para descripciones ---
if "filas_descripciones" not in st.session_state:
    st.session_state.filas_descripciones = [
        {"descripcion": "", "monto": 0.0},
    ]

def agregar_fila_descripcion():
    st.session_state.filas_descripciones.append({"descripcion": "", "monto": 0.0})

def quitar_fila_descripcion(idx):
    if len(st.session_state.filas_descripciones) > 1:
        st.session_state.filas_descripciones.pop(idx)

# --- Cache de clientes (sin cambios) ---
@st.cache_data(ttl=300)
def _clientes_cached(jwt):
    return get_clientes(jwt)

clientes = _clientes_cached(JWT)
cliente_opciones = {f"{c['nombre']} ({c['cuit']})": c['idclipro'] for c in clientes}
firmantes = ['Daniel Lorenzo', 'Gabriel Lorenzo', 'Matias Lorenzo', 'Federico Lorenzo', 'Pedro Taboada', 'Melina Lorenzo', 'Lucia Ahumada']

# --- Sección de Conceptos de cobro (FUERA DEL FORMULARIO) ---
st.markdown("### 💸 Conceptos de cobro (lo que estás cobrando)")
total_descripciones = 0.0
for i, fila in enumerate(st.session_state.filas_descripciones):
    c1, c2, c3 = st.columns([2, 1, 0.4])
    descripcion = c1.text_input(f"Descripción {i+1}", key=f"descripcion_{i}", value=fila["descripcion"], placeholder="Honorarios, Sindicato, etc.")
    monto = c2.number_input(f"Monto {i+1}", step=100.0, key=f"monto_desc_{i}", value=float(fila["monto"]))
    c3.button("🗑️", key=f"del_desc_{i}", on_click=quitar_fila_descripcion, args=(i,))
    
    st.session_state.filas_descripciones[i] = {"descripcion": descripcion, "monto": monto}
    total_descripciones += monto
st.button("➕ Agregar concepto", on_click=agregar_fila_descripcion)
st.write(f"**Total Conceptos:** ${total_descripciones:,.2f}")

st.markdown("---")

# --- Sección de Medios de cobro (FUERA DEL FORMULARIO) ---
st.markdown("### 💰 Medios de cobro (cómo lo recibís)")
total_medios = 0.0
for i, fila in enumerate(st.session_state.filas_medios):
    c1, c2, c3 = st.columns([2, 1, 0.4])
    cuenta = c1.selectbox(
        f"Medio {i+1}", list(CUENTAS_COBRO.keys()), key=f"cuenta_{i}",
        index=(list(CUENTAS_COBRO.keys()).index(fila["cuenta"]) if fila["cuenta"] in CUENTAS_COBRO else 0)
    )
    monto = c2.number_input(f"Monto {i+1}", step=100.0, key=f"monto_medio_{i}", value=float(fila["monto"]))
    c3.button("🗑️", key=f"del_medio_{i}", on_click=quitar_fila_medio, args=(i,))
    
    # ¡Línea corregida!
    st.session_state.filas_medios[i] = {"cuenta": cuenta, "monto": monto}
    total_medios += monto
st.button("➕ Agregar medio", on_click=agregar_fila_medio)
st.write(f"**Total Medios de cobro:** ${total_medios:,.2f}")

st.markdown("---")

# --- Formulario de datos principales con botón de envío ---
with st.form("form_recibo"):
    st.markdown("### 📝 Datos del recibo")
    cliente_label = st.selectbox("Cliente", list(cliente_opciones.keys()))
    fecha = st.date_input("Fecha", value=datetime.date.today())
    firmante = st.selectbox("Firmante", firmantes)
    
    submitted = st.form_submit_button("Generar Recibo")

# --- Procesamiento ---
if submitted:
    medios = [f for f in st.session_state.filas_medios if f["monto"] != 0]
    descripciones = [f for f in st.session_state.filas_descripciones if f["monto"] != 0]
    
    if not medios and not descripciones:
        st.error("Debés ingresar al menos un concepto o un medio de cobro con monto distinto de cero.")
    elif total_medios != total_descripciones:
        st.error(f"⚠️ El total de Medios de Cobro (${total_medios:,.2f}) no coincide con el total de Conceptos (${total_descripciones:,.2f}). Deben ser iguales.")
    else:
        idclipro = cliente_opciones[cliente_label]
        fecha_str = fecha.strftime("%d-%m-%Y")
        imputaciones = [{"fv": f"{m['monto']:.2f}", "cuid": CUENTAS_COBRO[m['cuenta']]} for m in medios]
        
        memo_parts = [f"{d['descripcion']}: {_fmt_money_app(d['monto'])}" for d in descripciones]
        if firmante:
            memo_parts.append(f"Firmado por {firmante}")
        memo_concatenado = ", ".join(memo_parts)
        
        payload = {
            "fecha": fecha.strftime("%Y-%m-%d"),
            "idclipro": idclipro,
            "idcuenta": CUENTAS_COBRO[medios[0]['cuenta']],
            "memo": memo_concatenado,
            "referencia": None,
            "idcentrocosto": None,
            "idprovinciaiibb": None,
            "imputaciones": imputaciones
        }

        api_resp = None
        api_error = None
        recibo_id = "SIN NÚMERO"
        try:
            api_resp = enviar_cobro(JWT, payload, COBRO_ENDPOINT)
            if api_resp and 'id' in api_resp:
                id_generado = api_resp['id']
                numero_recibo = obtener_numero_recibo_sos(JWT, id_generado)
                if numero_recibo:
                    recibo_id = numero_recibo
                else:
                    st.warning(f"⚠️ No se pudo obtener el número de factura para el ID {id_generado}.")
        except Exception as e:
            api_error = str(e)
            
        pdf_bytes = crear_recibo_pdf(cliente_label, fecha_str, medios, descripciones, recibo_id=recibo_id, firmante=firmante)
        guardar_log(cliente_label, fecha_str, memo_concatenado, medios)

        if api_resp:
            st.success("✅ Recibo generado y enviado a SOS correctamente.")
            st.json(api_resp)
        else:
            st.warning("⚠️ Recibo generado localmente. Envío a API omitido o fallido.")
            if api_error:
                with st.expander("Ver detalle del error de API"):
                    st.code(api_error)

        st.download_button(
            label="📥 Descargar Recibo (PDF)",
            data=pdf_bytes,
            file_name=f"recibo_{recibo_id}_{fecha_str}.pdf",
            mime="application/pdf"
        )