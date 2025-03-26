from IPCutils import *

def main():
    c = BaseClient()
    c.disconnect()
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
                if not c.tx_message(STOP_SERVER_MSG):
                    break
                print("Sent stop command")
                c.disconnect()
                return
            elif inp == "done":
                c.disconnect()
                print("Disconnected")
                break
            else:
                if len(toks := inp.split(" ")) != 2:
                    print(f"Unable to parse {inp} => {toks}")
                    continue
                cmd = toks[0]
                val = toks[1]
                if not c.tx_message((cmd, int(val))):
                    break
                c.rx_message()
        except ConnectionAbortedError:
            print("Conx with server closed")
            return
        except ConnectionResetError:
            print("Conx with server closed")
            return
        except KeyboardInterrupt:
            print("Disconnecting")
            c.disconnect()
            print("Done")
            return

if __name__ == "__main__":
    main()