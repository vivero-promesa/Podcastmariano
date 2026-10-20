"""Versión de consola del flujo (sin Streamlit).

Uso:  python main.py
Guarda la investigación, el guion y la revisión del Censor en la carpeta episodios/.
"""
import json
import os
import re

import config
from agents.investigator import investigar
from agents.script_writer import escribir_guion
from agents.theologian import resumen_para_correccion, revisar


def elegir_documento() -> dict:
    opciones = config.DOCUMENTOS + [config.TEMA_LIBRE]
    for i, d in enumerate(opciones, 1):
        print(f"  {i:2d}. {config.etiqueta_documento(d)}")
    while True:
        n = input("\nNúmero del documento: ").strip()
        if n.isdigit() and 1 <= int(n) <= len(opciones):
            return opciones[int(n) - 1]


def imprimir_revision(rev, titulo):
    print(f"\n⛪ {titulo}: {rev.veredicto} | Rigor {rev.nivel_rigor}/10")
    for c in rev.citas_dudosas:
        print(f"   ⚠️ Cita dudosa: {c}")
    for o in rev.observaciones:
        print(f"   • {o}")


def main():
    print(f"🎙️  {config.PODCAST['nombre']}\n" + "=" * 60)
    doc = elegir_documento()
    tema = input(f"Pregunta o enfoque [{doc['tema']}]: ").strip() or doc["tema"]

    print("\n🔎 Investigando…")
    inv = investigar(tema, doc if doc["url"] else None)
    rev = revisar(inv["informe"], "investigación", inv["fuente_texto"])
    print(inv["informe"])
    imprimir_revision(rev, "Censor (investigación)")
    if rev.veredicto == "RECHAZADO" or input("\n👑 ¿Apruebas la investigación? (si/no): ").strip().lower() != "si":
        print("🛑 Producción detenida.")
        return

    print("\n✍️ Escribiendo guion…")
    guion = escribir_guion(inv["informe"], tema)
    rev_g = revisar(guion, "guion", inv["fuente_texto"])
    if rev_g.veredicto != "APROBADO":
        print("🛠️ Aplicando correcciones del Censor…")
        guion = escribir_guion(inv["informe"], tema, correcciones=resumen_para_correccion(rev_g), guion_anterior=guion)
        rev_g = revisar(guion, "guion", inv["fuente_texto"])
    imprimir_revision(rev_g, "Censor (guion)")

    carpeta = os.path.join("episodios", re.sub(r"[^a-z0-9]+", "-", tema.lower()).strip("-")[:60])
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(carpeta, "investigacion.md"), "w", encoding="utf-8") as f:
        f.write(inv["informe"])
    with open(os.path.join(carpeta, "guion.md"), "w", encoding="utf-8") as f:
        f.write(guion)
    with open(os.path.join(carpeta, "revision.json"), "w", encoding="utf-8") as f:
        json.dump({"investigacion": rev.model_dump(), "guion": rev_g.model_dump()}, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Listo. Archivos en {carpeta}/")


if __name__ == "__main__":
    main()
