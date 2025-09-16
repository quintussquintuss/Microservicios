#!/bin/bash

# Script para detener todos los microservicios
echo "🛑 Deteniendo Arquitectura de Microservicios"
echo "============================================="

# Función para detener un servicio
stop_service() {
    local service_name=$1
    local pid_file="logs/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        echo "🔄 Deteniendo $service_name (PID: $pid)..."
        
        if kill $pid 2>/dev/null; then
            echo "✅ $service_name detenido correctamente"
            rm -f "$pid_file"
        else
            echo "❌ Error deteniendo $service_name (proceso no encontrado)"
            rm -f "$pid_file"
        fi
    else
        echo "⚠️  $service_name no está ejecutándose (no hay archivo PID)"
    fi
}

# Detener servicios en orden inverso
echo "🛑 Deteniendo microservicios..."

# 1. Gateway
stop_service "gateway-service"

# 2. Pedido Service
stop_service "pedido-service"

# 3. Usuario Service
stop_service "usuario-service"

# Limpiar logs antiguos (opcional)
echo ""
echo "🧹 Limpieza opcional de logs..."
read -p "¿Deseas eliminar los archivos de log? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f logs/*.log
    echo "✅ Logs eliminados"
else
    echo "ℹ️  Logs conservados en directorio logs/"
fi

echo ""
echo "✅ Todos los microservicios han sido detenidos"
echo "============================================="
