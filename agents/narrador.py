"""Voz IA gratuita (edge-tts) para borradores y cápsulas cortas.

El episodio principal se graba con tu voz; esta voz sirve para escuchar el guion
antes de grabar o para cápsulas de redes sin grabación.
"""
import asyncio
import os
import re

import edge_tts

import config


def limpiar_para_voz(texto: str) -> str:
    """Quita todo lo que no se debe leer en voz alta."""
    t = re.sub(r"^\s*-{2,}.*?-{2,}\s*$", "", texto, flags=re.MULTILINE)  # --- HOOK ---
    t = re.sub(r"\[/?CLIP\]", "", t)
    t = re.sub(r"\[[^\]]*\]", "", t)  # [MÚSICA: ...], [PAUSA], [SFX]
    t = re.sub(r"^\s*#+\s*", "", t, flags=re.MULTILINE)  # títulos markdown
    t = t.replace("*", "").replace("_", " ")
    t = re.sub(r"(?i)\b(narradora?|locutora?)\s*:\s*", "", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def generar_audio(texto_guion: str, ruta_salida: str = "voz_ia.mp3", velocidad: str = "+0%") -> dict:
    texto = limpiar_para_voz(texto_guion)
    if not texto:
        return {"success": False, "error": "El texto quedó vacío después de limpiarlo."}
    ruta = os.path.abspath(ruta_salida)

    async def _crear():
        await edge_tts.Communicate(texto, config.VOZ_IA, rate=velocidad).save(ruta)

    try:
        asyncio.run(_crear())
        return {"success": True, "ruta": ruta}
    except Exception as e:
        return {"success": False, "error": f"No se pudo generar la voz: {e}"}
