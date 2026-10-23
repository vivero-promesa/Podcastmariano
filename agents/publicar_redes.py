"""Publicación directa de los clips en Instagram (Reel) y TikTok.

INSTAGRAM — «API de Instagram con inicio de sesión de Instagram» (no necesita Facebook).
  Instagram descarga el video desde una dirección pública: la app lo sube a un
  alojamiento temporal (litterbox.catbox.moe, se borra solo en 1 hora), crea el Reel,
  espera a que Instagram lo procese y lo publica.
  Secreto: INSTAGRAM_TOKEN (token de larga duración, dura 60 días; la app lo renueva).

TIKTOK — Content Posting API.
  Modo «borrador» (por defecto): el video llega a tu bandeja de TikTok; abres TikTok,
  pegas el texto y publicas. Funciona sin que TikTok audite la app.
  Modo «directo»: se publica de una vez. Mientras la app no esté auditada por TikTok,
  solo se permite publicar como privado («Solo yo»).
  Secretos: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN, TIKTOK_REDIRECT_URI.
"""
import math
import os
import time
import urllib.parse
from typing import Optional

import requests

import config

TIEMPO_ESPERA = 60  # segundos para cada petición HTTP


class ErrorPublicacion(RuntimeError):
    pass


# ─────────────────────────── Alojamiento temporal ───────────────────────────

def subir_temporal(ruta: str, horas: str = "1h") -> str:
    """Sube el archivo a litterbox.catbox.moe (se borra solo) y devuelve su dirección pública."""
    with open(ruta, "rb") as f:
        r = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data={"reqtype": "fileupload", "time": horas},
            files={"fileToUpload": (os.path.basename(ruta), f)},
            timeout=300,
        )
    url = r.text.strip()
    if r.status_code != 200 or not url.startswith("http"):
        raise ErrorPublicacion(f"No se pudo subir el video al alojamiento temporal: {url[:200]}")
    return url


# ─────────────────────────── Instagram ───────────────────────────

_IG = {"token": None}


def _ig_base() -> str:
    return f"https://graph.instagram.com/{config.INSTAGRAM_API_VERSION}"


def instagram_configurado() -> bool:
    return bool(config.INSTAGRAM_TOKEN)


def _ig_token() -> str:
    return _IG["token"] or config.INSTAGRAM_TOKEN


def _ig(metodo: str, ruta: str, **params) -> dict:
    params["access_token"] = _ig_token()
    url = f"{_ig_base()}/{ruta.lstrip('/')}"
    r = requests.request(metodo, url, params=params if metodo == "GET" else None,
                         data=params if metodo != "GET" else None, timeout=TIEMPO_ESPERA)
    datos = r.json() if r.content else {}
    if r.status_code >= 400 or "error" in datos:
        error = datos.get("error", {})
        msg = error.get("error_user_msg") or error.get("message") or r.text[:300]
        if error.get("code") == 190:
            msg = "El token de Instagram venció o no es válido. Genera uno nuevo y cámbialo en los Secrets (INSTAGRAM_TOKEN)."
        raise ErrorPublicacion(f"Instagram: {msg}")
    return datos


def instagram_cuenta() -> dict:
    """{'id': ..., 'username': ...} de la cuenta conectada."""
    d = _ig("GET", "me", fields="user_id,username")
    return {"id": d.get("user_id") or d.get("id"), "username": d.get("username", "")}


def renovar_token_instagram() -> Optional[str]:
    """Renueva el token de larga duración (otros 60 días). Devuelve el token nuevo para pegarlo en Secrets."""
    r = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": _ig_token()},
        timeout=TIEMPO_ESPERA,
    )
    datos = r.json() if r.content else {}
    nuevo = datos.get("access_token")
    if nuevo:
        _IG["token"] = nuevo
    return nuevo


