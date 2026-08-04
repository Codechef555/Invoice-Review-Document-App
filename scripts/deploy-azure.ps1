# Azure CLI Deployment Script for Invoice Review Single Container App
param(
    [string]$ResourceGroup = "rg-invoice-review",
    [string]$Location = "westeurope",
    [string]$AppName = "app-invoice-review",
    [string]$AcrName = "acrinvoicereview$((Get-Random -Minimum 1000 -Maximum 9999))"
)

$ErrorActionPreference = "Stop"

Write-Host "==> Checking Azure CLI authentication..." -ForegroundColor Green
$Account = az account show 2>$null | ConvertFrom-Json
if (-not $Account) {
    Write-Host "Error: Not logged into Azure CLI. Please run 'az login' first." -ForegroundColor Red
    exit 1
}

Write-Host "Using Azure Subscription: $($Account.name) ($($Account.id))" -ForegroundColor Cyan

Write-Host "==> Creating Azure Container Registry ($AcrName) in $ResourceGroup..." -ForegroundColor Green
az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --admin-enabled true

Write-Host "==> Building and Pushing Container Image directly via Azure CLI..." -ForegroundColor Green
az acr build --registry $AcrName --image invoice-review-app:v1 .

Write-Host "==> Enabling Container Apps extension..." -ForegroundColor Green
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App

Write-Host "==> Creating Azure Container Apps Environment..." -ForegroundColor Green
az containerapp env create --name "env-invoice-review" --resource-group $ResourceGroup --location $Location

Write-Host "==> Deploying Single Container Application to Azure Container Apps..." -ForegroundColor Green
az containerapp create `
  --name $AppName `
  --resource-group $ResourceGroup `
  --environment "env-invoice-review" `
  --image "$AcrName.azurecr.io/invoice-review-app:v1" `
  --target-port 8000 `
  --ingress external

Write-Host "==> Deployment complete!" -ForegroundColor Green
$AppUrl = az containerapp show --name $AppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host "Application is live at: https://$AppUrl" -ForegroundColor Cyan
