from flask import Flask, jsonify, request, render_template
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from dotenv import load_dotenv
from functools import wraps
import os
import requests

# Cargar variables de entorno
load_dotenv('config.env')

app = Flask(__name__)

# Configuración de JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'fallback_secret_key')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret')
jwt = JWTManager(app)

# Variables de configuración
API_KEY = os.getenv('API_KEY')
AUTH_REQUIRED = os.getenv('AUTH_REQUIRED', 'False').lower() == 'true'
ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# URLs de los microservicios
USUARIO_SERVICE_URL = os.getenv('USUARIO_SERVICE_URL', 'http://localhost:5004')
PEDIDO_SERVICE_URL = os.getenv('PEDIDO_SERVICE_URL', 'http://localhost:5005')

# ===== FUNCIONES DE AUTENTICACIÓN =====

def verificar_api_key():
    """Verificar API key en headers"""
    if not AUTH_REQUIRED:
        return True
    
    api_key = request.headers.get('X-API-Key')
    return api_key == API_KEY

def verificar_autenticacion():
    """Verificar autenticación (API key o JWT)"""
    if not AUTH_REQUIRED:
        return True
    
    # Verificar API key
    if verificar_api_key():
        print("✅ [GATEWAY] Autenticación exitosa con API Key")
        return True
    
    # Verificar JWT token
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if identity:
            print(f"✅ [GATEWAY] Autenticación exitosa con JWT para usuario: {identity}")
            return True
    except Exception as e:
        print(f"❌ [GATEWAY] Error en autenticación JWT: {e}")
    
    print("❌ [GATEWAY] Autenticación fallida")
    return False

def requiere_autenticacion(f):
    """Decorador para requerir autenticación en endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not verificar_autenticacion():
            return jsonify({
                'error': 'No autorizado',
                'mensaje': 'Se requiere autenticación válida (API Key o JWT Token)',
                'codigo': 401,
                'servicio': 'gateway-service'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# ===== FUNCIONES DE COMUNICACIÓN CON MICROSERVICIOS =====

def hacer_peticion_microservicio(service_url, endpoint, method='GET', data=None, headers=None):
    """Hacer petición a un microservicio"""
    try:
        url = f"{service_url}{endpoint}"
        
        # Preparar headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Agregar autenticación si es requerida
        if AUTH_REQUIRED and API_KEY:
            request_headers['X-API-Key'] = API_KEY
        
        print(f"🔄 [GATEWAY] Enviando {method} a {url}")
        
        if method == 'GET':
            response = requests.get(url, headers=request_headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=request_headers, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=request_headers, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=request_headers, timeout=10)
        
        print(f"📡 [GATEWAY] Respuesta de {service_url}: {response.status_code}")
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"❌ [GATEWAY] Error comunicándose con {service_url}: {e}")
        return None

def verificar_salud_servicios():
    """Verificar el estado de todos los microservicios"""
    servicios_status = {}
    
    # Verificar usuario-service
    try:
        response = requests.get(f"{USUARIO_SERVICE_URL}/health", timeout=5)
        servicios_status['usuario-service'] = {
            'estado': 'healthy' if response.status_code == 200 else 'unhealthy',
            'url': USUARIO_SERVICE_URL,
            'codigo': response.status_code
        }
    except:
        servicios_status['usuario-service'] = {
            'estado': 'unreachable',
            'url': USUARIO_SERVICE_URL,
            'error': 'No se pudo conectar'
        }
    
    # Verificar pedido-service
    try:
        response = requests.get(f"{PEDIDO_SERVICE_URL}/health", timeout=5)
        servicios_status['pedido-service'] = {
            'estado': 'healthy' if response.status_code == 200 else 'unhealthy',
            'url': PEDIDO_SERVICE_URL,
            'codigo': response.status_code
        }
    except:
        servicios_status['pedido-service'] = {
            'estado': 'unreachable',
            'url': PEDIDO_SERVICE_URL,
            'error': 'No se pudo conectar'
        }
    
    return servicios_status

# ===== RUTAS DEL GATEWAY =====

@app.route("/", methods=["GET"])
def index():
    """Página principal con información de la arquitectura de microservicios"""
    servicios_status = verificar_salud_servicios()
    
    return jsonify({
        "mensaje": "Gateway API - Arquitectura de Microservicios",
        "arquitectura": "microservicios",
        "gateway": {
            "puerto": os.getenv('PORT', 5003),
            "version": "1.0.0"
        },
        "microservicios": {
            "usuario-service": {
                "url": USUARIO_SERVICE_URL,
                "descripcion": "Gestión de usuarios",
                "endpoints": [
                    "GET /usuarios - Obtener todos los usuarios",
                    "GET /usuarios/{id} - Obtener usuario por ID",
                    "POST /usuarios - Crear nuevo usuario",
                    "PUT /usuarios/{id} - Actualizar usuario",
                    "DELETE /usuarios/{id} - Eliminar usuario"
                ]
            },
            "pedido-service": {
                "url": PEDIDO_SERVICE_URL,
                "descripcion": "Gestión de pedidos",
                "endpoints": [
                    "GET /pedidos - Obtener todos los pedidos",
                    "GET /pedidos/{id} - Obtener pedido por ID",
                    "POST /pedidos - Crear nuevo pedido",
                    "PUT /pedidos/{id} - Actualizar pedido",
                    "DELETE /pedidos/{id} - Eliminar pedido"
                ]
            }
        },
        "estado_servicios": servicios_status,
        "autenticacion_requerida": AUTH_REQUIRED,
        "autenticacion": {
            "metodos": [
                "API Key: Agregar header 'X-API-Key' con tu API key",
                "JWT Token: Usar el token obtenido del endpoint /login"
            ]
        },
        "diferencias_monolitico": {
            "ventajas_microservicios": [
                "Servicios independientes y escalables",
                "Comunicación HTTP entre servicios",
                "Despliegue independiente",
                "Tecnologías diferentes por servicio",
                "Falla aislada por servicio"
            ],
            "comunicacion": "HTTP REST entre microservicios"
        }
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Health check del gateway y todos los servicios"""
    servicios_status = verificar_salud_servicios()
    
    all_healthy = all(
        status.get('estado') == 'healthy' 
        for status in servicios_status.values()
    )
    
    return jsonify({
        "gateway": "healthy",
        "timestamp": str(os.popen('date').read().strip()),
        "microservicios": servicios_status,
        "overall_status": "healthy" if all_healthy else "degraded"
    })

