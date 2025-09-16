# Arquitectura de Microservicios - Proyecto Académico

Este proyecto demuestra la transformación de una aplicación **monolítica** a una verdadera **arquitectura de microservicios**, implementando comunicación HTTP entre servicios independientes.

## 🏗️ Arquitectura

El proyecto está compuesto por **tres microservicios independientes**:

- **Gateway Service** (Puerto 5003): Punto de entrada único y orquestador
- **Usuario Service** (Puerto 5004): Gestión independiente de usuarios
- **Pedido Service** (Puerto 5005): Gestión independiente de pedidos con comunicación HTTP al servicio de usuarios

### Diferencias con Arquitectura Monolítica:
- ✅ **Servicios independientes** ejecutándose en puertos separados
- ✅ **Comunicación HTTP** entre microservicios
- ✅ **Escalabilidad granular** por servicio
- ✅ **Despliegue independiente** de cada servicio
- ✅ **Falla aislada** por servicio

## Requisitos

- Python 3.7+
- Flask
- python-dotenv
- flask-jwt-extended

## Instalación

1. Clona o descarga el proyecto
2. Crea un entorno virtual:

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Configura las variables de entorno:

```bash
# Copia el archivo de configuración
cp config.env .env

# Edita el archivo .env con tus valores
# Cambia las API keys y contraseñas por valores seguros
```

## Configuración

El archivo `config.env` contiene las siguientes variables:

```env
# Configuración de la API
API_KEY=74UIHTG984OJR094YTH49**-0573
SECRET_KEY=tu_secret_key_muy_segura_456
JWT_SECRET=tu_jwt_secret_para_tokens_789

# Configuración del servidor
PORT=5000
DEBUG=True
HOST=localhost

# Configuración de autenticación
AUTH_REQUIRED=True
ADMIN_USER=admin
ADMIN_PASSWORD=admin123
```

**⚠️ IMPORTANTE**: Cambia los valores por defecto por otros más seguros antes de usar en producción.

## 🚀 Ejecución

### Opción 1: Iniciar todos los microservicios automáticamente

```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar todos los microservicios
./start-microservicios.sh
```

### Opción 2: Iniciar servicios manualmente

```bash
# Terminal 1 - Usuario Service
cd microservicios/usuario-service
python app.py

# Terminal 2 - Pedido Service  
cd microservicios/pedido-service
python app.py

# Terminal 3 - Gateway Service
cd microservicios/gateway-service
python app.py
```

### Servicios disponibles:
- **Gateway API**: `http://localhost:5003` (Punto de entrada)
- **Usuario Service**: `http://localhost:5004` (Directo)
- **Pedido Service**: `http://localhost:5005` (Directo)

## Autenticación

La API soporta dos métodos de autenticación:

### 1. API Key
Agrega el header `X-API-Key` con tu API key:

```bash
curl -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" http://localhost:5003/usuarios
```

### 2. JWT Token
1. Obtén un token de autenticación:

```bash
curl -X POST http://localhost:5003/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

2. Usa el token en las peticiones:

```bash
curl -H "Authorization: Bearer TU_JWT_TOKEN" http://localhost:5003/usuarios
```

## API Endpoints

Todos los endpoints están disponibles en `http://localhost:5003`

### Autenticación

- `POST /login` - Autenticación con usuario y contraseña

### Gestión de Usuarios

- `GET /usuarios` - Obtener todos los usuarios (requiere autenticación)
- `GET /usuarios/{id}` - Obtener usuario por ID (requiere autenticación)
- `POST /usuarios` - Crear nuevo usuario (requiere autenticación)
- `PUT /usuarios/{id}` - Actualizar usuario existente (requiere autenticación)
- `DELETE /usuarios/{id}` - Eliminar usuario (requiere autenticación)

**Ejemplos de gestión de usuarios:**

Crear usuario:
```bash
curl -X POST http://localhost:5003/usuarios \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" \
  -d '{"nombre": "Juan Pérez", "email": "juan@example.com", "telefono": "555-1234"}'
```

