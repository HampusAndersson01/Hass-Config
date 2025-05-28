# Nodalink Add-on Installation Guide

## 🔧 Local Installation (Recommended)

Since these are custom add-ons, they need to be built locally rather than pulled from a registry.

### Step 1: Add Local Repository

1. **Copy the repository to your Home Assistant system**:
   ```bash
   # If using SSH access to Home Assistant
   scp -r /workspaces/Hass-Config/nodalink-* root@your-ha-ip:/addons/
   
   # Or if using the File Editor add-on, create these directories:
   # /addons/nodalink-core/
   # /addons/nodalink-frontend/
   ```

2. **Add as local add-on repository**:
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Click the **⋮** menu (three dots) → **Repositories**
   - Add local path: `/addons` or the path where you placed the folders

### Step 2: Install Add-ons

1. **Install Nodalink Core** (install this first):
   - Find "Nodalink Core" in your local repository
   - Click **Install** (it will build locally)
   - Configure options in the **Configuration** tab:
     ```yaml
     api_port: 8002
     api_host: "0.0.0.0"
     time_zone: "Your/Timezone"
     test_mode: false
     cors_origins: ["*"]
     ```
   - Start the add-on

2. **Install Nodalink Frontend**:
   - Find "Nodalink Frontend" in your local repository  
   - Click **Install** (it will build locally)
   - Configure options:
     ```yaml
     port: 3000
     api_url: "http://supervisor:8002"
     websocket_url: "ws://supervisor:8002/ws"
     ```
   - Start the add-on

### Step 3: Access the Interface

- **Frontend**: http://your-ha-ip:3000
- **API**: http://your-ha-ip:8002
- **AppDaemon Dashboard**: http://your-ha-ip:5050 (optional)

## 🐋 Alternative: Docker Build Method

If the above doesn't work, you can build the images manually:

### For aarch64 (Raspberry Pi 4, etc.):

```bash
# Build nodalink-core
cd /workspaces/Hass-Config/nodalink-core
docker build --platform linux/arm64 -t local/nodalink-core:latest .

# Build nodalink-frontend  
cd /workspaces/Hass-Config/nodalink-frontend
docker build --platform linux/arm64 -t local/nodalink-frontend:latest .
```

### For amd64 (x86_64 systems):

```bash
# Build nodalink-core
cd /workspaces/Hass-Config/nodalink-core
docker build --platform linux/amd64 -t local/nodalink-core:latest .

# Build nodalink-frontend
cd /workspaces/Hass-Config/nodalink-frontend  
docker build --platform linux/amd64 -t local/nodalink-frontend:latest .
```

Then update the config.json files to use local images:
```json
{
  "image": "local/nodalink-core:latest"
}
```

## 🚀 Publishing to GHCR (Optional)

If you want to publish your own images to GitHub Container Registry:

### Step 1: Setup GHCR Authentication

```bash
# Create a GitHub Personal Access Token with packages:write scope
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

### Step 2: Build and Push Multi-arch Images

```bash
# Create and use a multi-platform builder
docker buildx create --name multiplatform --use

# Build and push nodalink-core
cd /workspaces/Hass-Config/nodalink-core
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag ghcr.io/YOUR_USERNAME/nodalink-core:1.0.0 \
  --push .

# Build and push nodalink-frontend
cd /workspaces/Hass-Config/nodalink-frontend
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag ghcr.io/YOUR_USERNAME/nodalink-frontend:1.0.0 \
  --push .
```

### Step 3: Update config.json

```json
{
  "image": "ghcr.io/YOUR_USERNAME/{arch}-addon-nodalink-core"
}
```

### Step 4: Make Repository Public

1. Go to https://github.com/YOUR_USERNAME?tab=packages
2. Find your packages
3. Click **Package settings** → **Change visibility** → **Public**

## 🔍 Troubleshooting

### Build Failures

1. **Check base image availability**:
   ```bash
   docker pull ghcr.io/home-assistant/aarch64-base:3.19
   ```

2. **Verify Dockerfile syntax**:
   ```bash
   docker build --no-cache -t test .
   ```

3. **Check Home Assistant logs**:
   - Settings → System → Logs
   - Look for add-on build errors

### Network Issues

1. **Verify ports are not in use**:
   ```bash
   netstat -tulpn | grep :8002
   netstat -tulpn | grep :3000
   ```

2. **Check firewall settings**:
   ```bash
   # If using UFW
   sudo ufw allow 8002
   sudo ufw allow 3000
   ```

### API Connection Issues

1. **Test API directly**:
   ```bash
   curl http://localhost:8002/health
   ```

2. **Check WebSocket connection**:
   - Browser dev tools → Network → WS tab
   - Should see connection to `ws://localhost:8002/ws`

## ✅ Success Checklist

- [ ] Both add-ons build successfully without errors
- [ ] Nodalink Core starts and API responds at port 8002
- [ ] Nodalink Frontend starts and loads at port 3000
- [ ] Frontend can connect to Core API
- [ ] WebSocket connection established for real-time updates
- [ ] AppDaemon engine connects to Home Assistant
- [ ] Scenario management works through the frontend

## 📝 Development Notes

- Always test locally before pushing to GHCR
- Use semantic versioning for releases (1.0.0, 1.1.0, etc.)
- Keep build.yaml and config.json in sync
- Test on your target architecture (arm64 vs amd64)
- Monitor add-on logs during initial setup
