# 🚀 Amazon Price Tracker & Alert System

Monitor de precios automatizado desarrollado en Python que rastrea componentes de PC de alta demanda en Amazon (EE. UU.) y alerta vía email al detectar caídas significativas (superiores al 5%).

Este proyecto demuestra habilidades críticas en **Web Scraping robusto, Persistencia de Datos, Analítica con Pandas y Automatización (SMTP)**.

## 🌟 Valor del Proyecto

El objetivo principal es transformar el dato crudo (precio en Amazon) en una **alerta de negocio actionable**. En lugar de revisar manualmente los precios, el sistema hace el trabajo por ti, garantizando la mejor oportunidad de compra.

## 🛠️ Tecnologías y Características

| Característica | Tecnología | Descripción Técnica |
| :--- | :--- | :--- |
| **Extracción Robusta** | `requests`, `BeautifulSoup` | Implementación de una estrategia de búsqueda por contenedor (`corePriceDisplay_desktop_feature_div`) para manejar las inconsistencias del HTML de Amazon y evitar fallos. |
| **Limpieza de Datos** | `re` (Expresiones Regulares) | Manejo de múltiples formatos de moneda y limpieza de caracteres especiales para convertir el precio a tipo `float` usable. |
| **Persistencia de Datos**| `Pandas`, `.csv` | Almacenamiento y gestión de un historial de precios en `historial_precios.csv`, fundamental para el análisis de series de tiempo. |
| **Analítica** | `Pandas` | Implementación de lógica para comparar el precio actual con el precio histórico, detectando variaciones superiores al umbral (`UMBRAL_BAJADA = 0.05`). |
| **Notificación Segura** | `smtplib`, `python-dotenv` | Envío de alertas por email al detectar una caída. Las credenciales de email se gestionan de forma segura fuera del código fuente. |

## 💻 Instalación y Uso

### Prerrequisitos

Asegúrate de tener **Python 3.x** instalado.

### 1. Clonar el repositorio

```bash
git clone [https://docs.github.com/es/repositories/creating-and-managing-repositories/quickstart-for-repositories](https://docs.github.com/es/repositories/creating-and-managing-repositories/quickstart-for-repositories)
cd MonitoreoPreciosAmazon