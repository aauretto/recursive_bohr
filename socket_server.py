from BasicServer import *

def main():
    s = BasicServer('localhost', 9000, 1)
    s.accept_connections(2)

    print("Listening for messages")

    while True:
        s.rx_message()

if __name__ == "__main__":
    main()