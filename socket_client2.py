from BasicClient import *

def main():
    c = BasicClient()
    c.connect_to("localhost", 9000)

    while True:
        input("Press enter to get a message")
        print(c.rx_message())
        

if __name__ == "__main__":
    main()