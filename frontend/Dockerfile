FROM node:20-alpine

WORKDIR /app

# Install dependencies (uses package-lock.json for reproducible installs)
COPY package*.json ./
RUN npm ci

# Copy the rest of the source
COPY . .

EXPOSE 5173

# --host makes the Vite dev server bind to 0.0.0.0 (required inside Docker)
CMD ["npm", "run", "dev", "--", "--host"]
