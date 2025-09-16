from flask import Flask, jsonify, request
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
USUARIO_SERVICE_URL = os.getenv('USUARIO_SERVICE_URL', 'http://localhost:5004')

# Base de datos en memoria para pedidos
class PedidoDB:
    def __init__(self):
        self.pedidos = []
        self.next_id = 1
        # Agregar algunos pedidos iniciales
        self._crear_pedidos_iniciales()
    
    def _crear_pedidos_iniciales(self):
        """Crear pedidos iniciales para demostración"""
        pedidos_iniciales = [
            {"usuario_id": 1, "producto": "Laptop", "cantidad": 1, "precio": 1200.00, "estado": "pendiente"},
            {"usuario_id": 2, "producto": "Mouse", "cantidad": 2, "precio": 25.50, "estado": "pendiente"},
            {"usuario_id": 3, "producto": "Teclado", "cantidad": 1, "precio": 75.00, "estado": "completado"}
        ]
        
        for pedido_data in pedidos_iniciales:
            self.crear_pedido(pedido_data)
    
    def obtener_todos(self):
        """Obtener todos los pedidos"""
        return self.pedidos.copy()
    
    def obtener_por_id(self, pedido_id):
        """Obtener pedido por ID"""
        for pedido in self.pedidos:
            if pedido["id"] == pedido_id:
                return pedido
        return None
    
    def obtener_por_usuario(self, usuario_id):
        """Obtener pedidos por usuario"""
        return [pedido for pedido in self.pedidos if pedido["usuario_id"] == usuario_id]
    
    def crear_pedido(self, datos_pedido):
        """Crear nuevo pedido"""
        nuevo_pedido = {
            "id": self.next_id,
            "usuario_id": datos_pedido.get("usuario_id"),
            "producto": datos_pedido.get("producto", ""),
            "cantidad": datos_pedido.get("cantidad", 1),
            "precio": datos_pedido.get("precio", 0.00),
            "estado": datos_pedido.get("estado", "pendiente"),
            "fecha_creacion": str(os.popen('date').read().strip())
        }
        self.pedidos.append(nuevo_pedido)
        self.next_id += 1
        return nuevo_pedido
    
    def actualizar_pedido(self, pedido_id, datos_actualizados):
        """Actualizar pedido existente"""
        for i, pedido in enumerate(self.pedidos):
            if pedido["id"] == pedido_id:
                # Actualizar solo los campos proporcionados
                for campo, valor in datos_actualizados.items():
                    if campo in pedido:
                        pedido[campo] = valor
                pedido["fecha_actualizacion"] = str(os.popen('date').read().strip())
                return pedido
        return None
    
    def eliminar_pedido(self, pedido_id):
        """Eliminar pedido"""
        for i, pedido in enumerate(self.pedidos):
            if pedido["id"] == pedido_id:
                return self.pedidos.pop(i)
        return None
    
    def contar_pedidos(self):
        """Contar total de pedidos"""
        return len(self.pedidos)

# Instancia global de la base de datos
db_pedidos = PedidoDB()

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
        print("✅ [PEDIDO-SERVICE] Autenticación exitosa con API Key")
        return True
    
    # Verificar JWT token
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if identity:
            print(f"✅ [PEDIDO-SERVICE] Autenticación exitosa con JWT para usuario: {identity}")
            return True
    except Exception as e:
        print(f"❌ [PEDIDO-SERVICE] Error en autenticación JWT: {e}")
    
    print("❌ [PEDIDO-SERVICE] Autenticación fallida")
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
                'servicio': 'pedido-service'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# ===== COMUNICACIÓN CON OTROS MICROSERVICIOS =====

