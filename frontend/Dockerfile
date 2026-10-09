# Image du FRONTEND, construite en 2 etapes ("multi-stage build")

# Etape 1 : Node.js construit le site React (npm run build -> dossier dist/)
FROM node:20-alpine AS construction
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Etape 2 : Nginx sert le site et transmet /api au backend
# (Node.js n'est plus dans l'image finale : elle est petite et legere)
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=construction /app/dist /usr/share/nginx/html
EXPOSE 80
