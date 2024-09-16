# Importamos los módulos necesarios de Flask y otros módulos de Python
from flask import Flask, render_template, request, redirect, url_for  # Importar componentes de Flask para la aplicación web
import os  # Módulo para interactuar con el sistema de archivos
import re  # Módulo para trabajar con expresiones regulares
import requests  # Módulo para hacer solicitudes HTTP
from datetime import datetime, timedelta  # Módulos para manejar fechas y tiempos
from evtx import Evtx  # Importar módulo Evtx para leer archivos de registro de eventos de Windows (.evtx)

# Inicializamos la aplicación Flask
app = Flask(__name__)  # Crear una instancia de la aplicación Flask
app = Flask(__name__, static_url_path='/static')  # Especificar la ruta para archivos estáticos (opcional y redundante aquí)

# Función para analizar los logs del sistema
def analizar_logs():
    directorio_logs = 'C:\Windows\System32\winevt\Logs'  # Ruta al directorio de logs del sistema
    patron_inicio_sesion = r'4625</EventID>'  # Patrón para buscar eventos de ID 4625 (intentos fallidos de inicio de sesión)
    inicios_sesion = []  # Lista para almacenar los inicios de sesión encontrados
    limite_tiempo = datetime.now() - timedelta(days=3)  # Definir un límite de tiempo de 3 días atrás desde ahora

    # Verificar si el directorio de logs existe
    if os.path.exists(directorio_logs):
        # Iterar sobre los archivos en el directorio de logs
        for archivo_log in os.listdir(directorio_logs):
            # Considerar solo archivos .evtx y que contengan 'Security' en su nombre
            if archivo_log.endswith('.evtx') and 'Security' in archivo_log:
                ruta_archivo = os.path.join(directorio_logs, archivo_log)  # Obtener la ruta completa del archivo
                with Evtx(ruta_archivo) as log:  # Abrir el archivo de log para leer
                    print("Se está leyendo el fichero " + archivo_log)  # Imprimir un mensaje indicando el archivo que se está leyendo
                    # Iterar sobre los registros en el archivo de log
                    for record in log.records():
                        xml = record.xml()  # Obtener el XML del registro
                        if re.search(patron_inicio_sesion, xml, re.IGNORECASE):  # Buscar el patrón de inicio de sesión en el XML
                            print(xml)  # Imprimir el XML si se encuentra el patrón
                            fecha_log = obtener_fecha_log(xml)  # Obtener la fecha del inicio de sesión
                            print(fecha_log)  # Imprimir la fecha del log
                            # Verificar si la fecha es válida y está dentro del límite de tiempo
                            if fecha_log and fecha_log > limite_tiempo:
                                inicios_sesion.append({
                                    'Archivo': archivo_log,
                                    'Fecha': fecha_log
                                })  # Agregar el inicio de sesión a la lista

    return inicios_sesion  # Devolver la lista de inicios de sesión encontrados

# Función para extraer la fecha de un registro de log en formato XML
def obtener_fecha_log(xml):
    patron_fecha = r'<TimeCreated SystemTime=\"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'  # Patrón para extraer la fecha del XML
    match_fecha = re.search(patron_fecha, xml)  # Buscar el patrón en el XML
    if match_fecha:
        fecha_str = match_fecha.group(1)  # Extraer la cadena de fecha
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')  # Convertir la cadena a un objeto datetime
        return fecha  # Devolver la fecha
    return None  # Devolver None si no se encontró la fecha

# Función para enviar un mensaje con los resultados a un bot de Telegram
def enviar_mensaje_resultado(nombre, inicios_sesion):
    bot_token = '7106132626:AAEuD2z97DdLMZuLMfk9KxdX7-K3J5K3sw8'  # Token del bot de Telegram
    chat_id = '-1002030809168'  # ID del chat de Telegram

    if inicios_sesion:
        mensaje = f"¡Hola {nombre}!\nSe encontraron errores en los siguientes inicios de sesión de los últimos 3 días:\n\n"
        # Construir el mensaje con los inicios de sesión encontrados
        for inicio_sesion in inicios_sesion:
            mensaje += f"Archivo: {inicio_sesion['Archivo']}, Fecha: {inicio_sesion['Fecha']}\n"
    else:
        mensaje = f"¡Hola {nombre}!\nNo se encontraron inicios de sesión en los últimos 3 días."

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'  # URL de la API de Telegram
    parametros = {'chat_id': chat_id, 'text': mensaje}  # Parámetros de la solicitud
    respuesta = requests.post(url, params=parametros)  # Hacer la solicitud POST a la API de Telegram

    if not respuesta.ok:
        print("Error al enviar el mensaje al bot de Telegram:", respuesta.text)  # Imprimir un mensaje si hay un error

# Ruta principal de la aplicación Flask
@app.route('/')
def index():
    return render_template('index.html')  # Renderizar la plantilla index.html

# Ruta para analizar los logs cuando se recibe una solicitud POST
@app.route('/analizar_logs', methods=['POST'])
def analizar_logs_flask():
    nombre = request.form['nombre']  # Obtener el nombre del formulario
    inicios_sesion = analizar_logs()  # Llamar a la función para analizar los logs
    enviar_mensaje_resultado(nombre, inicios_sesion)  # Enviar los resultados al bot de Telegram
    return redirect(url_for('resultado'))  # Redirigir a la página de resultados

# Ruta para mostrar los resultados
@app.route('/resultado')
def resultado():
    return render_template('resultado.html')  # Renderizar la plantilla resultado.html

# Ejecutar la aplicación Flask en modo debug
if __name__ == "__main__":
    app.run(debug=True)  # Ejecutar la aplicación Flask
