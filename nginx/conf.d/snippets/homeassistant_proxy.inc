# Reusable reverse-proxy settings for Home Assistant.
# Included from both the local (port 80) and external (443) server blocks.
proxy_pass http://127.0.0.1:8123;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $connection_upgrade;
proxy_buffering off;
