import yt_dlp
import pygame
import tkinter as tk
from tkinter import ttk
from mutagen.mp3 import MP3
from PIL import Image, ImageTk
import threading
import os
import time
import requests

# Inicializar Pygame
pygame.mixer.init()

# Variables globales
lista_canciones = []
indice_actual = 0
reproduciendo = False
imagen_miniatura = None
duracion_total = 0
volumen_actual = 0.5
# Función para descargar audio y miniatura
def descargar_audio(url):
    progreso.set("Iniciando descarga...")

    def progreso_descarga(d):
        if d['status'] == 'downloading':
            porcentaje = d['_percent_str']
            progreso.set(f"Descargando... {porcentaje}")
        elif d['status'] == 'finished':
            progreso.set("Descarga completada.")
            cargar_lista_canciones()

    opciones = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'musica/%(title)s.%(ext)s',
        'progress_hooks': [progreso_descarga],
    }

    with yt_dlp.YoutubeDL(opciones) as ydl:
        info = ydl.extract_info(url, download=True)
        descargar_miniatura(info['thumbnail'])

# Función para descargar la miniatura
def descargar_miniatura(url):
    response = requests.get(url)
    with open("miniatura.jpg", "wb") as file:
        file.write(response.content)
    mostrar_miniatura()

# Función para mostrar la miniatura
def mostrar_miniatura():
    global imagen_miniatura
    try:
        imagen = Image.open("miniatura.jpg").resize((100, 100))
        imagen_miniatura = ImageTk.PhotoImage(imagen)
        etiqueta_miniatura.config(image=imagen_miniatura)
    except Exception as e:
        print(f"Error al mostrar la miniatura: {e}")

# Función para cargar la lista de canciones
def cargar_lista_canciones():
    lista_canciones.clear()
    listabox_canciones.delete(0, tk.END)
    carpeta = 'musica'

    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    archivos = [f for f in os.listdir(carpeta) if f.endswith('.mp3')]
    for archivo in archivos:
        ruta = os.path.join(carpeta, archivo)
        audio = MP3(ruta)
        duracion = time.strftime('%M:%S', time.gmtime(audio.info.length))
        lista_canciones.append({'nombre': archivo, 'ruta': ruta, 'duracion': duracion})
        listabox_canciones.insert(tk.END, f"{archivo} ({duracion})")

# Función para reproducir música
def reproducir_musica():
    global reproduciendo, indice_actual, duracion_total
    if lista_canciones:
        archivo = lista_canciones[indice_actual]['ruta']
        pygame.mixer.music.load(archivo)
        pygame.mixer.music.play()
        reproduciendo = True
        duracion_total = MP3(archivo).info.length
        actualizar_estado()
        actualizar_seleccion_lista()

# Función para pausar o reanudar
def pausar_musica():
    global reproduciendo
    if reproduciendo:
        pygame.mixer.music.pause()
        reproduciendo = False
        estado.set("Pausado")
    else:
        pygame.mixer.music.unpause()
        reproduciendo = True
        estado.set("Reproduciendo")

# Función para detener la música
def detener_musica():
    pygame.mixer.music.stop()
    estado.set("Detenido")

# Función para adelantar a la siguiente canción
def siguiente_cancion():
    global indice_actual
    indice_actual = (indice_actual + 1) % len(lista_canciones)
    reproducir_musica()

# Función para retroceder a la canción anterior
def anterior_cancion():
    global indice_actual
    indice_actual = (indice_actual - 1) % len(lista_canciones)
    reproducir_musica()

# Función para actualizar el estado y la barra de progreso
def actualizar_estado():
    if reproduciendo:
        tiempo_actual = pygame.mixer.music.get_pos() / 1000
        progreso_reproduccion.set(tiempo_actual / duracion_total * 100)
        estado.set(f"{time.strftime('%M:%S', time.gmtime(tiempo_actual))} / "
                   f"{time.strftime('%M:%S', time.gmtime(duracion_total))}")
        ventana.after(500, actualizar_estado)

# Función para manejar la selección de canción
def seleccionar_cancion(event):
    global indice_actual
    indice_actual = listabox_canciones.curselection()[0]
    reproducir_musica()

# Función para actualizar la selección en la lista
def actualizar_seleccion_lista():
    listabox_canciones.selection_clear(0, tk.END)
    listabox_canciones.selection_set(indice_actual)
    listabox_canciones.activate(indice_actual)

# Función para ajustar el volumen
def ajustar_volumen(valor):
    global volumen_actual
    volumen_actual = float(valor)
    pygame.mixer.music.set_volume(volumen_actual)
# Función para controlar la barra de progreso
def ajustar_tiempo(event):
    if reproduciendo:
        nuevo_tiempo = progreso_reproduccion.get() / 100 * duracion_total
        pygame.mixer.music.stop()
        pygame.mixer.music.play(start=nuevo_tiempo)

# Función para iniciar la descarga en un hilo separado
def iniciar_descarga():
    url = entrada_url.get()
    threading.Thread(target=descargar_audio, args=(url,)).start()

# Interfaz gráfica
ventana = tk.Tk()
ventana.title("Reproductor de Música")
ventana.geometry("600x600")

# Variable para el progreso de la descarga
progreso = tk.StringVar()
progreso.set("Esperando...")

# Etiqueta para mostrar el progreso de la descarga
etiqueta_progreso = tk.Label(ventana, textvariable=progreso)
etiqueta_progreso.pack(pady=5)

# Entrada URL
entrada_url = tk.Entry(ventana, width=50)
entrada_url.pack(pady=10)

# Miniatura
etiqueta_miniatura = tk.Label(ventana)
etiqueta_miniatura.pack(pady=10)

# Control de volumen
volumen_slider = ttk.Scale(ventana, from_=0, to=1, orient=tk.HORIZONTAL, length=300, command=ajustar_volumen)
volumen_slider.set(volumen_actual)
volumen_slider.pack(pady=10)

# Botones de control
frame_botones = tk.Frame(ventana)
frame_botones.pack(pady=10)

boton_descargar = tk.Button(frame_botones, text="Descargar", command=iniciar_descarga)
boton_descargar.grid(row=0, column=0, padx=10)

boton_play = tk.Button(frame_botones, text="Play", command=reproducir_musica)
boton_play.grid(row=0, column=1, padx=10)

boton_pausa = tk.Button(frame_botones, text="Pausar/Reanudar", command=pausar_musica)
boton_pausa.grid(row=0, column=2, padx=10)

boton_siguiente = tk.Button(frame_botones, text="Siguiente", command=siguiente_cancion)
boton_siguiente.grid(row=0, column=3, padx=10)

boton_anterior = tk.Button(frame_botones, text="Anterior", command=anterior_cancion)
boton_anterior.grid(row=0, column=4, padx=10)

# Lista de canciones
listabox_canciones = tk.Listbox(ventana, width=60, height=10)
listabox_canciones.pack(pady=10)
listabox_canciones.bind("<<ListboxSelect>>", seleccionar_cancion)

# Barra de progreso
progreso_reproduccion = tk.DoubleVar()
barra_progreso = ttk.Scale(ventana, variable=progreso_reproduccion, from_=0, to=100, orient=tk.HORIZONTAL, length=500)
barra_progreso.pack(pady=10)
barra_progreso.bind("<ButtonRelease-1>", ajustar_tiempo)

# Estado de la reproducción
estado = tk.StringVar()
estado.set("Detenido")
etiqueta_estado = tk.Label(ventana, textvariable=estado)
etiqueta_estado.pack(pady=10)

cargar_lista_canciones()

ventana.mainloop()