@app.route("/login", methods=["POST"])
def login():
    """Endpoint para autenticación centralizada"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    print(f"🔐 [GATEWAY] Intento de login para usuario: {username}")
    
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        access_token = create_access_token(identity=username)
        print(f"✅ [GATEWAY] Login exitoso para: {username}")
        return jsonify({
            'access_token': access_token,
            'message': 'Login exitoso',
            'servicio': 'gateway-service'
        }), 200
    else:
        print(f"❌ [GATEWAY] Login fallido para: {username}")
        return jsonify({'error': 'Credenciales inválidas'}), 401

# ===== PROXY A MICROSERVICIO DE USUARIOS =====

@app.route("/usuarios", methods=["GET"])
@requiere_autenticacion
def proxy_obtener_usuarios():
    """Proxy para obtener usuarios desde usuario-service"""
    print("🔄 [GATEWAY] Proxy: Obteniendo usuarios desde usuario-service")
    response = hacer_peticion_microservicio(USUARIO_SERVICE_URL, "/usuarios")
    
    if response and response.status_code == 200:
        data = response.json()
        data['gateway'] = True
        data['microservicio_original'] = 'usuario-service'
        return jsonify(data), 200
    else:
        return jsonify({
            'error': 'Error comunicándose con usuario-service',
            'gateway': True
        }), 503

@app.route("/usuarios/<int:id_usuario>", methods=["GET"])
@requiere_autenticacion
def proxy_obtener_usuario(id_usuario):
    """Proxy para obtener usuario específico desde usuario-service"""
    print(f"🔄 [GATEWAY] Proxy: Obteniendo usuario {id_usuario} desde usuario-service")
    response = hacer_peticion_microservicio(USUARIO_SERVICE_URL, f"/usuarios/{id_usuario}")
    
    if response:
        if response.status_code == 200:
            data = response.json()
            data['gateway'] = True
            data['microservicio_original'] = 'usuario-service'
            return jsonify(data), 200
        else:
            return jsonify(response.json()), response.status_code
    else:
        return jsonify({
            'error': 'Error comunicándose con usuario-service',
            'gateway': True
        }), 503

@app.route("/usuarios", methods=["POST"])
@requiere_autenticacion
def proxy_crear_usuario():
    """Proxy para crear usuario en usuario-service"""
    data = request.get_json()
    print(f"🔄 [GATEWAY] Proxy: Creando usuario en usuario-service")
    response = hacer_peticion_microservicio(USUARIO_SERVICE_URL, "/usuarios", 'POST', data)
    
    if response:
        response_data = response.json()
        response_data['gateway'] = True
        response_data['microservicio_original'] = 'usuario-service'
        return jsonify(response_data), response.status_code
    else:
        return jsonify({
            'error': 'Error comunicándose con usuario-service',
            'gateway': True
        }), 503

@app.route("/usuarios/<int:id_usuario>", methods=["PUT"])
@requiere_autenticacion
def proxy_actualizar_usuario(id_usuario):
    """Proxy para actualizar usuario en usuario-service"""
    data = request.get_json()
    print(f"🔄 [GATEWAY] Proxy: Actualizando usuario {id_usuario} en usuario-service")
    response = hacer_peticion_microservicio(USUARIO_SERVICE_URL, f"/usuarios/{id_usuario}", 'PUT', data)
    
    if response:
        response_data = response.json()
        response_data['gateway'] = True
        response_data['microservicio_original'] = 'usuario-service'
        return jsonify(response_data), response.status_code
    else:
        return jsonify({
            'error': 'Error comunicándose con usuario-service',
            'gateway': True
        }), 503

@app.route("/usuarios/<int:id_usuario>", methods=["DELETE"])
@requiere_autenticacion
def proxy_eliminar_usuario(id_usuario):
    """Proxy para eliminar usuario en usuario-service"""
    print(f"🔄 [GATEWAY] Proxy: Eliminando usuario {id_usuario} en usuario-service")
    response = hacer_peticion_microservicio(USUARIO_SERVICE_URL, f"/usuarios/{id_usuario}", 'DELETE')
    
    if response:
        response_data = response.json()
        response_data['gateway'] = True
        response_data['microservicio_original'] = 'usuario-service'
        return jsonify(response_data), response.status_code
    else:
        return jsonify({
            'error': 'Error comunicándose con usuario-service',
            'gateway': True
        }), 503

# ===== PROXY A MICROSERVICIO DE PEDIDOS =====

@app.route("/pedidos", methods=["GET"])
@requiere_autenticacion
def proxy_obtener_pedidos():
    """Proxy para obtener pedidos desde pedido-service"""
    print("🔄 [GATEWAY] Proxy: Obteniendo pedidos desde pedido-service")
    response = hacer_peticion_microservicio(PEDIDO_SERVICE_URL, "/pedidos")
    
    if response and response.status_code == 200:
        data = response.json()
        data['gateway'] = True
        data['microservicio_original'] = 'pedido-service'
        return jsonify(data), 200
    else:
        return jsonify({
            'error': 'Error comunicándose con pedido-service',
            'gateway': True
        }), 503

@app.route("/pedidos/<int:id_pedido>", methods=["GET"])
@requiere_autenticacion
def proxy_obtener_pedido(id_pedido):
    """Proxy para obtener pedido específico desde pedido-service"""
    print(f"🔄 [GATEWAY] Proxy: Obteniendo pedido {id_pedido} desde pedido-service")
    response = hacer_peticion_microservicio(PEDIDO_SERVICE_URL, f"/pedidos/{id_pedido}")
    
    if response:
        response_data = response.json()
        response_data['gateway'] = True
        response_data['microservicio_original'] = 'pedido-service'
        return jsonify(response_data), response.status_code
    else:
        return jsonify({
            'error': 'Error comunicándose con pedido-service',
            'gateway': True
        }), 503

@app.route("/pedidos", methods=["POST"])
@requiere_autenticacion
def proxy_crear_pedido():
    """Proxy para crear pedido en pedido-service"""
    data = request.get_json()
    print(f"🔄 [GATEWAY] Proxy: Creando pedido en pedido-service")
    response = hacer_peticion_microservicio(PEDIDO_SERVICE_URL, "/pedidos", 'POST', data)
    
    if response:
        response_data = response.json()
        response_data['gateway'] = True
        response_data['microservicio_original'] = 'pedido-service'
        return jsonify(response_data), response.status_code
    else:
        return jsonify({
            'error': 'Error comunicándose con pedido-service',
            'gateway': True
        }), 503

@app.route("/pedidos/<int:id_pedido>", methods=["PUT"])
@requiere_autenticacion
def proxy_actualizar_pedido(id_pedido):
    """Proxy para actualizar pedido en pedido-service"""
    data = request.get_json()
    print(f"🔄 [GATEWAY] Proxy: Actualizando pedido {id_pedido} en pedido-service")
    response = hacer_peticion_microservicio(PEDIDO_SERVICE_URL, f"/pedidos/{id_pedido}", 'PUT', data)
    
    if response:
        response_data = response.json()
        response_data['gateway'] = True
        response_data['microservicio_original'] = 'pedido-service'
        return jsonify(response_data), response.status_code
    else:
        return jsonify({
            'error': 'Error comunicándose con pedido-service',
            'gateway': True
        }), 503

@app.route("/pedidos/<int:id_pedido>", methods=["DELETE"])
@requiere_autenticacion
def proxy_eliminar_pedido(id_pedido):
    """Proxy para eliminar pedido en pedido-service"""
    print(f"🔄 [GATEWAY] Proxy: Eliminando pedido {id_pedido} en pedido-service")
    response = hacer_peticion_microservicio(PEDIDO_SERVICE_URL, f"/pedidos/{id_pedido}", 'DELETE')
    
    if response:
        response_data = response.json()
        response_data['gateway'] = True
        response_data['microservicio_original'] = 'pedido-service'
        return jsonify(response_data), response.status_code
    else:
        return jsonify({
            'error': 'Error comunicándose con pedido-service',
            'gateway': True
        }), 503

@app.route("/db", methods=["GET"])
def database_interface():
    """Interfaz web para gestionar la base de datos"""
    return render_template('index.html')

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5003))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    host = os.getenv('HOST', 'localhost')
    
    print(f"🚀 [GATEWAY] Iniciando Gateway API en {host}:{port}")
    print(f"🔐 [GATEWAY] Autenticación requerida: {AUTH_REQUIRED}")
    print(f"🔗 [GATEWAY] Conectando con microservicios:")
    print(f"   - Usuario Service: {USUARIO_SERVICE_URL}")
    print(f"   - Pedido Service: {PEDIDO_SERVICE_URL}")
    
    app.run(host=host, port=port, debug=debug)
