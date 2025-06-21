# Bloque de librerías estándar
import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import BytesIO
from collections import OrderedDict

# Bloque de librerías de terceros
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from django.shortcuts import render
from django.db.models import Sum
from django.db.models import Count

# Bloque de librerias locales
from pagos.models import Pago
from reservas.models import Reserva

def ver_estadisticas(request):
    grafico_ganancias = generar_reporte_ingresos()
    grafico_usuarios_mas_activos = generar_reporte_usuarios_mas_activos()
    grafico_autos_mas_alquilados = generar_reporte_autos_mas_alquilados()
    return render(request,
                  'estadisticas/estadisticas_list.html',
                  {'grafico_ganancias': grafico_ganancias, 'grafico_usuarios': grafico_usuarios_mas_activos, 'grafico_vehiculos':grafico_autos_mas_alquilados}
                  )


def generar_reporte_ingresos():
    meses = obtener_ultimos_meses(12)
    totales_dict = obtener_ganancias_por_mes(meses)

    categorias = list(totales_dict.keys())
    valores = list(totales_dict.values())

    return generar_grafico_barras(
        categorias,
        valores,
        "Ganancias de últimos 12 meses",
        "Ganancias en AR$",
        "Mes"
    )

def generar_reporte_usuarios_mas_activos():
    usuarios, cantidades = obtener_usuarios_con_mas_reservas()

    return generar_grafico_barras(
        usuarios,
        cantidades,
        "Usuarios con más reservas",
        "Cantidad de reservas",
        "Usuario"
    )

def generar_reporte_autos_mas_alquilados():
    autos, cantidades = obtener_autos_mas_alquilados()

    return generar_grafico_barras(
        autos,
        cantidades,
        "Vehiculos mas alquilados",
        "Cantidad de alquileres",
        "Modelo del vehiculo"
    )

def generar_grafico_barras(categorias, valores, titulo_grafico, titulo_eje_y, titulo_eje_x):
    """Genera un grafico del tipo grafico de barras

    Parametros
    ----------
    categorias : list of str
        Son las categorias sobre las que se quiere generar el grafico
    valores : list of int
        Son los valores correspondientes a las categorias
    titulo_grafico : str
        Es el titulo que se vera en el encabezado del grafico
    titulo_eje_y : str
        Es el subtitulo que dara informacion acerca de que representan los valores de y
    titulo_eje_x : str
        Es el subtitulo que dara informacion acerca de que representan las categorias

    Retorno
    -------
    data : str
        Es la imagen codificada en base64
    """
    fig = Figure()
    ax = fig.subplots()
    ax.bar(categorias, valores)

    # Seteamos unicamente valores enteros y positivos para el eje Y
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(bottom=0)

    # Agregamos titulos y etiquetas
    ax.set_title(titulo_grafico)
    ax.set_ylabel(titulo_eje_y)
    ax.set_xlabel(titulo_eje_x)

    ax.set_xticklabels(categorias, rotation=45, ha="right")
    fig.tight_layout()

    # Guardamos en un buffer temporal
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return data


def generar_grafico_funcion_puntos(categorias, valores, titulo_grafico, titulo_eje_y, titulo_eje_x):
    """Genera un grafico del tipo funcion

    Parametros
    ----------
    categorias : list of str
        Son las categorias sobre las que se quiere generar el grafico
    valores : list of int
        Son los valores correspondientes a las categorias
    titulo_grafico : str
        Es el titulo que se vera en el encabezado del grafico
    titulo_eje_y : str
        Es el subtitulo que dara informacion acerca de que representan los valores de y
    titulo_eje_x : str
        Es el subtitulo que dara informacion acerca de que representan las categorias

    Retorno
    -------
    data : str
        Es la imagen codificada en base64
    """
    fig = Figure()
    ax = fig.subplots()
    ax.plot(categorias, valores, marker='o', linestyle='-', color='b')

    # En caso de que no hayan valores para mostrar, se toma como limite inferior el 0 y el limite superior el 1000
    if all(valor <= 0 for valor in valores):
        ax.set_ylim(bottom=0, top=1000)

    # Agregamos titulos y etiquetas
    ax.set_title(titulo_grafico)
    ax.set_ylabel(titulo_eje_y)
    ax.set_xlabel(titulo_eje_x)

    ax.set_xticklabels(categorias, rotation=45, ha="right")
    fig.tight_layout()

    # Guardamos en un buffer temporal
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return data

def obtener_ultimos_meses(cant_meses):
    """
    Devuelve una lista con los ultimos "cant_meses" en formato Datetime.

    Parametros
    ----------
    cant_meses: int
        Es la cantidad de meses que se quiere obtener a partir de la fecha actual.

    Retorno
    -------
    meses: list of Datetime
        Es la lista que contiene los ultimos "cant_meses" solicitados a partir de la fecha actual
    """
    meses = []

    for i in range(cant_meses):
        fecha = datetime.now() - relativedelta(months=i)
        meses.append(fecha)

    return meses

def obtener_ganancias_por_mes(cant_meses):
    meses = cant_meses
    resultados = OrderedDict()

    for fecha in sorted(meses):
        inicio_mes = fecha.replace(day=1)
        fin_mes = (inicio_mes + relativedelta(months=1)) - relativedelta(days=1)

        total = Pago.objects.filter(
            fecha_pago__date__gte=inicio_mes.date(),
            fecha_pago__date__lte=fin_mes.date()
        ).aggregate(total=Sum('monto'))['total'] or 0

        resultados[inicio_mes.strftime("%Y-%m")] = total

    return resultados


def obtener_usuarios_con_mas_reservas(top_n=10):
    resultados = (
        Reserva.objects.values('usuario__username')
        .annotate(total=Count('id'))
        .order_by('-total')[:top_n]
    )

    usuarios = [r['usuario__username'] for r in resultados]
    cantidades = [r['total'] for r in resultados]

    return usuarios, cantidades

def obtener_autos_mas_alquilados(top_n=10):
    resultados = (
        Reserva.objects.values('vehiculo__modelo')
        .annotate(total=Count('id'))
        .order_by('-total')[:top_n]
    )

    modelos = [r['vehiculo__modelo'] for r in resultados]
    cantidades = [r['total'] for r in resultados]

    return modelos, cantidades

def parse_datetime_to_mm_yyyy(lista_de_meses):
    """
    Parsea una lista de meses de tipo Datetime a string

    Parametros
    ----------
    lista_de_meses: list of Datetime
        Es la lista de meses en formato Datetime

    Retorno
    -------
    lista_de_meses: list of str
        Es la lista de meses en formato mm-yyyy
    """
    lista_de_meses = [fecha.strftime("%m-%Y") for fecha in lista_de_meses]

    return lista_de_meses