def publicar_instagram(mp4: str, texto: str, portada: Optional[str] = None,
                       reel_de_prueba: bool = False, avisar=lambda m: None) -> dict:
    """Publica el clip como Reel. Devuelve {'id': ..., 'enlace': ...}."""
    cuenta = instagram_cuenta()
    avisar("⬆️ Subiendo el video para Instagram…")
    video_url = subir_temporal(mp4)
    datos = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": texto[:2200],
        "share_to_feed": "true",
    }
    if portada and os.path.exists(portada):
        try:
            datos["cover_url"] = subir_temporal(portada)
        except ErrorPublicacion:
            pass
    if reel_de_prueba:
        datos["trial_params"] = '{"graduation_strategy":"SS_PERFORMANCE"}'

    avisar("📦 Creando el Reel en Instagram…")
    try:
        contenedor = _ig("POST", f"{cuenta['id']}/media", **datos)
    except ErrorPublicacion:
        if not reel_de_prueba:
            raise
        # Si la cuenta aún no tiene Reels de prueba, se publica como Reel normal.
        datos.pop("trial_params", None)
        avisar("ℹ️ Tu cuenta no admite Reel de prueba por API; se publica como Reel normal.")
        contenedor = _ig("POST", f"{cuenta['id']}/media", **datos)
    cid = contenedor["id"]

    avisar("⏳ Instagram está procesando el video (puede tardar 1-3 minutos)…")
    for _ in range(60):
        estado = _ig("GET", cid, fields="status_code,status")
        codigo = estado.get("status_code")
        if codigo == "FINISHED":
            break
        if codigo in ("ERROR", "EXPIRED"):
            raise ErrorPublicacion(f"Instagram no pudo procesar el video: {estado.get('status', codigo)}")
        time.sleep(5)
    else:
        raise ErrorPublicacion("Instagram tardó demasiado procesando el video. Inténtalo de nuevo en unos minutos.")

    avisar("🚀 Publicando en Instagram…")
    pub = _ig("POST", f"{cuenta['id']}/media_publish", creation_id=cid)
    enlace = ""
    try:
        enlace = _ig("GET", pub["id"], fields="permalink").get("permalink", "")
    except ErrorPublicacion:
        pass
    return {"id": pub["id"], "enlace": enlace or config.PODCAST["instagram_url"]}


# ─────────────────────────── TikTok ───────────────────────────

_TT_API = "https://open.tiktokapis.com/v2"
_TT = {"access": None, "vence": 0.0, "refresh": None}
ALCANCES_TIKTOK = "user.info.basic,video.upload,video.publish"


def tiktok_configurado() -> bool:
    return bool(config.TIKTOK_CLIENT_KEY and config.TIKTOK_CLIENT_SECRET and (_TT["refresh"] or config.TIKTOK_REFRESH_TOKEN))


def tiktok_puede_conectar() -> bool:
    return bool(config.TIKTOK_CLIENT_KEY and config.TIKTOK_CLIENT_SECRET and config.TIKTOK_REDIRECT_URI)


def url_conectar_tiktok(estado: str) -> str:
    q = {
        "client_key": config.TIKTOK_CLIENT_KEY,
        "scope": ALCANCES_TIKTOK,
        "response_type": "code",
        "redirect_uri": config.TIKTOK_REDIRECT_URI,
        "state": estado,
    }
    return "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode(q)


def _tt_token_peticion(datos: dict) -> dict:
    datos = {"client_key": config.TIKTOK_CLIENT_KEY, "client_secret": config.TIKTOK_CLIENT_SECRET, **datos}
    r = requests.post(f"{_TT_API}/oauth/token/", data=datos,
                      headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=TIEMPO_ESPERA)
    d = r.json() if r.content else {}
    if "access_token" not in d:
        raise ErrorPublicacion(f"TikTok no entregó el permiso: {d.get('error_description') or d.get('error') or r.text[:200]}")
    _TT.update(access=d["access_token"], vence=time.time() + int(d.get("expires_in", 3600)) - 120,
               refresh=d.get("refresh_token") or _TT["refresh"])
    return d


def cambiar_codigo_tiktok(codigo: str) -> str:
    """Tras «Conectar TikTok»: cambia el código por los permisos. Devuelve el refresh token
    (dura 365 días) para pegarlo en los Secrets como TIKTOK_REFRESH_TOKEN."""
    d = _tt_token_peticion({"code": codigo, "grant_type": "authorization_code",
                            "redirect_uri": config.TIKTOK_REDIRECT_URI})
    return d.get("refresh_token", "")


def _tt_access() -> str:
    if _TT["access"] and time.time() < _TT["vence"]:
        return _TT["access"]
    refresh = _TT["refresh"] or config.TIKTOK_REFRESH_TOKEN
    if not refresh:
        raise ErrorPublicacion("TikTok no está conectado. Usa «Conectar TikTok» en la sección de publicación.")
    _tt_token_peticion({"grant_type": "refresh_token", "refresh_token": refresh})
    return _TT["access"]


def refresh_tiktok_cambio() -> Optional[str]:
    """Si TikTok entregó un refresh token distinto al de los Secrets, lo devuelve para actualizarlo."""
    if _TT["refresh"] and _TT["refresh"] != config.TIKTOK_REFRESH_TOKEN:
        return _TT["refresh"]
    return None


