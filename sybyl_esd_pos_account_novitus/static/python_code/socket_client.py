# Import socket module
import re
import socket
import xmltodict


def Main():
    # local host IP '127.0.0.1'
    # Client Location DTC
    host = "127.0.0.1"
    # host = '197.232.150.207'
    # Kenya Office - Non fiscal
    # host = '197.248.47.141'

    # Define the port on which you want to connect
    port = 6001

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    # connect to server on local computer
    s.connect((host, port))
    count = 1
    while True:
        # message you send to server
        message = """<packet><control action="beep"></control></packet>"""
        message = """<packet><info action="checkout" type="receipt" lasterror="?" isfiscal="?" receiptopen="?" lastreceipterror="?" resetcount="?" date="?" receiptcount="?" cash="?" uniqueno="?" lastreceipt="?" lastinvoice="?" lastprintout="?"></info></packet>"""
        # Only Works with fiscal printer
        if (count % 2) == 0:
            message = """<packet><info action="last_receipt"></info></packet>"""
            # message = """<packet><info action="teams_server" server_action="force_transfer"></info></packet>"""
        # message sent to server
        s.send(message.encode("ascii"))

        # message received from server
        data = s.recv(1024)

        # print the received message
        # here it would be a reverse of sent message
        print("Received from the server :", str(data.decode("ascii")))
        try:
            o = xmltodict.parse(str(data.decode("ascii")))
            cusn = o.get("packet").get("info").get("@CU_number")
            cuin = o.get("packet").get("info").get("@middleware_invoice_number")
            print("***********************", cusn, cuin)
        except Exception as e:
            print(e)

        url = False
        start_url = False
        end_url = False
        result = re.search('qr_code_link="(.*)"', data.decode("ascii"))
        print(result)

        if result:
            print(result.group(0))
            print(result.group(1))
        pre_result = re.search('qr_code_link="(.*)" CU_number', data.decode("ascii"))
        suffix_result = re.search(
            'middleware_invoice_number="(.*)" qr_code_link=', data.decode("ascii")
        )
        cuin_result = re.search(
            'middleware_invoice_number="(.*)" qr_code_link', data.decode("ascii")
        )
        cusn_result = re.search('CU_number="(.*)" ', data.decode("ascii"))

        if cuin_result:
            cuin_value = cuin_result_value = cuin_result.group(1)
            if not isinstance(cuin_result_value, int):
                int_value2 = [int(s) for s in cuin_result_value.split() if s.isdigit()]
                cuin_value = int_value2[0]
            print(cuin_value)
        if cusn_result:
            cusn_value = cusn_result.group(1)
            print(cusn_value)

        if pre_result:
            start_url = pre_result.group(1)
        if suffix_result:
            end_url = suffix_result.group(1)
        if start_url and end_url:
            url = start_url + end_url
            print("Full URL")
            print(url)
            url = url.replace("&amp;", "&")
            print(url)
        # print("sample URL")
        # print("https://itax.kra.go.ke/KRA-Portal/invoiceChk.htm?actionCode=loadPage&invoiceNo=0190429020000000002")
        # ask the client whether he wants to continue
        ans = input("\nDo you want to continue(y/n) :")
        if ans == "y":
            print("count : ", count)
            count += 1
            continue
        else:
            break
    # close the connection
    s.close()


if __name__ == "__main__":
    Main()
