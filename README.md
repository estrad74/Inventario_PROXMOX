INTRODUCCIÓN
Proyecto para sincronización de inventario en Ansible AWX tomando como fuente PROXMOX.

Se utiliza como fuente de inventario el plugin community.general.proxmox, el cual se
indica en el fichero requirements.yml

El fichero proxmox.yml contiene la configuración del plugin para usar credenciales
almacenadas en AWX y recopilar facts y etiquetas de las máquinas. 

El plugin genera automáticamente varios grupos de hosts basándose en varios criterios:
nodos del datacenter, tipos de elementos (máquinas virtuales y contenedores) y elementos
encendidos o apagados.

INSTRUCCIONES

1. Instalar la colección de Proxmox para Ansible: primero, necesitamos asegurarnos de que AWX tenga acceso a la colección de Proxmox:

# Conectarse al pod de AWX
kubectl exec -it $(kubectl get pods -n awx -l "app.kubernetes.io/component=awx" -o jsonpath="{.items[0].metadata.name}") -n awx -- bash

# Instalar la colección
ansible-galaxy collection install community.general

Si no se consigue instalar la colección no pasa nada, la añadiremos posteriormente en el fichero requirements.yml del proyecto.

2. Crear un Proyecto en AWX con script de inventario para Proxmox:

Creamos un nuevo repositorio Git (p.e., en GitHub) con el siguiente contenido:

- Fichero proxmox.yml (es necesario que el nombre del fichero termine en *proxmox.yml o *proxmox.yaml):
- Fichero requirements.yml.

3. Crear el Proyecto en AWX:
En AWX, ir a "Projects" y hacer clic en "Add". Completar los siguientes campos:
Name: Proxmox Inventory Script
Organization: es opcional
SCM Type: Git
SCM URL: URL del repositorio Git
SCM Branch/Tag/Commit: main (o la rama que contenga los scripts)
Control Source Credential: asignar aquí una credencial de tipo source control que hayamos creado previamente con los datos del repositorio de Github (en contraseña indicar el token del repositorio Github)
Update Revision on Launch: Activado

Guardar el proyecto y sincronizar.

4. Crear el Tipo de Credencial Personalizado para Proxmox:
Ir a "Credential Types" y hacer clic en "Add". Completar los siguientes campos:
	Name: Proxmox Credential Type
	Description: Credenciales para acceder a Proxmox VE API
	Input Configuration:
		fields:
		  - id: proxmox_host
		    type: string
		    label: Proxmox Host
		  - id: proxmox_user
		    type: string
		    label: Proxmox User
		  - id: proxmox_password
		    type: string
		    label: Proxmox Password
		    secret: true
		  - id: proxmox_verify_ssl
		    type: boolean
		    label: Verify SSL
		    default: false
		required:
		  - proxmox_host
		  - proxmox_user
		  - proxmox_password

	Injector Configuration:
		env:
		  PROXMOX_HOST: '{{ proxmox_host }}'
		  PROXMOX_USER: '{{ proxmox_user }}'
		  PROXMOX_PASSWORD: '{{ proxmox_password }}'
		  PROXMOX_VERIFY_SSL: '{{ proxmox_verify_ssl }}'

Guardar el tipo de credencial.

5. Crear la credencial Proxmox:
Ir a "Credentials" y hacer clic en "Add". Completar los siguientes campos:
	Name: Proxmox Credential
	Organization: es opcional.
	Credential Type: Proxmox Credential Type (creado antes)
	Proxmox Host: La dirección IP o FQDN del servidor Proxmox
	Proxmox User: usuario de Proxmox (normalmente root@pam)
	Proxmox Password: contraseña del usuario de Proxmox
	Verify SSL: Desmarcado (a menos que se usen certificados válidos)
Guardar la credencial.

6. Crear el inventario:
Ir a "Inventories" y hacer clic en "Add" → "Add Inventory". Completar los siguientes campos:
	Name: Proxmox Inventory
	Organization: es opcional.
Guardar el inventario
Hacer clic en el inventario y luego en "Sources"
Hacer clic en "Add" y completar:
	Name: Proxmox Source
	Source: Sourced from a Project
	Project: Proxmox Inventory Script (creado anteriormente)
	Inventory File: / (project root)
	Credential: Mi Proxmox (creada anteriormente)

Guardar la fuente y hacer clic en "Start Sync Process" para probar la sincronización

Si todo está configurado correctamente, deberían verse las VMs de Proxmox aparecer en el inventario, organizadas en grupos como "proxmox_vms", "running_vms", y "stopped_vms".




