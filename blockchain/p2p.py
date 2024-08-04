import ipfshttpclient

class IPFSClient:
    def __init__(self):
        self.client = ipfshttpclient.connect()

    def publish_block(self, block):
        block_data = block.to_dict()
        res = self.client.add_json(block_data)
        return res

    def subscribe_blocks(self, callback):
        with self.client.pubsub_subscribe('blocks') as sub:
            for message in sub:
                block_data = message['data']
                callback(block_data)

    def publish_message(self, topic, message):
        self.client.pubsub_pub(topic, message)