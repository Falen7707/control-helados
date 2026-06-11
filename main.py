from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import RedirectResponse
import sqlite3
from fastapi.staticfiles import StaticFiles
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT producto,
               cantidad,
               precio,
               cantidad * precio AS total,
               fecha
        FROM ventas
        WHERE date(fecha) = date('now')
        ORDER BY id DESC
    """)

    ventas = cursor.fetchall()

    cursor.execute("""
        SELECT SUM(cantidad * precio)
        FROM ventas
        WHERE date(fecha) = date('now')
    """)

    resultado = cursor.fetchone()
    ganancia_total = resultado[0] if resultado and resultado[0] else 0

    cursor.execute("""
        SELECT SUM(cantidad)
        FROM ventas
        WHERE date(fecha) = date('now')
    """)

    resultado = cursor.fetchone()
    helados_vendidos = resultado[0] if resultado and resultado[0] else 0

    comision = ganancia_total * PORCENTAJE_COMISION / 100

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "ventas": ventas,
            "ganancia_total": ganancia_total,
            "comision": comision,
            "helados_vendidos": helados_vendidos,
            "fecha_actual": fecha_actual
        }
    )

PRECIOS = {
    "Barquillon": 1.83,
    "Concha de Coco": 2.30,
    "Tetas": 0.94
}
PORCENTAJE_COMISION = 35

@app.get("/historial", response_class=HTMLResponse)
def historial(request: Request):

    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            date(fecha) as dia,
            SUM(cantidad * precio) as total
        FROM ventas
        GROUP BY date(fecha)
        ORDER BY dia DESC
    """)

    historial = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="historial.html",
        context={
            "historial": historial
        }
    )

@app.post("/venta")
def registrar_venta(
    producto: str = Form(...),
    cantidad: int = Form(...)
):

    precio = PRECIOS[producto]
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    cursor.execute(
    """
    INSERT INTO ventas
    (producto, cantidad, precio, fecha)
    VALUES (?, ?, ?, ?)
    """,
    (producto, cantidad, precio, fecha)
)

    conn.commit()
    conn.close()

    return RedirectResponse(
        url="/",
        status_code=303
    )

@app.get("/resumen")
def resumen():

    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            SUM(cantidad * precio)
        FROM ventas
    """)

    total = cursor.fetchone()[0]

    conn.close()

    return {
        "ganancia_total": total
    }