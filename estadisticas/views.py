# Bloque de librerías estándar
import base64
import calendar
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from io import BytesIO
from collections import OrderedDict

from fontTools.misc.textTools import tostr
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

    period_ganancias = request.GET.get('month-ganancias')   # period = year-month por ejemplo 2024-04
    period_usuarios = request.GET.get('month-usuarios')
    period_autos = request.GET.get('month-autos')

    print(period_ganancias)
    print(period_usuarios)
    print(period_autos)

    if period_ganancias is None:
        now = datetime.now()
        period_ganancias = f"{now.year}-{now.month:02d}"

    if period_usuarios is None:
        now = datetime.now()
        period_usuarios = f"{now.year}-{now.month:02d}"

    if period_autos is None:
        now = datetime.now()
        period_autos = f"{now.year}-{now.month:02d}"

    grafico_ganancias = generar_reporte_ingresos(period_ganancias)
    grafico_usuarios_mas_activos = generar_reporte_usuarios_mas_activos(period_usuarios)
    grafico_autos_mas_alquilados = generar_reporte_autos_mas_alquilados(period_autos)
    return render(request,
                  'estadisticas/estadisticas_list.html',
                  {'grafico_ganancias': grafico_ganancias, 'grafico_usuarios': grafico_usuarios_mas_activos, 'grafico_vehiculos':grafico_autos_mas_alquilados}
                  )


def generar_reporte_ingresos(period):

    mes = obtener_fechas_del_mes(period)
    totales_dict = obtener_ganancias_por_mes(mes)

    valores = list(totales_dict.values())
    categorias = [fecha.strftime("%d") for fecha in totales_dict.keys()]

    if (all(valor == 0 for valor in valores)):
        return generar_grafico_vacio()
    else:
        return generar_grafico_funcion_puntos(
            categorias,
            valores,
            "Ganancias del: " + tostr(period),
            "Ganancias en AR$",
            "Fecha"
        )

def generar_reporte_usuarios_mas_activos(period):
    usuarios, cantidades = obtener_usuarios_con_mas_reservas(period)

    if (all(cantidades == 0 for cantidades in cantidades)):
        return generar_grafico_vacio()
    else:
        return generar_grafico_barras(
            usuarios,
            cantidades,
            "Usuarios con más reservas",
            "Cantidad de reservas",
            "Usuario"
        )

def generar_reporte_autos_mas_alquilados(period):
    autos, cantidades = obtener_autos_mas_alquilados(period)

    if (all(cantidades == 0 for cantidades in cantidades)):
        return generar_grafico_vacio()
    else:
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

def generar_grafico_vacio():
    fig = Figure()
    ax = fig.subplots()

    ax.axis("off")
    ax.text(0.5, 0.5, 'No existen datos para el periodo seleccionado',
        horizontalalignment='center',
        verticalalignment='center',
        fontsize=16)

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

def obtener_fechas_del_mes(periodo):
    # Parsear el string "YYYY-MM"
    año, mes = map(int, periodo.split("-"))

    # Obtener cuántos días tiene ese mes
    _, cantidad_dias = calendar.monthrange(año, mes)

    # Crear la lista de fechas
    return [date(año, mes, día) for día in range(1, cantidad_dias + 1)]

def obtener_ganancias_por_mes(mes):
    fechas = mes
    resultados = OrderedDict()

    print(fechas)
    for fecha in sorted(fechas):
        inicio = datetime.combine(fecha, time.min)
        fin = inicio + timedelta(days=1)

        total = Reserva.objects.filter(fecha_creacion__gte=inicio, fecha_creacion__lt=fin).aggregate(total=Sum('monto_pago'))['total'] or 0

        resultados[fecha] = total

    print(resultados)

    return resultados


def obtener_usuarios_con_mas_reservas(period):
    año, mes = map(int, period.split("-"))
    _, cantidad_dias = calendar.monthrange(año, mes)

    inicio = datetime(año, mes, 1)
    fin = datetime(año, mes, cantidad_dias, 23, 59, 59)

    resultados = (
        Reserva.objects
        .filter(fecha_creacion__gte=inicio, fecha_creacion__lte=fin)
        .values('usuario__username')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )

    usuarios = [r['usuario__username'] for r in resultados]
    cantidades = [r['total'] for r in resultados]

    return usuarios, cantidades

def obtener_autos_mas_alquilados(period):
    año, mes = map(int, period.split("-"))
    _, cantidad_dias = calendar.monthrange(año, mes)

    inicio = datetime(año, mes, 1)
    fin = datetime(año, mes, cantidad_dias, 23, 59, 59)

    resultados = (
        Reserva.objects
        .filter(fecha_creacion__gte=inicio, fecha_creacion__lte=fin)
        .values('vehiculo__modelo')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
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