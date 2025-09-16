#!/bin/bash

# Script para verificar el estado de todos los microservicios
echo "📊 Estado de la Arquitectura de Microservicios"
echo "============================================="

# Función para verificar un servicio
check_service() {
    local service_name=$1
    local port=$2
    local pid_file="logs/${service_name}.pid"
    
    echo -n "🔍 $service_name (puerto $port): "
    
    # Verificar si hay un PID
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        # Verificar si el proceso está ejecutándose
        if ps -p $pid > /dev/null 2>&1; then
            # Verificar si responde HTTP
            if curl -s http://localhost:$port/health > /dev/null 2>&1; then
                echo "✅ RUNNING (PID: $pid) - Healthy"
                
                # Mostrar información adicional del health check
                echo "   📡 Health Check:"
                curl -s http://localhost:$port/health | python3 -m json.tool 2>/dev/null | sed 's/^/      /'
            else
                echo "⚠️  RUNNING (PID: $pid) - Unhealthy (no responde HTTP)"
            fi
        else
            echo "❌ STOPPED (archivo PID existe pero proceso no encontrado)"
            rm -f "$pid_file"
        fi
    else
        echo "❌ STOPPED (no hay archivo PID)"
    fi
    echo ""
}

# Verificar cada servicio
check_service "gateway-service" "5003"
check_service "usuario-service" "5004"
check_service "pedido-service" "5005"

# Verificar conectividad entre servicios
echo "🔗 Verificando comunicación entre microservicios..."
echo "=================================================="

# Gateway -> Usuario Service
echo -n "Gateway -> Usuario Service: "
if curl -s -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" http://localhost:5003/usuarios > /dev/null 2>&1; then
    echo "✅ Comunicación exitosa"
else
    echo "❌ Error de comunicación"
fi

# Gateway -> Pedido Service
echo -n "Gateway -> Pedido Service: "
if curl -s -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" http://localhost:5003/pedidos > /dev/null 2>&1; then
    echo "✅ Comunicación exitosa"
else
    echo "❌ Error de comunicación"
fi

# Pedido Service -> Usuario Service
echo -n "Pedido Service -> Usuario Service: "
if curl -s -H "X-API-Key: 74UIHTG984OJR094YTH49**-0573" http://localhost:5005/pedidos > /dev/null 2>&1; then
    echo "✅ Comunicación exitosa"
else
    echo "❌ Error de comunicación"
fi

echo ""
echo "📋 Comandos útiles:"
echo "   • Ver logs en tiempo real: tail -f logs/[servicio].log"
echo "   • Detener todos: ./stop-microservicios.sh"
echo "   • Reiniciar todos: ./stop-microservicios.sh && ./start-microservicios.sh"
echo ""
echo "🔧 Para más pruebas:"
echo "   • curl -H 'X-API-Key: 74UIHTG984OJR094YTH49**-0573' http://localhost:5003/"
echo "   • curl http://localhost:5004/ (usuario-service directo)"
echo "   • curl http://localhost:5005/ (pedido-service directo)"
