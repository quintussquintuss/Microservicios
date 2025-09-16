#!/bin/bash

# Script para iniciar todos los microservicios
echo "🚀 Iniciando Arquitectura de Microservicios"
echo "============================================="

# Función para verificar si un puerto está en uso
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Puerto $1 está en uso"
        return 1
    else
        echo "✅ Puerto $1 está disponible"
        return 0
    fi
}

# Verificar puertos
echo "🔍 Verificando puertos..."
check_port 5003 || { echo "Gateway necesita puerto 5003"; exit 1; }
check_port 5004 || { echo "Usuario-service necesita puerto 5004"; exit 1; }
check_port 5005 || { echo "Pedido-service necesita puerto 5005"; exit 1; }

# Activar entorno virtual
echo "🐍 Activando entorno virtual..."
source venv/bin/activate

# Función para iniciar un servicio
start_service() {
    local service_name=$1
    local port=$2
    
    echo "🔄 Iniciando $service_name en puerto $port..."
    
    # Crear directorio de logs si no existe
    mkdir -p logs
    
    # Cambiar al directorio del servicio y usar su config.env
    cd microservicios/$service_name
    
    # Iniciar servicio en background
    nohup python app.py > ../../logs/${service_name}.log 2>&1 &
    
    # Volver al directorio raíz
    cd ../..
    
    # Guardar PID
    echo $! > logs/${service_name}.pid
    
    # Esperar un momento para que el servicio inicie
    sleep 2
    
    # Verificar que el servicio esté funcionando
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $service_name iniciado correctamente (PID: $(cat logs/${service_name}.pid))"
    else
        echo "❌ Error iniciando $service_name"
        return 1
    fi
}

# Iniciar servicios en orden
echo "🚀 Iniciando microservicios..."

# 1. Usuario Service (debe iniciar primero)
start_service "usuario-service" "5004"
if [ $? -ne 0 ]; then
    echo "❌ Error iniciando usuario-service"
    exit 1
fi

# 2. Pedido Service (depende de usuario-service)
start_service "pedido-service" "5005"
if [ $? -ne 0 ]; then
    echo "❌ Error iniciando pedido-service"
    exit 1
fi

# 3. Gateway (depende de ambos servicios)
start_service "gateway-service" "5003"
if [ $? -ne 0 ]; then
    echo "❌ Error iniciando gateway-service"
    exit 1
fi

echo ""
echo "🎉 ¡Todos los microservicios están funcionando!"
echo "============================================="
echo "📍 Servicios disponibles:"
echo "   • Gateway API:      http://localhost:5003"
echo "   • Usuario Service:  http://localhost:5004"
echo "   • Pedido Service:   http://localhost:5005"
echo ""
echo "🔧 Comandos útiles:"
echo "   • Ver logs:         tail -f logs/[servicio].log"
echo "   • Detener todo:     ./stop-microservicios.sh"
echo "   • Estado:           ./status-microservicios.sh"
echo ""
echo "📋 Para probar la API:"
echo "   curl http://localhost:5003/"
echo "   curl http://localhost:5003/health"
echo ""
echo "🔐 Para autenticación:"
echo "   curl -X POST http://localhost:5003/login -H 'Content-Type: application/json' -d '{\"username\": \"admin\", \"password\": \"admin123\"}'"
