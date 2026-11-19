# GTA 6 Clips — página de fans sin rostro

Archivos de trabajo de la página (sección 15 del prompt de configuración).
No afiliada a Rockstar Games.

- `playbook.md` — cuenta, voz, mezcla, franjas, reglas
- `facts.md` — solo datos verificados con fuente oficial
- `idea-bank.md` — borradores por pilar
- `watchlist.md` — cuentas oficiales, creadores, subreddits
- `log.md` — todo lo publicado
- `scoreboard.csv` — métricas por post (12 h, 24 h, 72 h)
- `learning.md` — ganan, pierden, reglas actuales, revisiones semanales
- `takedowns.md` — solicitudes de retiro
- `media/official|raw|edits/` — los videos e imágenes quedan fuera de git

## Hacer un clip vertical
```
python3 tools/hacer_clip.py media/raw/video.mp4 --inicio 1:23 --fin 1:41 \
  --gancho "NADIE ESPERABA ESTO" --credito "@creador" --salida media/edits/clip.mp4
```
Crea un MP4 de 1080x1920 (H.264 + AAC) con fondo desenfocado, gancho arriba y crédito abajo.
Si le pasas `--subtitulos archivo.srt`, también quema los subtítulos. Junto al clip guarda un `.txt` con el texto para X, Instagram y TikTok/Shorts.
