from flask import Flask, request, jsonify
import pika
import json
import uuid

app = Flask(__name__)

# Configurações
RABBITMQ_HOST = 'localhost'
REQUEST_QUEUE = 'fila_requisicoes'

# Usuários autorizados (apenas para exemplo, o worker terá a lista definitiva)
AUTORIZADOS = ["admin", "usuario1", "usuario2"]

@app.route('/verificar', methods=['POST'])
def verificar_usuario():
    dados = request.get_json()
    
    if not dados or 'usuario' not in dados:
        return jsonify({"status": "dados inválidos"}), 400
    
    try:
        # Conexão com RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()
        
        # Declara a fila de requisições
        channel.queue_declare(queue=REQUEST_QUEUE, durable=True)
        
        # Cria uma fila temporária para a resposta
        result = channel.queue_declare(queue='', exclusive=True)
        callback_queue = result.method.queue
        
        # ID único para a requisição
        correlation_id = str(uuid.uuid4())
        
        # Publica a mensagem
        channel.basic_publish(
            exchange='',
            routing_key=REQUEST_QUEUE,
            body=json.dumps({'usuario': dados['usuario']}),
            properties=pika.BasicProperties(
                reply_to=callback_queue,
                correlation_id=correlation_id,
                delivery_mode=2  # Mensagem persistente
            )
        )
        
        # Espera a resposta
        response = None
        def on_response(ch, method, props, body):
            nonlocal response
            if correlation_id == props.correlation_id:
                response = json.loads(body)
        
        channel.basic_consume(
            queue=callback_queue,
            on_message_callback=on_response,
            auto_ack=True
        )
        
        # Timeout de 5 segundos
        connection.process_data_events(time_limit=5)
        connection.close()
        
        if response:
            return jsonify(response)
        else:
            return jsonify({"status": "timeout", "message": "Resposta não recebida"}), 504
            
    except Exception as e:
        return jsonify({"status": "erro", "detalhes": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)