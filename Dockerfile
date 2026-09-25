# Pacsi by DarwinAI – a telepíthető PWA (dist/pwa) kiszolgálása nginx-szel.
# A Coolify (Hetzner) építi a GitHub-repóból; a HTTPS-t és a domaint (pacsit.hu) a Coolify proxyja adja.
# Nincs fordítás: a dist/pwa a repóban van (python tools/build.py), ide csak bemásoljuk.
FROM nginx:1.27-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/pwa/ /usr/share/nginx/html/
EXPOSE 80