def _tt(ruta: str, cuerpo: dict) -> dict:
    r = requests.post(
        f"{_TT_API}/{ruta.lstrip('/')}",
        json=cuerpo,
        headers={"Authorization": f"Bearer {_tt_access()}", "Content-Type": "application/json; charset=UTF-8"},
        timeout=TIEMPO_ESPERA,
    )
    d = r.json() if r.content else {}
    err = d.get("error", {})
    if r.status_code >= 400 or (err and err.get("code") not in (None, "ok")):
        codigo = err.get("code", r.status_code)
        msg = err.get("message") or r.text[:300]
        if codigo == "unaudited_client_can_only_post_to_private_accounts":
            msg = ("TikTok solo deja publicar directo en cuentas privadas mientras la app no esté auditada. "
                   "Usa el modo «borrador» (TIKTOK_MODO = \"borrador\") o pide la auditoría en TikTok for Developers.")
        elif codigo == "spam_risk_too_many_posts":
            msg = "TikTok frenó la publicación por demasiadas subidas seguidas. Espera un rato."
        raise ErrorPublicacion(f"TikTok: {msg} ({codigo})")
    return d.get("data", {})


def tiktok_cuenta() -> dict:
    r = requests.get(
        f"{_TT_API}/user/info/", params={"fields": "display_name,username"},
        headers={"Authorization": f"Bearer {_tt_access()}"}, timeout=TIEMPO_ESPERA,
    )
    d = (r.json() if r.content else {}).get("data", {}).get("user", {})
    return {"nombre": d.get("display_name", ""), "usuario": d.get("username", "")}


def _partes(tam: int):
    """TikTok: un solo trozo si pesa hasta 64 MB; si no, trozos de 10 MB (el último absorbe el resto)."""
    if tam <= 64 * 1024 * 1024:
        return tam, 1
    trozo = 10 * 1024 * 1024
    return trozo, max(1, math.floor(tam / trozo))


def _subir_trozos(upload_url: str, mp4: str, tam: int, trozo: int, cuantos: int):
    with open(mp4, "rb") as f:
        for n in range(cuantos):
            ini = n * trozo
            fin = tam - 1 if n == cuantos - 1 else ini + trozo - 1
            f.seek(ini)
            datos = f.read(fin - ini + 1)
            r = requests.put(
                upload_url, data=datos, timeout=300,
                headers={"Content-Type": "video/mp4", "Content-Length": str(len(datos)),
                         "Content-Range": f"bytes {ini}-{fin}/{tam}"},
            )
            if r.status_code not in (200, 201, 206):
                raise ErrorPublicacion(f"TikTok rechazó la subida del video ({r.status_code}): {r.text[:200]}")


def publicar_tiktok(mp4: str, texto: str, avisar=lambda m: None) -> dict:
    """Sube el clip a TikTok. Modo borrador: queda en tu bandeja. Modo directo: se publica.
    Devuelve {'modo': ..., 'estado': ..., 'privacidad': ...}."""
    tam = os.path.getsize(mp4)
    trozo, cuantos = _partes(tam)
    fuente = {"source": "FILE_UPLOAD", "video_size": tam, "chunk_size": trozo, "total_chunk_count": cuantos}

    privacidad = ""
    if config.TIKTOK_MODO == "directo":
        info = _tt("post/publish/creator_info/query/", {})
        opciones = info.get("privacy_level_options", [])
        privacidad = "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in opciones else (opciones[0] if opciones else "SELF_ONLY")
        avisar("📦 Preparando la publicación en TikTok…")
        datos = _tt("post/publish/video/init/", {
            "post_info": {
                "title": texto[:2200],
                "privacy_level": privacidad,
                "disable_duet": False,
                "disable_stitch": False,
                "disable_comment": False,
                "video_cover_timestamp_ms": 500,
            },
            "source_info": fuente,
        })
    else:
        avisar("📦 Preparando el envío a tu bandeja de TikTok…")
        datos = _tt("post/publish/inbox/video/init/", {"source_info": fuente})

    avisar("⬆️ Subiendo el video a TikTok…")
    _subir_trozos(datos["upload_url"], mp4, tam, trozo, cuantos)

    estado = "PROCESSING_UPLOAD"
    for _ in range(40):
        time.sleep(4)
        try:
            estado = _tt("post/publish/status/fetch/", {"publish_id": datos["publish_id"]}).get("status", estado)
        except ErrorPublicacion:
            break
        if estado in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"):
            break
        if estado == "FAILED":
            raise ErrorPublicacion("TikTok no pudo procesar el video.")
    return {"modo": config.TIKTOK_MODO, "estado": estado, "privacidad": privacidad}
