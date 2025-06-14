import pika
import json

def callback(ch, method, properties, body):
    resposta = json.loads(body)
    print(f"\nResposta recebida: {resposta}\n")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def escutar_respostas():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()
    
    channel.queue_declare(queue='fila_respostas')
    channel.basic_consume(
        queue='fila_respostas',
        on_message_callback=callback
    )
    
    print(' [*] Aguardando respostas...')
    channel.start_consuming()

if __name__ == '__main__':
    escutar_respostas()