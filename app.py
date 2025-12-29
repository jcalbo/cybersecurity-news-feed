import json
import time
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta

import aiohttp
import asyncio
import feedparser
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Feed de Ciberseguridad", layout="wide", initial_sidebar_state="expanded")

# Fuentes RSS
RSS_FEEDS = {
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "Wiz Blog": "https://www.wiz.io/feed/rss.xml",
    "StepSecurity": "https://www.stepsecurity.io/blog/rss.xml",
    "ReversingLabs": "https://www.reversinglabs.com/blog/rss.xml",
}

# Archivo de caché
CACHE_FILE = Path("cache/news_cache.json")
CACHE_DURATION = 600  # 10 minutos en segundos


class NewsCache:
    """Gestión de caché de noticias"""

    @staticmethod
    def load_cache() -> Dict:
        """Cargar caché desde archivo"""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    # Verificar si el caché ha expirado
                    if time.time() - cache_data.get("timestamp", 0) < CACHE_DURATION:
                        # Convertir strings de fecha de vuelta a datetime
                        for item in cache_data.get("news", []):
                            if "published" in item and isinstance(item["published"], str):
                                item["published"] = datetime.fromisoformat(item["published"])
                        return cache_data
            except json.JSONDecodeError as e:
                # Si el caché está corrupto, eliminarlo
                try:
                    CACHE_FILE.unlink()
                except:
                    pass
            except Exception as e:
                st.warning(f"Error al cargar caché: {e}")
        return None

    @staticmethod
    def save_cache(news_items: List[Dict]):
        """Guardar caché en archivo"""
        try:
            # Crear una copia de los items para no modificar los originales
            serializable_items = []
            for item in news_items:
                item_copy = item.copy()
                # Convertir datetime a string ISO format
                if "published" in item_copy and isinstance(item_copy["published"], datetime):
                    item_copy["published"] = item_copy["published"].isoformat()
                serializable_items.append(item_copy)

            cache_data = {"timestamp": time.time(), "news": serializable_items}
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.warning(f"Error al guardar caché: {e}")


async def fetch_feed(session: aiohttp.ClientSession, name: str, url: str) -> List[Dict]:
    """Obtener y parsear un feed RSS de forma asíncrona"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            content = await response.text()
            feed = feedparser.parse(content)

            news_items = []
            for entry in feed.entries:
                # Extraer fecha de publicación
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                else:
                    pub_date = datetime.now()

                # Extraer descripción
                description = ""
                if hasattr(entry, "description"):
                    description = entry.description
                elif hasattr(entry, "summary"):
                    description = entry.summary

                # Limpiar HTML tags básicos de la descripción
                import re

                description = re.sub(r"<[^>]+>", "", description)
                description = description.strip()

                news_item = {
                    "title": entry.title if hasattr(entry, "title") else "Sin título",
                    "link": entry.link if hasattr(entry, "link") else "",
                    "description": description[:300] + "..." if len(description) > 300 else description,
                    "published": pub_date,
                    "source": name,
                    "author": entry.author if hasattr(entry, "author") else name,
                }

                news_items.append(news_item)

            return news_items

    except Exception as e:
        st.warning(f"Error al obtener {name}: {e}")
        return []


async def fetch_all_feeds() -> List[Dict]:
    """Obtener todos los feeds de forma concurrente"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_feed(session, name, url) for name, url in RSS_FEEDS.items()]
        results = await asyncio.gather(*tasks)

        # Combinar todos los resultados
        all_news = []
        for news_list in results:
            all_news.extend(news_list)

        return all_news


def get_news() -> List[Dict]:
    """Obtener noticias (desde caché o haciendo peticiones)"""
    # Intentar cargar desde caché
    cache = NewsCache.load_cache()
    if cache and "news" in cache:
        return cache["news"]

    # Si no hay caché válido, obtener noticias
    with st.spinner("Obteniendo noticias..."):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        news_items = loop.run_until_complete(fetch_all_feeds())
        loop.close()

        # Guardar en caché
        NewsCache.save_cache(news_items)

        return news_items


def filter_by_time(news_items: List[Dict], hours: int = None) -> List[Dict]:
    """Filtrar noticias por tiempo"""
    if hours is None:
        return news_items

    cutoff_time = datetime.now() - timedelta(hours=hours)
    return [item for item in news_items if item["published"] >= cutoff_time]


