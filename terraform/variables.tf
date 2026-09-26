variable "location" {
  default     = "eastasia"
}

variable "resource_group_name" {
  default     = "rg-sudoku-game"
}

variable "acr_name" {}

variable "aks_cluster_name" {
  default     = "aks-sudoku-game"
}

variable "kubernetes_version" {
  default     = "1.30"
}

variable "node_count" {
  default     = 1
}

variable "node_vm_size" {
  default     = "Standard_D2s_v3"
}

variable "dns_prefix" {
  default     = "sudoku-game"
}