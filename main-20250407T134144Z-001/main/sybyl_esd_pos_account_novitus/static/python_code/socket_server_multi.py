import socket
import threading

HEADER = 2048
PORT = 6001
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
SEPARATOR = "<SEPERATE>"
FILE_FINISHED_SENDING = "<!FILE_SENT!>"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

import datetime


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    current_file = None
    receipt_no = 6939

    while connected:
        data = conn.recv(HEADER).decode(FORMAT)
        print("data")
        print(data)
        print(type(data))
        print(receipt_no)
        #         return_response = """<packet crc="00540ADF"><info action="checkout" type="receipt" lasterror="0" isfiscal="yes" receiptopen="no" lastreceipterror="no" resetcount="0" date="23-05-2022" receiptcount="4926" cash="42643.00" uniqueno="KEB0500000011" lastreceipt="4926" lastinvoice="0" lastprintout="5135">
        #  <ptu name="A">8365.00</ptu>
        #  <ptu name="B">0.00</ptu>
        #  <ptu name="C">790.00</ptu>
        #  <ptu name="D">1355.00</ptu>
        # </info>
        # </packet>"""
        #         conn.send(return_response.encode())

        time = datetime.datetime.now()

        hour_minute = (
            str(time.hour).zfill(2)
            + (str(time.minute)).zfill(2)
            + str(time.second).zfill(2)
        )
        print("hour_minute :", str(hour_minute))
        # print('--------')
        # print(data.find("checkout"))
        print("--------", data)
        if "checkout" in data:
            print("find data")
            conn.send("<packet>".encode())
            return_xml = """<info action="checkout" type="receipt" lasterror="0" isfiscal="yes" receiptopen="no" lastreceipterror="no" resetcount="0" date="11-06-2022" 
        receiptcount="%s" cash="296560.00" uniqueno="KEB0500000011" lastreceipt="%s" lastinvoice="0" lastprintout="7240">
         <ptu name="A">176.00</ptu>
         <ptu name="B">0.00</ptu>
         <ptu name="C">0.00</ptu>
         <ptu name="D">0.00</ptu>
        </info>
        </packet>""" % (
                hour_minute,
                hour_minute,
            )
            return_xml_data = return_xml
        else:
            print("Invoice number")
            return_url_xml = """<packet crc="12663678"><info action="last_receipt" trader_sys_number_EX="" receipt_number="%s" TotalInvoiceAmount="6600.01" TotalTaxableAmount="5689.66" TotalTaxAmount="910.35" middleware_invoice_number="0190429020000000039" qr_code_link="https://itax.kra.go.ke/KRA-Portal/invoiceChk.htm?actionCode=loadPage&amp;invoiceNo=" CU_number="KRAMW019202207042902" />
</packet>""" % (
                hour_minute
            )
            return_xml_data = return_url_xml

        print("return_xml_data")
        print(return_xml_data)
        conn.send(return_xml_data.encode())
        if data == None:
            connected = False
        # if data == DISCONNECT_MESSAGE:
        #     connected = False
        # elif data == FILE_FINISHED_SENDING:
        #     current_file.close()
        #     current_file = None
        #     conn.send(b'file received.')
        # else:
        #     data = data.split(SEPARATOR)
        #     if len(data) == 2 and data[1] == '':
        #         # The name of the file was sent, more will follow.
        #         current_file = open(data[0], 'w')
        #         conn.send(b'filename received')
        #     else:
        #         # File data was send, so write it to the current file
        #         current_file.write(data[1])
        #         print('chunk of file recv''d')
        #         conn.send(b'chunk received')
    conn.close()
    print(f"[DISCONNECT] {addr} disconnected")


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


print("[STARTING] server is starting...")
start()
