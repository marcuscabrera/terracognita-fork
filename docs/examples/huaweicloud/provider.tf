terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.36.0"
    }
  }
}

# Substitua os placeholders abaixo caso não utilize variáveis de ambiente.
# Para maior segurança, exporte TF_VAR_huaweicloud_access_key, TF_VAR_huaweicloud_secret_key
# e TF_VAR_huaweicloud_region antes de executar o Terraform. Exemplo:
#   export TF_VAR_huaweicloud_access_key="minha-ak"
#   export TF_VAR_huaweicloud_secret_key="minha-sk"
#   export TF_VAR_huaweicloud_region="sa-brazil-1"

variable "huaweicloud_access_key" {
  description = "Access Key (AK) obtida no console da Huawei Cloud em Management & Deployment > Access Credentials."
  type        = string
  sensitive   = true
  default     = ""
}

variable "huaweicloud_secret_key" {
  description = "Secret Key (SK) emparelhada com a AK, também disponível em Access Credentials."
  type        = string
  sensitive   = true
  default     = ""
}

variable "huaweicloud_region" {
  description = "Região alvo. Consulte a lista atualizada em https://developer.huaweicloud.com/intl/pt-br/endpoint."
  type        = string
  default     = ""
}

locals {
  default_huaweicloud_region     = "<sua_regiao>"
  default_huaweicloud_access_key = "<seu_access_key>"
  default_huaweicloud_secret_key = "<seu_secret_key>"
}

provider "huaweicloud" {
  # Defina explicitamente a região ou utilize TF_VAR_huaweicloud_region.
  region = coalesce(var.huaweicloud_region, local.default_huaweicloud_region)

  # Informe a Access Key (AK) criada para um usuário com permissões adequadas.
  access_key = coalesce(var.huaweicloud_access_key, local.default_huaweicloud_access_key)

  # Informe a Secret Key (SK) correspondente. Nunca versione valores reais.
  secret_key = coalesce(var.huaweicloud_secret_key, local.default_huaweicloud_secret_key)
}
