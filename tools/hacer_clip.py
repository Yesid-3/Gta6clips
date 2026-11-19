#!/usr/bin/env python3
"""Convierte un video horizontal en un clip vertical 9:16 listo para TikTok, Reels y Shorts.

Formato del clip (secciones 6 y 7 del prompt):
  - 1080x1920, H.264 + AAC, MP4
  - fondo desenfocado del mismo video, video centrado
  - gancho grande arriba, crédito abajo, subtítulos opcionales (.srt)
  - también guarda un .txt con los textos para cada plataforma

Ejemplo:
  python3 tools/hacer_clip.py media/raw/video.mp4 \
      --inicio 1:23 --fin 1:41 \
      --gancho "NADIE ESPERABA ESTO" \
      --credito "@creador" \
      --salida media/edits/npc-raro.mp4
"""
import argparse
import os
import subprocess
import sys
import tempfile
import textwrap

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ANCHO, ALTO = 1080, 1920


def segundos(t):
    """Acepta 83, 83.5, '1:23' o '0:01:23'."""
    if t is None:
        return None
    partes = [float(p) for p in str(t).split(":")]
    total = 0.0
    for p in partes:
        total = total * 60 + p
    return total


def sin_emojis(texto):
    # La fuente de video no dibuja emojis: van solo en el texto del post.
    return "".join(c for c in texto if ord(c) < 0x2000 or 0x2000 <= ord(c) <= 0x206F).strip()


def escapar_ruta(ruta):
    return ruta.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", help="video original (guárdalo en media/raw/ con su enlace anotado)")
    ap.add_argument("--inicio", help="segundo o mm:ss donde empieza el clip")
    ap.add_argument("--fin", help="segundo o mm:ss donde termina el clip")
    ap.add_argument("--gancho", required=True, help="texto grande arriba (se pasa a MAYÚSCULAS)")
    ap.add_argument("--credito", required=True, help='ej. "@creador" o "@RockstarGames"')
    ap.add_argument("--subtitulos", help="archivo .srt opcional para subtítulos quemados")
    ap.add_argument("--texto-post", help="texto del post; por defecto se usa el gancho")
    ap.add_argument("--spoiler", action="store_true", help='agrega "SPOILER" al texto del post')
    ap.add_argument("--salida", required=True, help="ruta del MP4 final (media/edits/...)")
    a = ap.parse_args()

    ini, fin = segundos(a.inicio), segundos(a.fin)
    if ini is not None and fin is not None:
        dur = fin - ini
        if dur <= 0:
            sys.exit("El fin debe ser mayor que el inicio.")
        if not 5 <= dur <= 60:
            print(f"Aviso: el clip dura {dur:.1f} s. Lo ideal son 7 a 30 s.", file=sys.stderr)

    gancho = sin_emojis(a.gancho).upper()
    lineas = textwrap.wrap(gancho, width=14)[:3]
    # DejaVu Bold en mayúsculas mide ~0.72 del tamaño por letra; deja 60 px de margen a cada lado.
    tam = min(96, int((ANCHO - 120) / (0.72 * max(len(l) for l in lineas))))

    tmp = tempfile.mkdtemp()
    filtros = [
        f"[0:v]scale={ANCHO}:{ALTO}:force_original_aspect_ratio=increase,crop={ANCHO}:{ALTO},"
        f"gblur=sigma=30,eq=brightness=-0.15[fondo]",
        f"[0:v]scale={ANCHO}:-2[frente]",
        "[fondo][frente]overlay=(W-w)/2:(H-h)/2[base]",
    ]
    actual = "base"
    y0 = 260
    for i, linea in enumerate(lineas):
        archivo = os.path.join(tmp, f"g{i}.txt")
        with open(archivo, "w", encoding="utf-8") as f:
            f.write(linea)
        sig = f"g{i}"
        filtros.append(
            f"[{actual}]drawtext=fontfile={FUENTE}:textfile='{escapar_ruta(archivo)}':"
            f"fontsize={tam}:fontcolor=white:borderw=8:bordercolor=black:"
            f"x=(w-text_w)/2:y={y0 + i * int(tam * 1.2)}[{sig}]"
        )
        actual = sig

    credito = os.path.join(tmp, "credito.txt")
    with open(credito, "w", encoding="utf-8") as f:
        f.write("Clip: " + sin_emojis(a.credito))
    filtros.append(
        f"[{actual}]drawtext=fontfile={FUENTE}:textfile='{escapar_ruta(credito)}':"
        f"fontsize=44:fontcolor=white:borderw=5:bordercolor=black:"
        f"x=(w-text_w)/2:y=h-300[cred]"
    )
    actual = "cred"

    if a.subtitulos:
        estilo = ("FontName=DejaVu Sans,Bold=1,FontSize=11,PrimaryColour=&H00FFFFFF,"
                  "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Alignment=2,MarginV=70")
        filtros.append(f"[{actual}]subtitles='{escapar_ruta(a.subtitulos)}':force_style='{estilo}'[subs]")
        actual = "subs"

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    if ini is not None:
        cmd += ["-ss", str(ini)]
    if fin is not None:
        cmd += ["-to", str(fin)]
    cmd += ["-i", a.entrada, "-filter_complex", ";".join(filtros),
            "-map", f"[{actual}]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-r", "30", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
            "-movflags", "+faststart", a.salida]
    os.makedirs(os.path.dirname(os.path.abspath(a.salida)), exist_ok=True)
    subprocess.run(cmd, check=True)

    titulo = a.texto_post or (a.gancho.upper() if a.gancho.upper() == a.gancho else a.gancho)
    spoiler = "SPOILER\n\n" if a.spoiler else ""
    textos = f"""=== X (sin hashtags) ===
{spoiler}{titulo}

🎥 {a.credito}

=== Instagram Reels ===
{spoiler}{titulo}

Etiqueta a quien le pasaría esto 👀

🎥 {a.credito}

#GTA6 #GTAVI #GTA6Clips #Gaming #GTA6Español

=== TikTok / YouTube Shorts ===
{spoiler}{titulo} 🎥 {a.credito} #GTA6 #GTAVI #gaming
"""
    txt = os.path.splitext(a.salida)[0] + ".txt"
    with open(txt, "w", encoding="utf-8") as f:
        f.write(textos)
    print(f"Clip: {a.salida}\nTextos: {txt}")


if __name__ == "__main__":
    main()
