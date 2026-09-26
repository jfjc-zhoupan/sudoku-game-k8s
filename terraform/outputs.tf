output "resource_group_name" {
  value       = azurerm_resource_group.main.name
}

output "aks_cluster_name" {
  value       = azurerm_kubernetes_cluster.main.name
}

output "acr_name" {
  value       = azurerm_container_registry.main.name
}

output "acr_login_server" {
  description = "ACR login server URL (for docker push)"
  value       = azurerm_container_registry.main.login_server
}

output "kube_config" {
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}