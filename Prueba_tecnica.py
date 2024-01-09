import os
import time
import zipfile
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# -------------------------------------------------- Webscraping para descargar el archivo solicitado --------------------------------------------------


# Configuro el driver se selenium
driver = webdriver.Chrome()

# Abro la web
url = 'https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/home'
driver.get(url)

try:
    # Espera un máximo de 6 segundos para encontrar el botón 'Go' y luego haz clic en él
    WebDriverWait(driver, 6).until(
        EC.element_to_be_clickable((By.ID, 'home-dwnload-go-btn'))
    ).click()

    # Espera un máximo de 4 segundos para encontrar y hacer clic en el primer dropdown
    dropdown = WebDriverWait(driver, 4).until(
        EC.element_to_be_clickable((By.ID, 'dwnnibrs-download-select'))
    )
    dropdown.click()

    # Selecciona la opción 'Victims' dentro del primer dropdown
    option_victims = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, "//nb-option[contains(text(), 'Victims')]"))
    )
    option_victims.click()

    # El ano 2022 viene seleccionado por defecto, por esa razon, no se lo selecciona por medio de funciones.

    # Espera un máximo de 3 segundos para encontrar y hacer clic en el segundo dropdown
    dropdown_2 = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, "//nb-select[@id='dwnnibrsloc-select']"))
    )
    dropdown_2.click()

    # Encuentra y haz clic en la opción "Florida" en el segundo menú desplegable
    option_florida = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, "//nb-option[contains(text(), 'Florida')]"))
    )
    option_florida.click()

    # Espera un máximo de 3 segundos para encontrar y hacer clic en el botón de descarga
    WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.ID, 'nibrs-download-button'))
    ).click()

    time.sleep(5)  # Espera 5 segundos para permitir la descarga
    
    print('Se descargo el archivo')
    
except Exception as e:
    print("No se pudo realizar la selección:", e)

# Cierra el navegador cuando hayas terminado
driver.quit()


# -------------------------------------------------- Busqueda del archivo descargado --------------------------------------------------


# Función para obtener las carpetas de descargas según el sistema operativo
def obtener_carpetas_descargas():
    sistema_operativo = os.name
    if sistema_operativo == 'posix':  # Sistema tipo Unix (Linux, macOS, etc.)
        return [os.path.expanduser('~/Downloads')]
    elif sistema_operativo == 'nt':  # Windows
        return [os.path.join(os.environ['USERPROFILE'], 'Downloads')]
    else:
        return []

# Función para buscar el archivo en las carpetas de descargas
def buscar_archivo_en_carpetas(nombre_archivo, carpetas):
    archivos_encontrados = []
    for carpeta in carpetas:
        for ruta_carpeta, _, archivos in os.walk(carpeta):
            if nombre_archivo in archivos:
                archivos_encontrados.append(os.path.join(ruta_carpeta, nombre_archivo))
    return archivos_encontrados

# Nombre del archivo que estoy buscando
nombre_archivo = 'victims.zip'

# Obtener las carpetas de descargas según el sistema operativo
carpetas_descargas = obtener_carpetas_descargas()

# Buscar el archivo en las carpetas de descargas
archivos_encontrados = buscar_archivo_en_carpetas(nombre_archivo, carpetas_descargas)


# -------------------------------------------------- Descompresion del archivo solicitado --------------------------------------------------


# Abre el archivo ZIP en modo lectura
with zipfile.ZipFile(archivos_encontrados[0], 'r') as archivo_zip:
    
    lista_contenidos = archivo_zip.namelist()
    # Extraer archivo
    archivo_zip.extract('Victims_Age_by_Offense_Category_2022.xlsx')
    
print('Se descomprimio el archivo')


# -------------------------------------------------- ETL (extraccion, transformacion y carga) --------------------------------------------------



# Lee el archivo Victims_Age_by_Offense_Category_2022.xlsx y lo almacena en un DataFrame llamado 'victims'
victims = pd.read_excel('Victims_Age_by_Offense_Category_2022.xlsx')

# Elimina las dos primeras filas del DataFrame 'victims'
victims.drop(victims.index[:2], inplace=True)

# Elimina la última fila del DataFrame 'victims'
victims.drop(victims.index[-1], inplace=True)

# Selecciona la tercera fila del DataFrame 'victims' y la almacena en 'indice_age'
indice_age = victims.iloc[1].values[2:]

# Convierte 'indice_age' en una lista y agrega dos elementos al principio de la lista
indice_age = [x for x in indice_age]
indice_age.insert(0,'Total_Victims')
indice_age.insert(0,'Offense Category')

# Reemplaza los saltos de línea en la lista 'indice_age' si el elemento es una cadena de texto
indice_age = [columna.replace('\n', ' ') if isinstance(columna, str) else columna for columna in indice_age]

# Filtra el DataFrame 'victims' donde la columna 'Victims' es igual a 'Crimes Against Property' y crea una copia
Crimes_Against_Property = victims.loc[victims['Victims'] == 'Crimes Against Property'].copy()

# Renombra las columnas del DataFrame 'Crimes_Against_Property' con los elementos de 'indice_age'
Crimes_Against_Property.columns = indice_age[0:len(Crimes_Against_Property.columns)]

# Elimina la columna 'Total_Victims' del DataFrame 'Crimes_Against_Property'
Crimes_Against_Property.drop(columns=['Total_Victims'], inplace=True)

# Transpone el DataFrame 'Crimes_Against_Property'
Crimes_Against_Property = Crimes_Against_Property.transpose()

# Elimina la primera fila del DataFrame 'Crimes_Against_Property'
Crimes_Against_Property.drop(Crimes_Against_Property.index[0], inplace=True)

# Renombra las columnas del DataFrame 'Crimes_Against_Property' como 'Crimes Against Property'
Crimes_Against_Property.columns = ['Crimes Against Property']

# Renombra el índice del DataFrame 'Crimes_Against_Property' como 'Age'
Crimes_Against_Property = Crimes_Against_Property.rename_axis('Age')

# Guarda el DataFrame 'Crimes_Against_Property' como un archivo CSV llamado 'Crimes_Against_Property.csv'
Crimes_Against_Property.to_csv('Crimes_Against_Property.csv')

if os.path.exists('Victims_Age_by_Offense_Category_2022.xlsx'):
    os.remove('Victims_Age_by_Offense_Category_2022.xlsx')

print('El archivo resultante tiene el nombre de "Crimes_Against_Property.csv"')


# -------------------------------------------------- Fin del proceso --------------------------------------------------