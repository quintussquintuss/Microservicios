from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from dotenv import load_dotenv
from functools import wraps
import os

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

# Datos de usuarios
usuarios = [
    {"id": 1, "nombre": "Ever"},
    {"id": 2, "nombre": "Cristian"},
    {"id": 3, "nombre": "Hervin"}
]

# Datos de pedidos
pedidos = [
    {"id": 1, "usuario_id": 1, "producto": "Laptop"},
    {"id": 2, "usuario_id": 2, "producto": "Mouse"}
]

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
        print("✅ Autenticación exitosa con API Key")
        return True
    
    # Verificar JWT token
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if identity:
            print(f"✅ Autenticación exitosa con JWT para usuario: {identity}")
            return True
    except Exception as e:
        print(f"❌ Error en autenticación JWT: {e}")
    
    print("❌ Autenticación fallida - No se proporcionó API Key válida o JWT token")
    return False

def requiere_autenticacion(f):
    """Decorador para requerir autenticación en endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not verificar_autenticacion():
            return jsonify({
                'error': 'No autorizado',
                'mensaje': 'Se requiere autenticación válida (API Key o JWT Token)',
                'codigo': 401
            }), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["POST"])
def login():
    """Endpoint para autenticación"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        access_token = create_access_token(identity=username)
        return jsonify({
            'access_token': access_token,
            'message': 'Login exitoso'
        }), 200
    else:
        return jsonify({'error': 'Credenciales inválidas'}), 401

# ===== RUTAS DE USUARIOS =====

@app.route("/usuarios", methods=["GET"])
@requiere_autenticacion
def obtener_usuarios():
    """Obtener todos los usuarios"""
    return jsonify(usuarios)

@app.route("/usuarios/<int:id_usuario>", methods=["GET"])
@requiere_autenticacion
def obtener_usuario(id_usuario):
    """Obtener usuario por ID"""
    usuario = next((u for u in usuarios if u["id"] == id_usuario), None)
    if usuario:
        return jsonify(usuario)
    return jsonify({"error": "Usuario no encontrado"}), 404

@app.route("/usuarios", methods=["POST"])
@requiere_autenticacion
def crear_usuario():
    """Crear nuevo usuario"""
    nuevo = request.get_json()
    nuevo["id"] = len(usuarios) + 1
    usuarios.append(nuevo)
    return jsonify(nuevo), 201

# ===== RUTAS DE PEDIDOS =====

@app.route("/pedidos", methods=["GET"])
@requiere_autenticacion
def obtener_pedidos():
    """Obtener todos los pedidos con información del usuario"""
    pedidos_con_usuario = []
    for p in pedidos:
        # Buscar el usuario directamente en la lista local
        usuario = next((u for u in usuarios if u["id"] == p["usuario_id"]), None)
        nombre_usuario = usuario["nombre"] if usuario else "Usuario no encontrado"
        
        pedidos_con_usuario.append({
            "id": p["id"],
            "producto": p["producto"],
            "usuario": nombre_usuario
        })
    return jsonify(pedidos_con_usuario)

@app.route("/pedidos", methods=["POST"])
@requiere_autenticacion
def crear_pedido():
    """Crear nuevo pedido"""
    nuevo = request.get_json()
    nuevo["id"] = len(pedidos) + 1
    pedidos.append(nuevo)
    return jsonify(nuevo), 201

@app.route("/pedidos/<int:id_pedido>", methods=["GET"])
@requiere_autenticacion
def obtener_pedido(id_pedido):
    """Obtener pedido por ID"""
    pedido = next((p for p in pedidos if p["id"] == id_pedido), None)
    if pedido:
        # Buscar el usuario asociado
        usuario = next((u for u in usuarios if u["id"] == pedido["usuario_id"]), None)
        nombre_usuario = usuario["nombre"] if usuario else "Usuario no encontrado"
        
        return jsonify({
            "id": pedido["id"],
            "producto": pedido["producto"],
            "usuario_id": pedido["usuario_id"],
            "usuario": nombre_usuario
        })
    return jsonify({"error": "Pedido no encontrado"}), 404

# ===== RUTA PRINCIPAL =====

@app.route("/", methods=["GET"])
def index():
    """Página principal con información de la API"""
    return jsonify({
        "mensaje": "API de Microservicios Unificada",
        "autenticacion_requerida": AUTH_REQUIRED,
        "servicios": {
            "autenticacion": {
                "endpoints": [
                    "POST /login - Autenticación con usuario y contraseña"
                ]
            },
            "usuarios": {
                "endpoints": [
                    "GET /usuarios - Obtener todos los usuarios",
                    "GET /usuarios/{id} - Obtener usuario por ID",
                    "POST /usuarios - Crear nuevo usuario"
                ]
            },
            "pedidos": {
                "endpoints": [
                    "GET /pedidos - Obtener todos los pedidos",
                    "GET /pedidos/{id} - Obtener pedido por ID",
                    "POST /pedidos - Crear nuevo pedido"
                ]
            }
        },
        "autenticacion": {
            "metodos": [
                "API Key: Agregar header 'X-API-Key' con tu API key",
                "JWT Token: Usar el token obtenido del endpoint /login"
            ]
        }
    })

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    host = os.getenv('HOST', 'localhost')
    
    print(f"🚀 Iniciando servidor en {host}:{port}")
    print(f"🔐 Autenticación requerida: {AUTH_REQUIRED}")
    if AUTH_REQUIRED:
        print(f"🔑 API Key configurada: {'Sí' if API_KEY else 'No'}")
        print(f"👤 Usuario admin: {ADMIN_USER}")
    
    app.run(host=host, port=port, debug=debug)
