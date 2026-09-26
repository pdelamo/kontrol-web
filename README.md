# Web de venta de Kontrol

La web de una página de Kontrol («Kontrol» es nombre provisional), servida en `kontrolapp.es` (antes `kontrol.delamotech.es`, que ahora redirige)
por un nginx detrás del Traefik del VPS. De momento es un borrador para enseñar: no sale en Google
(cabecera `X-Robots-Tag` y `web/robots.txt`).

- `web/`: lo que se publica, tal cual (la fuente está en `~/Desktop/Agencia IA/KONTROL/WEB/`).
- `nginx-web.conf`: la configuración de nginx (fuera de `web/` a propósito).
- `docker-compose.kontrolweb.yml`: el contenedor y sus etiquetas de Traefik.

**Primera vez (VPS):**

```
cd /root && git clone https://github.com/pdelamo/kontrol-web.git && cd kontrol-web && docker compose -p kontrolweb -f docker-compose.kontrolweb.yml up -d
```

**Cada versión nueva:** `cd /root/kontrol-web && git pull` (no hay nada que construir ni reiniciar).

DNS (Hostinger): en kontrolapp.es, registros **A** `@` y `www` → `187.124.113.210`; en delamotech.es, el **A** `kontrol` → `187.124.113.210` se deja (redirige).
