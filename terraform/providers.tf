terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=5.0.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "tfstatesudoku2026"
    container_name       = "tfstate"
    key                  = "sudoku-game-k8s.tfstate"
  }
}

provider "azurerm" {
  features {}
}

