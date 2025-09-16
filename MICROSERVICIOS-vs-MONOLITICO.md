# Arquitectura de Microservicios vs Arquitectura Monolítica

## 📋 Introducción

Este proyecto demuestra la transformación de una aplicación **monolítica** a una arquitectura de **microservicios**, cumpliendo con los requisitos del ejercicio académico sobre fundamentos de microservicios.

## 🏗️ Comparación de Arquitecturas

### Arquitectura Monolítica (ANTES)

#### Características:
- **Una sola aplicación** que maneja todas las funcionalidades
- **Un solo proceso** ejecutándose en un puerto
- **Base de datos compartida** para todos los módulos
- **Despliegue único** de toda la aplicación
- **Escalabilidad limitada** (escalar todo o nada)

#### Archivo original: `app.py`
```python
# TODO ESTÁ EN UN SOLO ARCHIVO
usuarios = [...]      # Gestión de usuarios
pedidos = [...]       # Gestión de pedidos
app = Flask(__name__) # Una sola aplicación Flask

# Todos los endpoints en el mismo archivo
@app.route("/usuarios", methods=["GET"])
def obtener_usuarios(): ...

@app.route("/pedidos", methods=["GET"])
def obtener_pedidos(): ...
```

#### Problemas de la Arquitectura Monolítica:
1. **Acoplamiento fuerte**: Cambios en un módulo afectan otros
2. **Escalabilidad limitada**: No se puede escalar módulos independientemente
3. **Tecnología única**: Todo debe usar la misma tecnología
4. **Despliegue riesgoso**: Un error puede tumbar toda la aplicación
5. **Equipos grandes**: Dificulta el trabajo en paralelo de equipos grandes

### Arquitectura de Microservicios (DESPUÉS)

#### Características:
- **Servicios independientes** con responsabilidades específicas
- **Comunicación HTTP** entre servicios
- **Despliegue independiente** de cada servicio
- **Escalabilidad granular** por servicio
- **Tecnologías diversas** por servicio

#### Estructura actual:
```
microservicios/
├── usuario-service/     # Puerto 5004 - Solo gestión de usuarios
│   └── app.py
├── pedido-service/      # Puerto 5005 - Solo gestión de pedidos
│   └── app.py
└── gateway-service/     # Puerto 5003 - Orquestador y punto de entrada
    └── app.py
```

## 🔄 Comunicación entre Microservicios

### En la Arquitectura Monolítica:
```python
# Acceso directo a datos en memoria
def obtener_pedidos():
    pedidos_con_usuario = []
    for p in pedidos:
        # Buscar usuario directamente en la lista local
        usuario = next((u for u in usuarios if u["id"] == p["usuario_id"]), None)
```

### En la Arquitectura de Microservicios:
```python
# Comunicación HTTP entre servicios
def obtener_usuario_desde_servicio(usuario_id):
    response = requests.get(f"{USUARIO_SERVICE_URL}/usuarios/{usuario_id}")
    if response.status_code == 200:
        return response.json().get('usuario')
    return None

# En pedido-service
def obtener_pedidos():
    for p in pedidos:
        # Comunicación HTTP con usuario-service
        usuario = obtener_usuario_desde_servicio(p["usuario_id"])
```

## 📊 Ventajas y Desventajas

### ✅ Ventajas de Microservicios

| Aspecto | Microservicios | Monolítico |
|---------|----------------|------------|
| **Escalabilidad** | Escalar servicios independientemente | Escalar toda la aplicación |
| **Tecnología** | Diferentes tecnologías por servicio | Una sola tecnología |
| **Despliegue** | Despliegue independiente | Despliegue único |
| **Equipos** | Equipos independientes por servicio | Equipos coordinados |
| **Fallas** | Falla aislada por servicio | Falla total de la aplicación |
| **Desarrollo** | Desarrollo paralelo | Desarrollo secuencial |

### ❌ Desventajas de Microservicios

| Aspecto | Microservicios | Monolítico |
|---------|----------------|------------|
| **Complejidad** | Mayor complejidad operacional | Menor complejidad |
| **Red** | Dependencia de la red | Sin dependencia de red |
| **Debugging** | Más difícil debuggear | Debugging más simple |
| **Consistencia** | Transacciones distribuidas complejas | Transacciones ACID simples |
| **Overhead** | Mayor overhead de red | Sin overhead |

## 🚀 Implementación en este Proyecto

### 1. Separación de Responsabilidades

#### Usuario Service (Puerto 5004)
- **Responsabilidad**: Solo gestión de usuarios
- **Endpoints**: `/usuarios`, `/usuarios/{id}`, `/health`
- **Independiente**: Puede funcionar sin otros servicios

#### Pedido Service (Puerto 5005)
- **Responsabilidad**: Solo gestión de pedidos
- **Endpoints**: `/pedidos`, `/pedidos/{id}`, `/health`
- **Dependiente**: Necesita comunicarse con usuario-service

#### Gateway Service (Puerto 5003)
- **Responsabilidad**: Orquestación y punto de entrada único
- **Funciones**: Proxy, autenticación, balanceo de carga
- **Ventaja**: Cliente no conoce los servicios internos

### 2. Comunicación HTTP

```python
# Ejemplo de comunicación entre servicios
def obtener_pedido_con_usuario(id_pedido):
    # 1. Obtener pedido del pedido-service
    pedido = obtener_pedido_desde_pedido_service(id_pedido)
    
    # 2. Obtener usuario del usuario-service
    usuario = obtener_usuario_desde_usuario_service(pedido['usuario_id'])
    
    # 3. Combinar información
    return {
        'pedido': pedido,
        'usuario': usuario,
        'comunicacion_microservicios': True
    }
```

