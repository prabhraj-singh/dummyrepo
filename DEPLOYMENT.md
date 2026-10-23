# Azure Deployment Guide for Dummy MCP Server

## Overview
This guide covers deploying your MCP (Model Context Protocol) server to Azure using containerization.

## Prerequisites
- Azure CLI installed ([Install Guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))
- Docker installed locally
- Active Azure subscription

## Deployment Options

### Option 1: Azure Container Instances (ACI)
**Best for:** Simple deployments, testing, low-traffic applications

#### Quick Deploy
```bash
# Login to Azure
az login

# Create resource group
az group create --name mcp-server-rg --location eastus

# Build and push to Azure Container Registry
az acr create --resource-group mcp-server-rg --name mcpserveracr --sku Basic
az acr login --name mcpserveracr

# Build and tag image
docker build -t mcpserveracr.azurecr.io/dummy-mcp-server:latest .
docker push mcpserveracr.azurecr.io/dummy-mcp-server:latest

# Deploy to Container Instance
az container create \
  --resource-group mcp-server-rg \
  --name mcp-server-container \
  --image mcpserveracr.azurecr.io/dummy-mcp-server:latest \
  --dns-name-label mcp-server-unique \
  --ports 8000 \
  --environment-variables PORT=8000 \
  --registry-login-server mcpserveracr.azurecr.io \
  --registry-username mcpserveracr \
  --registry-password $(az acr credential show --name mcpserveracr --query "passwords[0].value" -o tsv)

# Get public IP
az container show --resource-group mcp-server-rg --name mcp-server-container --query ipAddress.fqdn
```

---

### Option 2: Azure App Service (Web App for Containers)
**Best for:** Production deployments, auto-scaling, managed SSL

#### Deploy Steps
```bash
# Login to Azure
az login

# Create resource group
az group create --name mcp-server-rg --location eastus

# Create Azure Container Registry
az acr create --resource-group mcp-server-rg --name mcpserveracr --sku Basic
az acr login --name mcpserveracr

# Build and push image
docker build -t mcpserveracr.azurecr.io/dummy-mcp-server:latest .
docker push mcpserveracr.azurecr.io/dummy-mcp-server:latest

# Create App Service Plan
az appservice plan create \
  --name mcp-server-plan \
  --resource-group mcp-server-rg \
  --is-linux \
  --sku B1

# Create Web App
az webapp create \
  --resource-group mcp-server-rg \
  --plan mcp-server-plan \
  --name mcp-server-app-unique \
  --deployment-container-image-name mcpserveracr.azurecr.io/dummy-mcp-server:latest

# Configure registry credentials
az webapp config container set \
  --name mcp-server-app-unique \
  --resource-group mcp-server-rg \
  --docker-custom-image-name mcpserveracr.azurecr.io/dummy-mcp-server:latest \
  --docker-registry-server-url https://mcpserveracr.azurecr.io \
  --docker-registry-server-user mcpserveracr \
  --docker-registry-server-password $(az acr credential show --name mcpserveracr --query "passwords[0].value" -o tsv)

# Set environment variables
az webapp config appsettings set \
  --resource-group mcp-server-rg \
  --name mcp-server-app-unique \
  --settings PORT=8000 WEBSITES_PORT=8000

# Your app will be available at: https://mcp-server-app-unique.azurewebsites.net
```

---

### Option 3: Using Docker Hub (Alternative to ACR)

```bash
# Build and tag
docker build -t yourusername/dummy-mcp-server:latest .

# Login to Docker Hub
docker login

# Push to Docker Hub
docker push yourusername/dummy-mcp-server:latest

# Deploy to Azure Container Instance (using Docker Hub)
az container create \
  --resource-group mcp-server-rg \
  --name mcp-server-container \
  --image yourusername/dummy-mcp-server:latest \
  --dns-name-label mcp-server-unique \
  --ports 8000 \
  --environment-variables PORT=8000
```

---

## Local Testing

```bash
# Build the image
docker build -t dummy-mcp-server .

# Run locally
docker run -p 8000:8000 dummy-mcp-server

# Test in another terminal
curl http://localhost:8000
```

---

## Environment Variables

Set these in Azure App Settings or Container Instance environment variables:

- `PORT` - Server port (default: 8000)
- Add any other configuration needed by your MCP server

---

## Security Considerations

1. **Update Allowed Hosts**: Modify `server.py` to include your Azure domain:
   ```python
   allowed_hosts=[
       "your-app-name.azurewebsites.net",
       "your-container.eastus.azurecontainer.io",
       "127.0.0.1:*",
       "localhost:*",
   ]
   ```

2. **Use Managed Identities**: For production, use Azure Managed Identity instead of registry passwords

3. **Enable HTTPS**: App Service provides free SSL; for ACI, use Azure Application Gateway

4. **Secrets Management**: Use Azure Key Vault for sensitive configuration

---

## Monitoring

```bash
# View logs (App Service)
az webapp log tail --name mcp-server-app-unique --resource-group mcp-server-rg

# View logs (Container Instance)
az container logs --resource-group mcp-server-rg --name mcp-server-container
```

---

## Cleanup Resources

```bash
# Delete entire resource group (removes all resources)
az group delete --name mcp-server-rg --yes --no-wait
```

---

## Troubleshooting

**Container won't start:**
- Check logs using commands above
- Verify PORT environment variable is set
- Ensure `server.py` binds to `0.0.0.0` (not `127.0.0.1`)

**Cannot access server:**
- Check firewall/NSG rules
- Verify allowed_hosts configuration in server.py
- Confirm container is running: `az container show ...`

**Build fails:**
- Verify `requirements.txt` has all dependencies
- Check Docker daemon is running
- Ensure you're logged into ACR/Docker Hub

---

## Cost Estimation

- **Azure Container Instances (B1)**: ~$10-30/month
- **App Service (B1)**: ~$13/month
- **Container Registry (Basic)**: ~$5/month

---

## Next Steps

- Set up CI/CD with GitHub Actions or Azure DevOps
- Configure custom domain and SSL certificate
- Implement health checks and auto-scaling
- Add Application Insights for monitoring