import pika
import json

AUTORIZADOS = ["admin", "usuario1", "usuario2"]

def on_request(ch, method, props, body):
    try:
        dados = json.loads(body)
        usuario = dados['usuario']
        
        autorizado = usuario in AUTORIZADOS
        resposta = {
            "usuario": usuario,
            "autorizado": autorizado,
            "status": "autorizado" if autorizado else "não autorizado"
        }
        
        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(
                correlation_id=props.correlation_id
            ),
            body=json.dumps(resposta)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        print(f"Processado: {usuario} -> {'✅ Autorizado' if autorizado else '❌ Não autorizado'}")
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()
    
    channel.queue_declare(queue='fila_requisicoes', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue='fila_requisicoes',
        on_message_callback=on_request
    )
    
    print(' [*] Worker RPC aguardando requisições. CTRL+C para sair')
    channel.start_consuming()

if __name__ == '__main__':
    main()