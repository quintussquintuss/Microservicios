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

# Base de datos en memoria para usuarios
class UsuarioDB:
    def __init__(self):
        self.usuarios = []
        self.next_id = 1
        # Agregar algunos usuarios iniciales
        self._crear_usuarios_iniciales()
    
    def _crear_usuarios_iniciales(self):
        """Crear usuarios iniciales para demostración"""
        usuarios_iniciales = [
            {"nombre": "Ever", "email": "ever@example.com", "telefono": "123-456-7890"},
            {"nombre": "Cristian", "email": "cristian@example.com", "telefono": "098-765-4321"},
            {"nombre": "Hervin", "email": "hervin@example.com", "telefono": "555-123-4567"}
        ]
        
        for usuario_data in usuarios_iniciales:
            self.crear_usuario(usuario_data)
    
    def obtener_todos(self):
        """Obtener todos los usuarios"""
        return self.usuarios.copy()
    
    def obtener_por_id(self, usuario_id):
        """Obtener usuario por ID"""
        for usuario in self.usuarios:
            if usuario["id"] == usuario_id:
                return usuario
        return None
    
    def crear_usuario(self, datos_usuario):
        """Crear nuevo usuario"""
        nuevo_usuario = {
            "id": self.next_id,
            "nombre": datos_usuario.get("nombre", ""),
            "email": datos_usuario.get("email", ""),
            "telefono": datos_usuario.get("telefono", ""),
            "fecha_creacion": str(os.popen('date').read().strip())
        }
        self.usuarios.append(nuevo_usuario)
        self.next_id += 1
        return nuevo_usuario
    
    def actualizar_usuario(self, usuario_id, datos_actualizados):
        """Actualizar usuario existente"""
        for i, usuario in enumerate(self.usuarios):
            if usuario["id"] == usuario_id:
                # Actualizar solo los campos proporcionados
                for campo, valor in datos_actualizados.items():
                    if campo in usuario:
                        usuario[campo] = valor
                usuario["fecha_actualizacion"] = str(os.popen('date').read().strip())
                return usuario
        return None
    
    def eliminar_usuario(self, usuario_id):
        """Eliminar usuario"""
        for i, usuario in enumerate(self.usuarios):
            if usuario["id"] == usuario_id:
                return self.usuarios.pop(i)
        return None
    
    def contar_usuarios(self):
        """Contar total de usuarios"""
        return len(self.usuarios)

# Instancia global de la base de datos
db_usuarios = UsuarioDB()

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
        print("✅ [USUARIO-SERVICE] Autenticación exitosa con API Key")
        return True
    
    # Verificar JWT token
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if identity:
            print(f"✅ [USUARIO-SERVICE] Autenticación exitosa con JWT para usuario: {identity}")
            return True
    except Exception as e:
        print(f"❌ [USUARIO-SERVICE] Error en autenticación JWT: {e}")
    
    print("❌ [USUARIO-SERVICE] Autenticación fallida")
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
                'servicio': 'usuario-service'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# ===== RUTAS DEL MICROSERVICIO DE USUARIOS =====

