from django.shortcuts import render

# Bloque de librerías estándar
import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import BytesIO

# Bloque de librerías de terceros
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

def ver_estadisticas(request):

    return render(request, 'estadisticas/estadisticas_list.html')

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


def generar_grafico_torta(categorias, valores, titulo_grafico):
    """Genera un grafico del tipo grafico de torta

    Parametros
    ----------
    categorias : list of str
        Son las categorias sobre las que se quiere generar el grafico
    valores : list of int
        Son los valores correspondientes a las categorias
    titulo_grafico : str
        Es el titulo que se vera en el encabezado del grafico

    Retorno
    -------
    data : str
        Es la imagen codificada en base64
    """
    fig = Figure()
    ax = fig.subplots()
    ax.pie(
        valores,
        autopct='%1.1f%%'
    )

    ax.set_title(titulo_grafico)
    ax.legend(categorias, loc="center right", bbox_to_anchor=(0.85, 0.37, 0.5, 1))

    # Guardamos en un buffer temporal
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return data