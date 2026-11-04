# Reusable reverse-proxy settings for OctoPrint.
# Included from both the local (port 88) and external (443/8888) server blocks.
proxy_pass http://127.0.0.1:8880/;
proxy_set_header Host $http_host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Scheme $scheme;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $connection_upgrade;
proxy_http_version 1.1;
client_max_body_size 0;
