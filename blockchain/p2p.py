import subprocess
import time
import threading
import uuid

class IPFSClient:
    def __init__(self, topic):
        self.topic = topic
        self.id = str(uuid.uuid4())  # Unique identifier for each instance

    def publish(self):
        while True:
            # Create a message with the unique ID
            # message = f"Message from {self.id}: Hello from IPFS!"
            message = input("MESSAGE :")
            
            # Use subprocess to run the IPFS CLI command to publish the message
            process = subprocess.run(
                ["ipfs", "pubsub", "pub", self.topic, message],
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                print(f"Published message: {message}")
            else:
                print(f"Failed to publish message: {message}, Error: {process.stderr}")
            
            # Sleep before the next publish
            time.sleep(5)

    def subscribe(self):
        # Use subprocess to run the IPFS CLI command to subscribe to the topic
        process = subprocess.Popen(
            ["ipfs", "pubsub", "sub", self.topic],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"Subscribed to topic: {self.topic}")
        
        # Continuously listen to messages from the topic

        while True:
            print("Waiting for message")
            time.sleep(5)
            output = process.stdout.readline()
            if output:
                print(f"Received message: {output}")
            # time.sleep(1)  # Sleep briefly to reduce CPU usage

    def run(self):
        try:
            # Start both publishing and subscribing in parallel using threads
            publish_thread = threading.Thread(target=self.publish)
            subscribe_thread = threading.Thread(target=self.subscribe)

            publish_thread.start()
            subscribe_thread.start()

            # Keep the main thread alive while the threads run
            publish_thread.join()
            subscribe_thread.join()

        except KeyboardInterrupt:
            print("Interrupted by user. Exiting...")
        except Exception as e:
            print(f"An error occurred: {e}")
        

if __name__ == "__main__":
    ipfs_client = IPFSClient(topic="example_topic")
    ipfs_client.run()
