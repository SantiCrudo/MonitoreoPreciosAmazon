import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta # Se usa timedelta, pero está bien mantenerlo
import os
import re 
import smtplib
from email.message import EmailMessage
import dotenv

# ====================================================================
# --- CORRECCIÓN 1: LIMPIEZA DE IMPORTS Y CONFIGURACIÓN ---
# ====================================================================
dotenv.load_dotenv()
# Los nombres de las variables se cargan desde .env
EMAIL_USER = os.getenv('EMAIL_USER') 
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

UMBRAL_BAJADA = 0.05
# Se eliminan las líneas redundantes: EMAIL_USER = EMAIL_USER

# ----------------- FASE 1: PRODUCTOS Y CONFIGURACIÓN -----------------

productos = {
    "RTX 4070 Ti": "https://www.amazon.com/-/es/GIGABYTE-ventiladores-WINDFORCE-GV-N407TGAMING-OC-12GD/dp/B0BRR2R8HH/ref=sr_1_3?__mk_es_US=%C3%85M%C3%85%C5%BD%C3%95%C3%91&sr=8-3",
    "Ryzen 7 9800X3D": "https://www.amazon.com/-/es/AMD-Procesador-escritorio-9800X3D-n%C3%BAcleos/dp/B0DKFMSMYK/ref=sr_1_1?__mk_es_US=%C3%85M%C3%85%C5%BD%C3%95%C3%91&sr=8-1",
    "M.2 1TB": "https://www.amazon.com/computadoras-port%C3%A1tiles-escritorio-consolas-recuperaci%C3%B3n/dp/B0DC8VPSHV/ref=sr_1_2_sspa?__mk_es_US=%C3%85M%C3%85%C5%BD%C3%95%C3%91&sr=8-2-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9atf"
}

HEADERS = ({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Connection': 'keep-alive',
})

# ----------------- FASE 2: EXTRACCIÓN MEJORADA -----------------

def extraer_precio(url):
    try:
        respuesta = requests.get(url, headers=HEADERS)
        respuesta.raise_for_status()

        sopa = BeautifulSoup(respuesta.content, 'html.parser')
        
        # 1. Buscar el principal bloque que contiene el precio (más estable)
        price_block = sopa.find('div', id='corePriceDisplay_desktop_feature_div')
        precio_elemento = None
        
        if price_block:
            # 2. Buscar dentro del bloque principal el span que contiene el precio (mejor opción: a-offscreen)
            precio_elemento = price_block.find('span', {'class': 'a-price-whole'})
        
        # 3. Respaldo: Si no se encontró en el bloque, buscarlo en todo el HTML
        if not precio_elemento:
             precio_elemento = sopa.find('span', {'class': 'a-offscreen'})


        if precio_elemento:
            precio_texto = precio_elemento.text.strip()
            
            # --- LIMPIEZA ROBUSTA ---
            # ⚠️ Importar 're' dentro de la función no es necesario si ya se importa globalmente,
            # pero no causa error. Se deja el re.sub que ya funciona.
            precio_limpio = re.sub(r'[A-Za-z$€]', '', precio_texto).strip()
            precio_limpio = precio_limpio.replace(',', '')
            precio_limpio = precio_limpio.strip()
            
            return float(precio_limpio)
        else:
            return None
            
    except requests.exceptions.HTTPError:
        return None
    except ValueError:
        return None
    except Exception:
        return None


# ----------------- FASE 3: ALMACENAMIENTO EN CSV -----------------

def guardar_datos_csv(datos_nuevos, nombre_archivo='historial_precios.csv'):
    """Guarda o añade nuevos datos al archivo CSV."""
    
    df_nuevo = pd.DataFrame(datos_nuevos)
    
    if os.path.exists(nombre_archivo):
        df_existente = pd.read_csv(nombre_archivo)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo

    df_final.to_csv(nombre_archivo, index=False)
    print(f"\n✅ Datos guardados exitosamente en {nombre_archivo}. Total de registros: {len(df_final)}")


# ====================================================================
# --- CORRECCIÓN 2: DEFINICIÓN DE FUNCIONES DE FASE 4 (DEBEN IR AQUÍ) ---
# ====================================================================

# ----------------- FASE 4: FUNCIÓN DE ENVÍO DE EMAIL -----------------

