# utils.py
import io
import os
import time
import requests
import pandas as pd
from fpdf import FPDF

API_BASE = "https://api.sos-contador.com/api-comunidad"

def _headers(jwt: str):
    return {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

def get_clientes(jwt: str, pagina_inicial: int = 1, registros: int = 50):
    clientes = []
    pagina = pagina_inicial
    while True:
        url = f"{API_BASE}/cliente/listado?proveedor=true&cliente=true&pagina={pagina}&registros={registros}"
        r = requests.get(url, headers=_headers(jwt), timeout=30)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", []) if isinstance(data, dict) else []
        for it in items:
            clientes.append({
                "idclipro": it.get("id"),
                "nombre": it.get("clipro") or it.get("nombre", "Sin nombre"),
                "cuit": it.get("cuit", ""),
            })
        if len(items) < registros:
            break
        pagina += 1
        time.sleep(0.2)
    clientes.sort(key=lambda x: (x["nombre"] or "").lower())
    return clientes

def obtener_numero_recibo_sos(jwt: str, id_recibo: int):
    url = f"{API_BASE}/cobro/listado/mes?pagina=1&registros=1000"
    r = requests.get(url, headers=_headers(jwt), timeout=30)
    r.raise_for_status()
    data = r.json()
    items = data.get("items", [])
    for item in items:
        if item.get("id") == id_recibo:
            return item.get("factura")
    return None

class _ReciboPDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.recibo_id = None
        # Definir un color de línea más suave (gris oscuro)
        self.set_draw_color(150, 150, 150)
        # Definir un ancho de línea más delgado
        self.set_line_width(0.2)

    def header(self):
        script_dir = os.path.dirname(__file__)
        logo_path = os.path.join(script_dir, "logo.png")
        self.image(logo_path, x=10, y=8, w=40)
        
        self.set_y(38)
        self.set_x(10)
        self.set_font("Arial", "", 8)
        self.cell(0, 4, "Riccheri 440/42 (1661) - Bella Vista - Bs.As.", ln=1)
        self.set_x(10)
        self.cell(0, 4, "Cel.: 15-6048-5050 (Estudio)", ln=1)
        self.set_x(10)
        self.cell(0, 4, "www.estudiolorenzoasoc.com", ln=1)
  
        self.set_y(10)
        self.set_x(105)
        self.set_font("Arial", "B", 12)
        # La 'X' se mantiene con borde, pero ahora de color gris
        self.cell(10, 5, "X", border=1, align="C", ln=1)
        self.ln(1)
        self.set_x(60)
        self.cell(100, 5, "RECIBO DE COBRANZA", align="C", ln=1)
        self.set_x(60)
        self.set_font("Arial", "", 8)
        self.cell(100, 4, "DOCUMENTO NO VALIDO COMO FACTURA", align="C", ln=1)
        self.set_x(150)
        self.set_font("Arial", "B", 9)
        # El número de recibo también usa un borde con el nuevo color
        if self.recibo_id:
            self.cell(50, 4, f"N° {self.recibo_id}", border=1, ln=1, align="C")
        else:
            self.cell(50, 4, "N° SIN NÚMERO", border=1, ln=1, align="C")
        
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

def _fmt_money(n):
    try:
        return f"$ {float(n):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    except Exception:
        return str(n)

def crear_recibo_pdf(cliente_label: str, fecha_str: str, medios: list, descripciones: list, recibo_id: str = None, firmante: str = None):
    total = sum(d["monto"] for d in descripciones)
    pdf = _ReciboPDF()
    pdf.recibo_id = recibo_id
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Resto del código...
    pdf.set_y(52)
    pdf.set_x(150)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, f"Fecha: {fecha_str}", ln=1, align="R")

    pdf.ln(5)

    pdf.set_font("Arial", size=9)
    pdf.cell(15, 5, "Señor(es):")
    pdf.cell(100, 5, cliente_label, border="B", ln=1)
    pdf.cell(15, 5, "Domicilio:")
    pdf.cell(100, 5, "", border="B", ln=1)
    pdf.cell(15, 5, "Localidad:")
    pdf.cell(40, 5, "", border="B")
    pdf.cell(15, 5, "C.U.I.T.:")
    try:
        cuit = cliente_label.split('(')[-1].strip(')')
    except IndexError:
        cuit = ''
    pdf.cell(40, 5, cuit, border="B", ln=1)
    
    pdf.ln(5)

    pdf.multi_cell(0, 5, "Recibí(mos) la suma de pesos: ____________________________________________________________________")

    pdf.ln(5)

    # Definir un color de relleno más claro para los encabezados de tabla
    pdf.set_fill_color(20, 95, 145)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(110, 7, "Descripción", border=1, fill=True)
    pdf.cell(0, 7, "Monto", border=1, ln=1, align="R", fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=9)

    for d in descripciones:
        pdf.set_x(10)
        y_before_multicell = pdf.get_y()
        pdf.multi_cell(110, 5, d["descripcion"] or "-", border='L')
        y_after_multicell = pdf.get_y()
        h_desc = y_after_multicell - y_before_multicell
        
        pdf.set_xy(120, y_before_multicell)
        pdf.multi_cell(0, h_desc, _fmt_money(d["monto"]), border='R', align="R")
    
    # Las líneas de cierre también usan el nuevo color y grosor
    pdf.cell(110, 0, "", border="T", ln=1)
    pdf.cell(0, 0, "", border="T", ln=1)
    pdf.ln(5)

    pdf.set_fill_color(20, 95, 145)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(110, 7, "Medio de Cobro", border=1, fill=True)
    pdf.cell(0, 7, "Monto", border=1, ln=1, align="R", fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=9)
    
    for m in medios:
        pdf.set_x(10)
        pdf.cell(110, 5, str(m["cuenta"]), border='L')
        pdf.cell(0, 5, _fmt_money(m["monto"]), border='R', ln=1, align="R")
    
    pdf.cell(110, 0, "", border="T", ln=1)
    pdf.cell(0, 0, "", border="T", ln=1)
    pdf.ln(5)


    pdf.set_font("Arial", "B", 10)
    # Borde de la línea total
    pdf.cell(110, 7, "TOTAL", border="B", align="R")
    pdf.cell(0, 7, _fmt_money(total), border="B", ln=1, align="R")

    pdf.ln(10)

    pdf.set_font("Arial", size=9)
    pdf.cell(110, 5, "Firma: ______________________________")
    pdf.cell(0, 5, f"Aclaración: {firmante if firmante else '______________________________'}", ln=1)

    buffer = io.BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer.write(pdf_bytes)
    buffer.seek(0)

    return buffer.getvalue()


def guardar_log(cliente_label: str, fecha_str: str, descripcion: str, medios: list, path: str = "log_recibos.csv"):
    total = sum(m["monto"] for m in medios)
    filas = [{
        "fecha": fecha_str,
        "cliente": cliente_label,
        "descripcion": descripcion,
        "medio": m["cuenta"],
        "monto": float(m["monto"]),
        "total": float(total),
    } for m in medios]
    df = pd.DataFrame(filas)
    if os.path.exists(path):
        df.to_csv(path, mode="a", header=False, index=False)
    else:
        df.to_csv(path, index=False)

def _normalize_cobro_endpoint(endpoint: str) -> str:
    e = (endpoint or "").rstrip()
    if not e:
        return ""
    if e.endswith("/cobro") or e.endswith("/cobro/"):
        return e.rstrip("/") + "/0"
    return e

def enviar_cobro(jwt: str, payload: dict, endpoint: str = None):
    url = _normalize_cobro_endpoint(endpoint)
    if not url:
        return None
    r = requests.put(url, headers=_headers(jwt), json=payload, timeout=60)
    r.raise_for_status()
    return r.json()