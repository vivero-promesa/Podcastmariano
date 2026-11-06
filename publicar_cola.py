"""Publica en Instagram los Reels de la cola a los que ya les llegó la hora.

Lo ejecuta GitHub Actions (.github/workflows/publicar-instagram.yml). Antes de publicar deja el
clip marcado «publicando», para que un fallo a mitad de camino nunca publique dos veces. Si
falla con un error claro, lo reintenta hasta 3 veces. Sale con error para que GitHub avise.
"""
import os
import sys
import tempfile
import traceback

from agents import cola
from agents import planeacion as plan_mod
from agents import publicar_redes as pub


def _marcar_en_calendario(item: dict):
    plan, _ = plan_mod._leer_github()
    if not plan:
        return
    semana = next((s for s in plan.get("semanas", []) if s.get("fecha") == item["semana"]), None)
    if semana:
        plan_mod.marcar_clip(semana, item["clip"] - 1, "Publicado")
        plan_mod.guardar(plan, f"Planeación: {item['id']} publicado")


def _guardar(item: dict, mensaje: str):
    datos, sha = cola.leer()
    datos["clips"] = [item if c["id"] == item["id"] else c for c in datos["clips"]]
    cola.escribir(datos, sha, mensaje)


def publicar(item: dict):
    item["estado"] = "publicando"
    item["intentos"] = item.get("intentos", 0) + 1
    _guardar(item, f"Cola de Instagram: publicando {item['id']}")
    with tempfile.TemporaryDirectory() as carpeta:
        mp4 = cola.descargar(item["video"]["url"], os.path.join(carpeta, "clip.mp4"))
        portada = None
        if item.get("portada"):
            portada = cola.descargar(item["portada"]["url"], os.path.join(carpeta, "portada.jpg"))
        resultado = pub.publicar_instagram(mp4, item["texto"], portada, avisar=print)
    item.update(estado="publicado", enlace=resultado["enlace"], error="")
    _guardar(item, f"Cola de Instagram: publicado {item['id']}")
    _marcar_en_calendario(item)
    cola.borrar_archivo(item["video"]["nombre"])
    if item.get("portada"):
        cola.borrar_archivo(item["portada"]["nombre"])
    print(f"Publicado {item['id']}: {item['enlace']}")


def principal(ahora=None) -> int:
    datos, _ = cola.leer()
    atascados = [c["id"] for c in datos.get("clips", []) if c["estado"] == "publicando"]
    fallos = 0
    for atascado in atascados:
        print(f"Revisar en Instagram si salió: {atascado} quedó a medias. No se reintenta para no repetirlo.")
        fallos += 1
    for item in cola.pendientes(datos, ahora):
        try:
            publicar(item)
        except Exception as e:
            fallos += 1
            traceback.print_exc()
            agotado = item.get("intentos", 0) >= cola.MAX_INTENTOS
            item.update(estado="error" if agotado else "pendiente", error=str(e)[:300])
            _guardar(item, f"Cola de Instagram: fallo en {item['id']}")
    print(f"Listo. Fallos: {fallos}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(principal())
