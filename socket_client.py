from IPCutils import *

def main():
    c = BaseClient()
    print("about to connect")
    connected = c.connect_to("10.243.100.155", 9000)
    if connected:
        print("connected successfully")
    else:
        print("not connected")
        exit(1)

    while True:
        try: 
            inp = input()
            if (inp == "stop"):
                c.tx_message(STOP_SERVER_MSG)
                print("Sent stop command")
                c.disconnect()
                return
            else:
                if len(toks := inp.split(" ")) != 2:
                    print(f"Unable to parse {inp} => {toks}")
                    continue
                cmd = toks[0]
                val = toks[1]
                c.tx_message((cmd, int(val)))
                c.rx_message()
        except ConnectionAbortedError:
            print("Conx with server closed")
            return
        except ConnectionResetError:
            print("Conx with server closed")
            return
        except KeyboardInterrupt:
            c.disconnect()
            return

if __name__ == "__main__":
    main()