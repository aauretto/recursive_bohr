from IPCutils import *


def main():
    c = BaseClient()
    c.connect_to("localhost", 9000)

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