def enviar_email_alerta(asunto, cuerpo_mensaje):
    """Configura y envía el email de alerta."""
    
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print("Error: EMAIL_USER o EMAIL_PASSWORD no están configurados en .env.")
        return

    msg = EmailMessage()
    msg.set_content(cuerpo_mensaje)
    msg['Subject'] = asunto
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER 

    print(f"Intentando enviar email a {EMAIL_USER}...")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("✅ Alerta enviada por email exitosamente.")
        
    except Exception as e:
        print(f"❌ ERROR al enviar email. Verifica tus credenciales (App Password): {e}")


# ----------------- FASE 4: FUNCIÓN DE ANÁLISIS -----------------

def analizar_y_alertar(df_historial, df_nuevos_datos):
    """Analiza los nuevos precios contra los precios históricos y envía alertas."""
    
    print("\nIniciando análisis de variación...")
    alertas_enviadas = 0

    for index, fila_nueva in df_nuevos_datos.iterrows():
        componente = fila_nueva['Componente']
        precio_actual = fila_nueva['Precio']

        # 1. Filtrar el historial para el componente y tomar el último registro *antes* de esta ejecución
        df_componente = df_historial[df_historial['Componente'] == componente].sort_values(by='Fecha', ascending=False)
        
        # Necesitamos al menos un registro histórico para comparar
        if len(df_componente) >= 1:
            precio_anterior = df_componente.iloc[0]['Precio']
            
            # 2. Lógica de comparación
            diferencia = precio_actual - precio_anterior
            if precio_anterior == 0: continue 

            porcentaje_cambio = diferencia / precio_anterior
            
            # 3. Verificar si es una caída significativa (ej. más del 5% negativo)
            if porcentaje_cambio < -UMBRAL_BAJADA:
                
                # --- ALERTA DETECTADA ---
                porcentaje_caida = abs(porcentaje_cambio * 100)
                
                asunto = f"ALERTA DE PRECIO: {componente} cayó un {porcentaje_caida:.2f}%"
                cuerpo = (
                    f"Componente: {componente}\n"
                    f"Precio Anterior: ${precio_anterior:.2f}\n"
                    f"Precio Actual: ${precio_actual:.2f}\n"
                    f"Caída Total: ${abs(diferencia):.2f}\n"
                    f"URL: {fila_nueva['URL']}"
                )
                
                print(f"** ¡ALERTA! ** {componente} cayó un {porcentaje_caida:.2f}%")
                
                # Enviar Email
                enviar_email_alerta(asunto, cuerpo)
                alertas_enviadas += 1

    print(f"Análisis completado. Se detectaron {alertas_enviadas} alertas de bajada.")


# ----------------- FUNCIÓN PRINCIPAL DE EJECUCIÓN -----------------

def ejecutar_scraping():
    """Ejecuta la extracción, análisis y guarda los resultados."""
    datos_recientes = []
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nombre_archivo = 'historial_precios.csv'

    print(f"Iniciando extracción a las {fecha_actual}...")
    
    # 1. Cargar historial existente ANTES de la extracción para tener datos de comparación.
    df_historial = None
    if os.path.exists(nombre_archivo):
        df_historial = pd.read_csv(nombre_archivo)
    
    for componente, url in productos.items():
        precio = extraer_precio(url)
        
        if precio is not None:
             print(f"  > Componente: {componente} | Precio extraído: ${precio}")
             datos_recientes.append({
                 'Fecha': fecha_actual,
                 'Componente': componente,
                 'Precio': precio,
                 'URL': url
             })
        else:
             print(f"  > ❌ Fallo en {componente}. (Precio no encontrado o error en la URL)")


    # 2. Ejecutar el análisis y alerta
    if datos_recientes:
        df_nuevos_datos = pd.DataFrame(datos_recientes)
        
        if df_historial is not None and not df_historial.empty:
            analizar_y_alertar(df_historial, df_nuevos_datos) 
            
        # 3. Guarda la nueva data (añade los datos de esta ejecución al historial)
        guardar_datos_csv(datos_recientes, nombre_archivo)
    else:
        print("No se extrajo ningún precio, no se actualizará el historial.")

# Ejecutar el script principal
if __name__ == "__main__":
    ejecutar_scraping()