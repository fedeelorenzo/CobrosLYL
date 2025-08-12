# config.py
import streamlit as st

# Lee las credenciales del archivo secrets.toml
JWT = st.secrets["JWT"]

# Solo las cuentas que vas a usar como medios de cobro (nombre visible -> ID cuenta contable)
CUENTAS_COBRO = {
    "Caja Estudio": 78043610,
    "Caja Gabi": 236384363,
    "Caja Dani": 236384364,
    "Banco Provincia SH": 78043991,
    "Banco Provincia GL/DL ": 227197490,
    "Banco ICBC Adri": 236403092,
    "Retencion Impuesto a las Ganancias": 78043603,
    # "Banco ICBC Hector": 52300001,
    # "Banco Provincia Dani": 52300001,
    # "Banco UALA Meli": 52300001,
    # "Mercado Pago Gabi": 52300001,
    # "Banco Fede": 52300001,
    # "Banco Mati": 52300001,


}

COBRO_ENDPOINT = "https://api.sos-contador.com/api-comunidad/cobro/" 