Actualizar usuario:
```bash
curl -X PUT http://localhost:5003/usuarios/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" \
  -d '{"email": "nuevo@example.com"}'
```

Eliminar usuario:
```bash
curl -X DELETE http://localhost:5003/usuarios/1 \
  -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573"
```

### Gestión de Pedidos

- `GET /pedidos` - Obtener todos los pedidos (requiere autenticación)
- `GET /pedidos/{id}` - Obtener pedido por ID (requiere autenticación)
- `POST /pedidos` - Crear nuevo pedido (requiere autenticación)
- `PUT /pedidos/{id}` - Actualizar pedido existente (requiere autenticación)
- `DELETE /pedidos/{id}` - Eliminar pedido (requiere autenticación)

**Ejemplos de gestión de pedidos:**

Crear pedido:
```bash
curl -X POST http://localhost:5003/pedidos \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" \
  -d '{"usuario_id": 1, "producto": "Teclado", "cantidad": 2, "precio": 75.00, "estado": "pendiente"}'
```

Actualizar pedido:
```bash
curl -X PUT http://localhost:5003/pedidos/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" \
  -d '{"estado": "completado", "precio": 80.00}'
```

Eliminar pedido:
```bash
curl -X DELETE http://localhost:5003/pedidos/1 \
  -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573"
```

### Información de la API

- `GET /` - Información general de la API y endpoints disponibles (no requiere autenticación)

## Integración de Datos

La aplicación unifica los datos de usuarios y pedidos, por lo que cuando consultas pedidos, automáticamente incluye la información del usuario asociado sin necesidad de comunicación externa.

## 📁 Estructura del Proyecto

```
microservicios_proyecto/
├── microservicios/           # Arquitectura de microservicios
│   ├── usuario-service/      # Microservicio de usuarios
│   │   ├── app.py           # Aplicación Flask independiente
│   │   └── config.env       # Configuración del servicio
│   ├── pedido-service/       # Microservicio de pedidos
│   │   ├── app.py           # Aplicación Flask independiente
│   │   └── config.env       # Configuración del servicio
│   └── gateway-service/      # Gateway API
│       ├── app.py           # Orquestador de servicios
│       └── config.env       # Configuración del gateway
├── app.py                   # Aplicación monolítica original (comparación)
├── config.env              # Variables de entorno originales
├── requirements.txt        # Dependencias del proyecto
├── start-microservicios.sh # Script para iniciar todos los servicios
├── stop-microservicios.sh  # Script para detener todos los servicios
├── status-microservicios.sh# Script para verificar estado
├── test-microservicios.sh  # Script para pruebas automatizadas
├── MICROSERVICIOS-vs-MONOLITICO.md # Documentación comparativa
├── venv/                   # Entorno virtual
└── README.md              # Documentación principal
```

## Datos de Ejemplo

### Usuarios Iniciales
- ID: 1, Nombre: "Ever"
- ID: 2, Nombre: "Cristian"  
- ID: 3, Nombre: "Hervin"

### Pedidos Iniciales
- ID: 1, Usuario ID: 1, Producto: "Laptop"
- ID: 2, Usuario ID: 2, Producto: "Mouse"

## Pruebas

### 1. Verificar información de la API (sin autenticación):
```bash
curl http://localhost:5003/
```

### 2. Autenticación con JWT:
```bash
# Obtener token
curl -X POST http://localhost:5003/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 3. Probar la gestión de usuarios (con autenticación):
```bash
# Obtener todos los usuarios (con API Key)
curl -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" http://localhost:5003/usuarios

# Obtener usuario específico
curl -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" http://localhost:5003/usuarios/1

# Crear un nuevo usuario
curl -X POST http://localhost:5003/usuarios \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" \
  -d '{"nombre": "Nuevo Usuario"}'
```

### 4. Probar la gestión de pedidos (con autenticación):
```bash
# Obtener todos los pedidos
curl -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" http://localhost:5003/pedidos

