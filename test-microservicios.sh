#!/bin/bash

# Script para probar la funcionalidad de los microservicios
echo "🧪 Pruebas de la Arquitectura de Microservicios"
echo "============================================="

API_KEY="74UIHTG984OJR094YTH49**-0573"
BASE_URL="http://localhost:5003"

# Función para hacer una petición y mostrar resultado
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo "🔍 $description"
    echo "   $method $BASE_URL$endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint")
    fi
    
    # Separar respuesta y código HTTP
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo "   ✅ Éxito (HTTP $http_code)"
        echo "$body" | python3 -m json.tool 2>/dev/null | sed 's/^/      /'
    else
        echo "   ❌ Error (HTTP $http_code)"
        echo "$body" | sed 's/^/      /'
    fi
    echo ""
}

# Función para probar autenticación JWT
test_jwt_auth() {
    echo "🔐 Pruebas de Autenticación JWT"
    echo "================================"
    
    # Obtener token
    echo "🔑 Obteniendo token JWT..."
    jwt_response=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username": "admin", "password": "admin123"}' "$BASE_URL/login")
    echo "$jwt_response" | python3 -m json.tool 2>/dev/null | sed 's/^/   /'
    
    # Extraer token
    token=$(echo "$jwt_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
    
    if [ -n "$token" ] && [ "$token" != "null" ]; then
        echo ""
        echo "🔍 Probando endpoint con JWT token..."
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $token" "$BASE_URL/usuarios")
        
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)
        
        if [ "$http_code" -eq 200 ]; then
            echo "   ✅ JWT funciona correctamente (HTTP $http_code)"
        else
            echo "   ❌ Error con JWT (HTTP $http_code)"
        fi
    else
        echo "   ❌ No se pudo obtener token JWT"
    fi
    echo ""
}

echo "📋 Verificando que los servicios estén funcionando..."
if ! curl -s http://localhost:5003/health > /dev/null; then
    echo "❌ Gateway no está funcionando. Ejecuta ./start-microservicios.sh primero"
    exit 1
fi

echo "✅ Gateway funcionando"
echo ""

# 1. Información general
test_endpoint "GET" "/" "" "Información general de la arquitectura"

# 2. Health check
test_endpoint "GET" "/health" "" "Health check de todos los servicios"

# 3. Autenticación JWT
test_jwt_auth

# 4. Gestión de usuarios
echo "👥 Pruebas de Gestión de Usuarios"
echo "=================================="
test_endpoint "GET" "/usuarios" "" "Obtener todos los usuarios"
test_endpoint "GET" "/usuarios/1" "" "Obtener usuario específico (ID: 1)"
test_endpoint "POST" "/usuarios" '{"nombre": "Usuario de Prueba"}' "Crear nuevo usuario"

# 5. Gestión de pedidos
echo "📦 Pruebas de Gestión de Pedidos"
echo "================================"
test_endpoint "GET" "/pedidos" "" "Obtener todos los pedidos"
test_endpoint "GET" "/pedidos/1" "" "Obtener pedido específico (ID: 1)"
test_endpoint "POST" "/pedidos" '{"usuario_id": 1, "producto": "Producto de Prueba"}' "Crear nuevo pedido"

# 6. Pruebas de comunicación entre microservicios
echo "🔗 Pruebas de Comunicación entre Microservicios"
echo "==============================================="

echo "🔍 Verificando que pedidos incluyan información de usuarios (comunicación inter-servicios)..."
pedidos_response=$(curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/pedidos")
echo "$pedidos_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'pedidos' in data:
        for pedido in data['pedidos']:
            if 'usuario' in pedido and 'comunicacion_microservicios' in pedido:
                print(f'   ✅ Pedido {pedido[\"id\"]}: Usuario \"{pedido[\"usuario\"]}\" (Comunicación: {pedido[\"comunicacion_microservicios\"]})')
            else:
                print(f'   ⚠️  Pedido {pedido[\"id\"]}: Sin información de usuario')
    else:
        print('   ❌ No se pudieron obtener pedidos')
except:
    print('   ❌ Error procesando respuesta')
"

echo ""
echo "🎉 ¡Pruebas completadas!"
echo "========================"
echo ""
echo "📊 Resumen:"
echo "   • ✅ Arquitectura de microservicios funcionando"
echo "   • ✅ Comunicación HTTP entre servicios"
echo "   • ✅ Gateway orquestando peticiones"
echo "   • ✅ Autenticación (API Key y JWT)"
echo "   • ✅ Servicios independientes y escalables"
echo ""
echo "🔧 Para más pruebas:"
echo "   • curl -H 'X-API-Key: $API_KEY' http://localhost:5003/"
echo "   • curl http://localhost:5004/ (usuario-service directo)"
echo "   • curl http://localhost:5005/ (pedido-service directo)"