@app.route("/", methods=["GET"])
def index():
    """Información del microservicio"""
    return jsonify({
        "servicio": "usuario-service",
        "version": "1.0.0",
        "descripcion": "Microservicio para gestión de usuarios",
        "puerto": os.getenv('PORT', 5004),
        "endpoints": {
            "usuarios": [
                "GET /usuarios - Obtener todos los usuarios",
                "GET /usuarios/{id} - Obtener usuario por ID",
                "POST /usuarios - Crear nuevo usuario",
                "PUT /usuarios/{id} - Actualizar usuario",
                "DELETE /usuarios/{id} - Eliminar usuario"
            ],
            "health": [
                "GET /health - Estado del servicio"
            ]
        },
        "autenticacion_requerida": AUTH_REQUIRED
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Health check del servicio"""
    return jsonify({
        "servicio": "usuario-service",
        "estado": "healthy",
        "timestamp": str(os.popen('date').read().strip())
    })

@app.route("/usuarios", methods=["GET"])
@requiere_autenticacion
def obtener_usuarios():
    """Obtener todos los usuarios"""
    usuarios = db_usuarios.obtener_todos()
    total = db_usuarios.contar_usuarios()
    print(f"📋 [USUARIO-SERVICE] Obteniendo todos los usuarios ({total} usuarios)")
    return jsonify({
        "usuarios": usuarios,
        "total": total,
        "servicio": "usuario-service"
    })

@app.route("/usuarios/<int:id_usuario>", methods=["GET"])
@requiere_autenticacion
def obtener_usuario(id_usuario):
    """Obtener usuario por ID"""
    print(f"🔍 [USUARIO-SERVICE] Buscando usuario con ID: {id_usuario}")
    usuario = db_usuarios.obtener_por_id(id_usuario)
    if usuario:
        print(f"✅ [USUARIO-SERVICE] Usuario encontrado: {usuario}")
        return jsonify({
            "usuario": usuario,
            "servicio": "usuario-service"
        })
    
    print(f"❌ [USUARIO-SERVICE] Usuario con ID {id_usuario} no encontrado")
    return jsonify({
        "error": "Usuario no encontrado",
        "id_buscado": id_usuario,
        "servicio": "usuario-service"
    }), 404

@app.route("/usuarios", methods=["POST"])
@requiere_autenticacion
def crear_usuario():
    """Crear nuevo usuario"""
    datos_usuario = request.get_json()
    
    # Validaciones básicas
    if not datos_usuario or not datos_usuario.get("nombre"):
        return jsonify({
            "error": "El campo 'nombre' es requerido",
            "servicio": "usuario-service"
        }), 400
    
    nuevo_usuario = db_usuarios.crear_usuario(datos_usuario)
    print(f"➕ [USUARIO-SERVICE] Nuevo usuario creado: {nuevo_usuario}")
    return jsonify({
        "usuario": nuevo_usuario,
        "mensaje": "Usuario creado exitosamente",
        "servicio": "usuario-service"
    }), 201

@app.route("/usuarios/<int:id_usuario>", methods=["PUT"])
@requiere_autenticacion
def actualizar_usuario(id_usuario):
    """Actualizar usuario existente"""
    datos_actualizados = request.get_json()
    
    if not datos_actualizados:
        return jsonify({
            "error": "Datos de actualización requeridos",
            "servicio": "usuario-service"
        }), 400
    
    usuario_actualizado = db_usuarios.actualizar_usuario(id_usuario, datos_actualizados)
    
    if usuario_actualizado:
        print(f"✏️ [USUARIO-SERVICE] Usuario {id_usuario} actualizado: {usuario_actualizado}")
        return jsonify({
            "usuario": usuario_actualizado,
            "mensaje": "Usuario actualizado exitosamente",
            "servicio": "usuario-service"
        }), 200
    else:
        print(f"❌ [USUARIO-SERVICE] Usuario con ID {id_usuario} no encontrado para actualizar")
        return jsonify({
            "error": "Usuario no encontrado",
            "id_buscado": id_usuario,
            "servicio": "usuario-service"
        }), 404

@app.route("/usuarios/<int:id_usuario>", methods=["DELETE"])
@requiere_autenticacion
def eliminar_usuario(id_usuario):
    """Eliminar usuario"""
    usuario_eliminado = db_usuarios.eliminar_usuario(id_usuario)
    
    if usuario_eliminado:
        print(f"🗑️ [USUARIO-SERVICE] Usuario {id_usuario} eliminado: {usuario_eliminado}")
        return jsonify({
            "usuario_eliminado": usuario_eliminado,
            "mensaje": "Usuario eliminado exitosamente",
            "servicio": "usuario-service"
        }), 200
    else:
        print(f"❌ [USUARIO-SERVICE] Usuario con ID {id_usuario} no encontrado para eliminar")
        return jsonify({
            "error": "Usuario no encontrado",
            "id_buscado": id_usuario,
            "servicio": "usuario-service"
        }), 404

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5004))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    host = os.getenv('HOST', 'localhost')
    
    print(f"🚀 [USUARIO-SERVICE] Iniciando microservicio en {host}:{port}")
    print(f"🔐 [USUARIO-SERVICE] Autenticación requerida: {AUTH_REQUIRED}")
    
    app.run(host=host, port=port, debug=debug)