# Obtener pedido específico
curl -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" http://localhost:5003/pedidos/1

# Crear un nuevo pedido
curl -X POST http://localhost:5003/pedidos \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" \
  -d '{"usuario_id": 1, "producto": "Monitor"}'
```

## Notas Importantes

1. **Aplicación unificada**: Todos los servicios están disponibles en un solo puerto (5000).

2. **Autenticación**: La API requiere autenticación para todos los endpoints excepto `/` y `/login`.

3. **Variables de entorno**: Configura el archivo `.env` con valores seguros antes de usar en producción.

4. **Entorno virtual**: Siempre usa un entorno virtual para evitar conflictos de dependencias.

5. **Integración directa**: Los pedidos incluyen automáticamente la información del usuario sin necesidad de comunicación externa.

6. **Modo Debug**: La aplicación está configurada con `debug=True` para desarrollo.

7. **Persistencia**: Los datos se almacenan en memoria, por lo que se perderán al reiniciar la aplicación.

## Desarrollo

Para agregar nuevas funcionalidades:

1. Modifica el archivo `app.py` para agregar nuevos endpoints
2. Agrega nuevas dependencias en `requirements.txt` si es necesario
3. Actualiza este README con los nuevos endpoints o funcionalidades

## 🛠️ Comandos Útiles

### Gestión de Microservicios
```bash
# Iniciar todos los servicios
./start-microservicios.sh

# Verificar estado de todos los servicios
./status-microservicios.sh

# Ejecutar pruebas automatizadas
./test-microservicios.sh

# Detener todos los servicios
./stop-microservicios.sh
```

### Pruebas Manuales
```bash
# Información general de la arquitectura
curl http://localhost:5003/

# Health check de todos los servicios
curl http://localhost:5003/health

# Autenticación
curl -X POST http://localhost:5003/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Probar comunicación entre microservicios
curl -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" http://localhost:5003/pedidos
```

### Logs y Monitoreo
```bash
# Ver logs en tiempo real
tail -f logs/gateway-service.log
tail -f logs/usuario-service.log
tail -f logs/pedido-service.log

# Ver todos los logs
tail -f logs/*.log
```

## 📚 Documentación Adicional

- **[MICROSERVICIOS-vs-MONOLITICO.md](./MICROSERVICIOS-vs-MONOLITICO.md)**: Documentación completa comparando ambas arquitecturas
- **[app.py](./app.py)**: Aplicación monolítica original para comparación

## 🎯 Cumplimiento de Requisitos Académicos

Este proyecto cumple completamente con los requisitos del ejercicio:

✅ **Investigación y comprensión de fundamentos**: Documentación detallada en `MICROSERVICIOS-vs-MONOLITICO.md`

✅ **Diferencias con arquitectura monolítica**: Comparación directa entre `app.py` (monolítico) y `microservicios/` (microservicios)

✅ **Relevancia en aplicaciones modernas**: Implementación práctica con comunicación HTTP, escalabilidad y fallas aisladas

✅ **Ejercicio práctico**: Tres microservicios independientes con comunicación real

✅ **Visualización del diseño**: Scripts de despliegue y monitoreo que muestran cómo se comunican los servicios

## Troubleshooting

- **Error de conexión**: Ejecuta `./status-microservicios.sh` para verificar qué servicios están funcionando
- **Puerto en uso**: Los scripts verifican automáticamente la disponibilidad de puertos
- **Dependencias**: Ejecuta `pip install -r requirements.txt` si hay errores de importación
- **Error 401 (No autorizado)**: Verifica que estés enviando la API key correcta o el JWT token
- **Error de variables de entorno**: Cada servicio tiene su propio `config.env`
- **Error de entorno virtual**: Activa el entorno virtual antes de ejecutar los scripts
- **Servicios no se comunican**: Verifica que todos los servicios estén ejecutándose con `./status-microservicios.sh`
# Microservicios