def filter_by_search(news_items: List[Dict], search_term: str) -> List[Dict]:
    """Filtrar noticias por término de búsqueda"""
    if not search_term:
        return news_items

    search_term = search_term.lower()
    return [item for item in news_items if search_term in item["title"].lower() or search_term in item["description"].lower()]


def filter_by_source(news_items: List[Dict], sources: List[str]) -> List[Dict]:
    """Filtrar noticias por fuente"""
    if not sources or len(sources) == len(RSS_FEEDS):
        return news_items

    return [item for item in news_items if item["source"] in sources]


def display_news_item(item: Dict):
    """Mostrar un item de noticia con formato mejorado"""
    # Calcular tiempo transcurrido
    time_diff = datetime.now() - item["published"]
    if time_diff.days > 0:
        time_str = f"hace {time_diff.days} día{'s' if time_diff.days > 1 else ''}"
    elif time_diff.seconds >= 3600:
        hours = time_diff.seconds // 3600
        time_str = f"hace {hours} hora{'s' if hours > 1 else ''}"
    else:
        minutes = time_diff.seconds // 60
        time_str = f"hace {minutes} minuto{'s' if minutes > 1 else ''}"

    with st.container():
        col1, col2 = st.columns([0.95, 0.05])

        with col1:
            st.markdown(f"### [{item['title']}]({item['link']})")
            st.markdown(f"**Fuente:** {item['source']} | **Publicado:** {time_str}")
            st.markdown(f"{item['description']}")

        st.markdown("---")


def main():
    """Función principal de la aplicación"""

    # Header
    st.title("🔒 Feed de Ciberseguridad")
    st.markdown("**Fuentes:** BleepingComputer, The Hacker News, Wiz, StepSecurity, ReversingLabs")

    # Sidebar - Filtros
    with st.sidebar:
        st.header("⚙️ Filtros")

        # Filtro de tiempo
        st.subheader("📅 Periodo de tiempo")
        time_filter = st.radio(
            "Mostrar noticias de:", ["Últimas 12 horas", "Últimas 24 horas", "Últimas 48 horas", "Todos los tiempos"], index=1
        )

        time_map = {"Últimas 12 horas": 12, "Últimas 24 horas": 24, "Últimas 48 horas": 48, "Todos los tiempos": None}

        # Filtro de fuente
        st.subheader("📰 Fuentes")
        selected_sources = st.multiselect("Seleccionar fuentes:", options=list(RSS_FEEDS.keys()), default=list(RSS_FEEDS.keys()))

        # Búsqueda
        st.subheader("🔍 Búsqueda")
        search_term = st.text_input("Buscar por palabra clave:", "")

        # Ordenamiento
        st.subheader("📊 Ordenamiento")
        sort_order = st.radio("Ordenar por:", ["Más recientes primero", "Más antiguas primero"])

        # Botón de actualizar
        st.markdown("---")
        if st.button("🔄 Actualizar noticias", use_container_width=True):
            # Eliminar caché para forzar actualización
            if CACHE_FILE.exists():
                CACHE_FILE.unlink()
            st.rerun()

        # Info sobre caché
        if CACHE_FILE.exists():
            cache_data = NewsCache.load_cache()
            if cache_data:
                cache_age = time.time() - cache_data["timestamp"]
                st.info(f"⏱️ Caché: {int(cache_age)} segundos de antigüedad")

    # Obtener y procesar noticias
    news_items = get_news()

    # Aplicar filtros
    filtered_news = filter_by_time(news_items, time_map[time_filter])
    filtered_news = filter_by_search(filtered_news, search_term)
    filtered_news = filter_by_source(filtered_news, selected_sources)

    # Ordenar
    reverse = sort_order == "Más recientes primero"
    filtered_news = sorted(filtered_news, key=lambda x: x["published"], reverse=reverse)

    # Mostrar estadísticas
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📰 Total Noticias", len(filtered_news))
    with col2:
        sources_count = len(set(item["source"] for item in filtered_news))
        st.metric("📡 Fuentes", sources_count)

    st.markdown("---")

    # Mostrar noticias
    if filtered_news:
        for item in filtered_news:
            display_news_item(item)
    else:
        st.info("No se encontraron noticias con los filtros seleccionados.")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "🔒 Feed de Noticias de Ciberseguridad | "
        f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