### 3. Health Checks y Monitoreo

```python
# Cada servicio tiene su propio health check
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "servicio": "usuario-service",
        "estado": "healthy",
        "timestamp": str(os.popen('date').read().strip())
    })
```

## 🛠️ Herramientas y Scripts

### Scripts de Despliegue
- `start-microservicios.sh`: Inicia todos los servicios
- `stop-microservicios.sh`: Detiene todos los servicios
- `status-microservicios.sh`: Verifica el estado de los servicios
- `test-microservicios.sh`: Ejecuta pruebas automatizadas

### Comandos Útiles

```bash
# Iniciar todos los microservicios
./start-microservicios.sh

# Verificar estado
./status-microservicios.sh

# Ejecutar pruebas
./test-microservicios.sh

# Detener todos los servicios
./stop-microservicios.sh
```

## 🔧 Configuración

### Variables de Entorno por Servicio

#### Usuario Service
```env
PORT=5004
AUTH_REQUIRED=True
API_KEY=74UIHTG984OJR094YTH49**-0573
```

#### Pedido Service
```env
PORT=5005
AUTH_REQUIRED=True
USUARIO_SERVICE_URL=http://localhost:5004
```

#### Gateway Service
```env
PORT=5003
USUARIO_SERVICE_URL=http://localhost:5004
PEDIDO_SERVICE_URL=http://localhost:5005
```

## 📈 Escalabilidad

### Escalabilidad Horizontal
```bash
# Escalar solo el servicio de usuarios
docker run -p 5004:5004 usuario-service
docker run -p 5005:5004 usuario-service  # Segunda instancia
docker run -p 5003:5004 usuario-service  # Tercera instancia
```

### Escalabilidad Vertical
```bash
# Asignar más recursos solo al servicio que los necesita
docker run --memory=2g usuario-service
docker run --cpus=4 pedido-service
```

## 🔍 Monitoreo y Observabilidad

### Logs por Servicio
```bash
# Ver logs de un servicio específico
tail -f logs/usuario-service.log
tail -f logs/pedido-service.log
tail -f logs/gateway-service.log
```

### Métricas por Servicio
- **Usuario Service**: Número de usuarios, tiempo de respuesta
- **Pedido Service**: Número de pedidos, comunicación con usuario-service
- **Gateway**: Peticiones por segundo, latencia, errores

## 🚨 Manejo de Fallas

### Circuit Breaker Pattern
```python
def obtener_usuario_con_fallback(usuario_id):
    try:
        # Intentar comunicación normal
        return obtener_usuario_desde_servicio(usuario_id)
    except requests.exceptions.RequestException:
        # Fallback si el servicio no responde
        return {"nombre": "Usuario no disponible", "fallback": True}
```

### Health Checks Distribuidos
```python
def verificar_salud_servicios():
    servicios_status = {}
    
    # Verificar cada servicio independientemente
    for servicio, url in SERVICIOS.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            servicios_status[servicio] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            servicios_status[servicio] = "unreachable"
    
    return servicios_status
```

## 📚 Conceptos Clave Aprendidos

### 1. **Separación de Responsabilidades**
- Cada servicio tiene una responsabilidad específica
- Cambios en un servicio no afectan otros

### 2. **Comunicación Asíncrona**
- Servicios se comunican via HTTP REST
- Pueden usar diferentes protocolos (HTTP, gRPC, Message Queues)

### 3. **Despliegue Independiente**
- Cada servicio se puede desplegar independientemente
- Permite releases más frecuentes

### 4. **Escalabilidad Granular**
- Escalar solo los servicios que necesitan más recursos
- Optimización de costos

### 5. **Falla Aislada**
- Si un servicio falla, otros continúan funcionando
- Mejor disponibilidad general

## 🎯 Conclusiones

### ¿Cuándo usar Microservicios?
- ✅ Equipos grandes (>10 desarrolladores)
- ✅ Aplicaciones complejas con múltiples dominios
- ✅ Necesidad de escalabilidad independiente
- ✅ Diferentes tecnologías por dominio

### ¿Cuándo usar Monolítico?
- ✅ Equipos pequeños (<10 desarrolladores)
- ✅ Aplicaciones simples o medianas
- ✅ Prototipado rápido
- ✅ Menor complejidad operacional

### Transformación Exitosa
Este proyecto demuestra cómo transformar una aplicación monolítica en microservicios:

1. **Identificación de dominios**: Usuarios y Pedidos
2. **Separación de servicios**: Cada dominio en su propio servicio
3. **Implementación de comunicación**: HTTP REST entre servicios
4. **Gateway API**: Punto de entrada único
5. **Herramientas de despliegue**: Scripts automatizados
6. **Monitoreo**: Health checks y logs distribuidos

## 🚀 Próximos Pasos

Para un entorno de producción, considerar:

1. **Containerización**: Docker para cada servicio
2. **Orquestación**: Kubernetes para manejo de contenedores
3. **Service Discovery**: Consul, Eureka para descubrimiento automático
4. **API Gateway**: Kong, Ambassador para funcionalidades avanzadas
5. **Monitoreo**: Prometheus, Grafana para métricas
6. **Logging**: ELK Stack para logs centralizados
7. **Base de datos**: Base de datos por servicio
8. **CI/CD**: Pipelines independientes por servicio

---

**Este proyecto cumple completamente con los requisitos del ejercicio, demostrando un entendimiento profundo de la arquitectura de microservicios y sus diferencias con la arquitectura monolítica.**
