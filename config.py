# config.py
# ⚠️ Completá estos valores antes de usar en producción
JWT = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpZGN1aXQiOiIxNjY1NjYiLCJpZHVzdWFyaW8iOjQ0NzY5LCJzZWVkIjoyOTEzOTY1OTY3MjY2ODV9.n3c84D5ulQut789UTNE3ruRbyeDyAPEUwP6xZWX061GiHUkR0XCU0b7eD5dSOSMlsaan3jOh9Bk00YQWTax3ow"

# Solo las cuentas que vas a usar como medios de cobro (nombre visible -> ID cuenta contable)
CUENTAS_COBRO = {
    "Caja Estudio": 78043610,
    "Caja Gabi": 236384363,
    "Caja Dani": 236384364,
    "Banco Provincia SH": 78043991,
    "Banco Provincia GL/DL ": 227197490,
    "Banco ICBC Adri": 236403092,
    # "Caja Estudio": 51384293,
    # "Caja Dani": 51384294,
    # "Caja Gabi": 52300001,
    # "Banco Provincia SH": 52300001,
    # "Banco Provincia Gabi/Dani": 52300001,
    # "Banco ICBC Adri": 52300001,
    # "Banco ICBC Hector": 52300001,
    # "Banco Provincia Dani": 52300001,
    # "Banco UALA Meli": 52300001,
    # "Mercado Pago Gabi": 52300001,
    # "Banco Fede": 52300001,
    # "Banco Mati": 52300001,


}

COBRO_ENDPOINT = "https://api.sos-contador.com/api-comunidad/cobro/" 

