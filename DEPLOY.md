# Despliegue en Ubuntu

Guía paso a paso para instalar OpenCaja en un servidor Ubuntu (22.04/24.04 LTS) usando Docker.

## 1. Requisitos

- Servidor Ubuntu con acceso SSH y usuario con permisos `sudo`.
- (Opcional, para HTTPS) Un dominio apuntando a la IP del servidor.

## 2. Instalar Docker Engine

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

Verificar:
```bash
docker --version
docker compose version
```

## 3. Subir el código al servidor

```bash
sudo mkdir -p /opt/opencaja
sudo chown $USER:$USER /opt/opencaja
git clone https://github.com/falconsoft3d/opencaja.git /opt/opencaja
cd /opt/opencaja
```

## 4. Configurar variables de entorno

```bash
cd /opt/opencaja
cp .env.example .env
nano .env
```

Define en `.env`:
- `SECRET_KEY`: clave larga y aleatoria (genera una con el comando de abajo)
- `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`: credenciales del primer usuario administrador

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 5. Construir y levantar el contenedor

```bash
docker compose up -d --build
```

Verificar que arrancó correctamente:
```bash
docker compose logs -f web
curl -I http://localhost:8000/login
```
El entrypoint crea las tablas y el usuario administrador automáticamente en el primer arranque.

## 6. Firewall (ufw)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 8000/tcp    # solo si accedes directo por este puerto (sin Nginx)
sudo ufw enable
```

## 7. (Recomendado) Nginx como proxy inverso + HTTPS

Exponer la app directamente en el puerto 8000 sin TLS no es recomendable en internet. Lo ideal
es poner Nginx delante con HTTPS:

```bash
sudo apt install -y nginx
sudo tee /etc/nginx/sites-available/opencaja > /dev/null <<'EOF'
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
sudo ln -s /etc/nginx/sites-available/opencaja /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

sudo ufw allow "Nginx Full"
sudo ufw delete allow 8000/tcp
```

HTTPS gratis con Let's Encrypt:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

## 8. Auto-arranque tras reiniciar el servidor

No requiere pasos extra: Docker queda habilitado como servicio del sistema (`systemctl enable
docker`, paso 2) y el contenedor tiene `restart: unless-stopped` en `docker-compose.yml`, así que
vuelve a levantarse solo si el servidor se reinicia.

## 9. Backups

El estado (base de datos SQLite) vive en el volumen `opencaja_opencaja_data`.

Backup:
```bash
docker run --rm -v opencaja_opencaja_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/opencaja-backup-$(date +%Y%m%d).tar.gz -C /data .
```

Restaurar:
```bash
docker compose down
docker run --rm -v opencaja_opencaja_data:/data -v $(pwd):/backup alpine \
  sh -c "cd /data && tar xzf /backup/opencaja-backup-XXXXXXXX.tar.gz"
docker compose up -d
```

## 10. Actualizar a una nueva versión

```bash
cd /opt/opencaja
git pull
docker compose up -d --build
```