def obtener_usuario_desde_servicio(usuario_id):
    """Obtener información de usuario desde el microservicio de usuarios"""
    try:
        headers = {}
        if AUTH_REQUIRED and API_KEY:
            headers['X-API-Key'] = API_KEY
        
        response = requests.get(
            f"{USUARIO_SERVICE_URL}/usuarios/{usuario_id}",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ [PEDIDO-SERVICE] Usuario obtenido desde usuario-service: {data}")
            return data.get('usuario')
        else:
            print(f"❌ [PEDIDO-SERVICE] Error obteniendo usuario: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ [PEDIDO-SERVICE] Error de comunicación con usuario-service: {e}")
        return None

# ===== RUTAS DEL MICROSERVICIO DE PEDIDOS =====

@app.route("/", methods=["GET"])
def index():
    """Información del microservicio"""
    return jsonify({
        "servicio": "pedido-service",
        "version": "1.0.0",
        "descripcion": "Microservicio para gestión de pedidos",
        "puerto": os.getenv('PORT', 5005),
        "servicios_conectados": {
            "usuario-service": USUARIO_SERVICE_URL
        },
        "endpoints": {
            "pedidos": [
                "GET /pedidos - Obtener todos los pedidos",
                "GET /pedidos/{id} - Obtener pedido por ID",
                "POST /pedidos - Crear nuevo pedido",
                "PUT /pedidos/{id} - Actualizar pedido",
                "DELETE /pedidos/{id} - Eliminar pedido"
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
    # Verificar conectividad con usuario-service
    usuario_service_status = "disconnected"
    try:
        response = requests.get(f"{USUARIO_SERVICE_URL}/health", timeout=3)
        if response.status_code == 200:
            usuario_service_status = "connected"
    except:
        pass
    
    return jsonify({
        "servicio": "pedido-service",
        "estado": "healthy",
        "timestamp": str(os.popen('date').read().strip()),
        "dependencias": {
            "usuario-service": usuario_service_status
        }
    })

@app.route("/pedidos", methods=["GET"])
@requiere_autenticacion
def obtener_pedidos():
    """Obtener todos los pedidos con información del usuario"""
    pedidos = db_pedidos.obtener_todos()
    total = db_pedidos.contar_pedidos()
    print(f"📋 [PEDIDO-SERVICE] Obteniendo todos los pedidos ({total} pedidos)")
    
    pedidos_con_usuario = []
    for p in pedidos:
        # Comunicación con el microservicio de usuarios
        usuario = obtener_usuario_desde_servicio(p["usuario_id"])
        nombre_usuario = usuario["nombre"] if usuario else "Usuario no encontrado"
        
        pedidos_con_usuario.append({
            "id": p["id"],
            "producto": p["producto"],
            "cantidad": p.get("cantidad", 1),
            "precio": p.get("precio", 0.00),
            "estado": p.get("estado", "pendiente"),
            "usuario_id": p["usuario_id"],
            "usuario": nombre_usuario,
            "fecha_creacion": p.get("fecha_creacion", ""),
            "servicio_usuario": "usuario-service" if usuario else "error"
        })
    
    return jsonify({
        "pedidos": pedidos_con_usuario,
        "total": len(pedidos_con_usuario),
        "servicio": "pedido-service",
        "comunicacion_microservicios": True
    })

@app.route("/pedidos", methods=["POST"])
@requiere_autenticacion
def crear_pedido():
    """Crear nuevo pedido"""
    datos_pedido = request.get_json()
    
    # Validaciones básicas
    if not datos_pedido:
        return jsonify({
            "error": "Datos del pedido requeridos",
            "servicio": "pedido-service"
        }), 400
    
    if not datos_pedido.get("usuario_id"):
        return jsonify({
            "error": "El campo 'usuario_id' es requerido",
            "servicio": "pedido-service"
        }), 400
    
    if not datos_pedido.get("producto"):
        return jsonify({
            "error": "El campo 'producto' es requerido",
            "servicio": "pedido-service"
        }), 400
    
    # Validar que el usuario existe en el microservicio de usuarios
    usuario = obtener_usuario_desde_servicio(datos_pedido['usuario_id'])
    if not usuario:
        return jsonify({
            "error": "Usuario no encontrado",
            "usuario_id": datos_pedido['usuario_id'],
            "mensaje": "El usuario debe existir en el microservicio de usuarios",
            "servicio": "pedido-service"
        }), 400
    
    nuevo_pedido = db_pedidos.crear_pedido(datos_pedido)
    print(f"➕ [PEDIDO-SERVICE] Nuevo pedido creado: {nuevo_pedido}")
    return jsonify({
        "pedido": nuevo_pedido,
        "mensaje": "Pedido creado exitosamente",
        "servicio": "pedido-service"
    }), 201

@app.route("/pedidos/<int:id_pedido>", methods=["PUT"])
@requiere_autenticacion
def actualizar_pedido(id_pedido):
    """Actualizar pedido existente"""
    datos_actualizados = request.get_json()
    
    if not datos_actualizados:
        return jsonify({
            "error": "Datos de actualización requeridos",
            "servicio": "pedido-service"
        }), 400
    
    # Si se actualiza usuario_id, validar que el usuario existe
    if 'usuario_id' in datos_actualizados:
        usuario = obtener_usuario_desde_servicio(datos_actualizados['usuario_id'])
        if not usuario:
            return jsonify({
                "error": "Usuario no encontrado",
                "usuario_id": datos_actualizados['usuario_id'],
                "servicio": "pedido-service"
            }), 400
    
    pedido_actualizado = db_pedidos.actualizar_pedido(id_pedido, datos_actualizados)
    
    if pedido_actualizado:
        print(f"✏️ [PEDIDO-SERVICE] Pedido {id_pedido} actualizado: {pedido_actualizado}")
        return jsonify({
            "pedido": pedido_actualizado,
            "mensaje": "Pedido actualizado exitosamente",
            "servicio": "pedido-service"
        }), 200
    else:
        print(f"❌ [PEDIDO-SERVICE] Pedido con ID {id_pedido} no encontrado para actualizar")
        return jsonify({
            "error": "Pedido no encontrado",
            "id_buscado": id_pedido,
            "servicio": "pedido-service"
        }), 404

@app.route("/pedidos/<int:id_pedido>", methods=["DELETE"])
@requiere_autenticacion
def eliminar_pedido(id_pedido):
    """Eliminar pedido"""
    pedido_eliminado = db_pedidos.eliminar_pedido(id_pedido)
    
    if pedido_eliminado:
        print(f"🗑️ [PEDIDO-SERVICE] Pedido {id_pedido} eliminado: {pedido_eliminado}")
        return jsonify({
            "pedido_eliminado": pedido_eliminado,
            "mensaje": "Pedido eliminado exitosamente",
            "servicio": "pedido-service"
        }), 200
    else:
        print(f"❌ [PEDIDO-SERVICE] Pedido con ID {id_pedido} no encontrado para eliminar")
        return jsonify({
            "error": "Pedido no encontrado",
            "id_buscado": id_pedido,
            "servicio": "pedido-service"
        }), 404

@app.route("/pedidos/<int:id_pedido>", methods=["GET"])
@requiere_autenticacion
def obtener_pedido(id_pedido):
    """Obtener pedido por ID con información del usuario"""
    print(f"🔍 [PEDIDO-SERVICE] Buscando pedido con ID: {id_pedido}")
    pedido = db_pedidos.obtener_por_id(id_pedido)
    
    if pedido:
        # Comunicación con el microservicio de usuarios
        usuario = obtener_usuario_desde_servicio(pedido["usuario_id"])
        nombre_usuario = usuario["nombre"] if usuario else "Usuario no encontrado"
        
        resultado = {
            "id": pedido["id"],
            "producto": pedido["producto"],
            "cantidad": pedido.get("cantidad", 1),
            "precio": pedido.get("precio", 0.00),
            "estado": pedido.get("estado", "pendiente"),
            "usuario_id": pedido["usuario_id"],
            "usuario": nombre_usuario,
            "fecha_creacion": pedido.get("fecha_creacion", ""),
            "servicio": "pedido-service",
            "comunicacion_microservicios": True,
            "servicio_usuario": "usuario-service" if usuario else "error"
        }
        
        print(f"✅ [PEDIDO-SERVICE] Pedido encontrado: {resultado}")
        return jsonify(resultado)
    
    print(f"❌ [PEDIDO-SERVICE] Pedido con ID {id_pedido} no encontrado")
    return jsonify({
        "error": "Pedido no encontrado",
        "id_buscado": id_pedido,
        "servicio": "pedido-service"
    }), 404

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5005))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    host = os.getenv('HOST', 'localhost')
    
    print(f"🚀 [PEDIDO-SERVICE] Iniciando microservicio en {host}:{port}")
    print(f"🔐 [PEDIDO-SERVICE] Autenticación requerida: {AUTH_REQUIRED}")
    print(f"🔗 [PEDIDO-SERVICE] Conectando con usuario-service en: {USUARIO_SERVICE_URL}")
    
    app.run(host=host, port=port, debug=debug)
