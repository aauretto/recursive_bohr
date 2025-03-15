from BasicClient import *

def main():
    c = BasicClient()
    c.connect_to("localhost", 9000)

    ctr = 0
    while True:
        c.tx_message((ctr, input()))
        ctr += 1
        

if __name__ == "__main__":
    main()