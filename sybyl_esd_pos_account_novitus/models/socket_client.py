import logging
import socket
import sys
from time import sleep

_logger = logging.getLogger(__name__)


def socket_client_request(url, data):
    ip_address_split = url.split(":")
    host = ip_address_split[0]
    port = int(ip_address_split[1])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(7)
    try:
        s.connect((host, port))
    except Exception as e:
        _logger.info(e)
        return False
    _logger.info(s)

    if isinstance(data, str):
        data = bytes(data, "utf-8")

    while True:
        try:
            _logger.info("\nSocket.send(data) : %s", data)
            s.send(data)
            full_data = ""
            counter = 0
            while True:
                s_recv = s.recv(2048)
                _logger.info("\nSocket.recv(1024) : %s", s_recv)
                d = s_recv.decode("utf-8")
                full_data += d
                counter += 1
                if counter > 5:
                    return False
                if "</packet>" in full_data:
                    _logger.info("full_data :")
                    _logger.info(full_data)
                    return full_data
        except socket.timeout as e:
            err = e.args[0]
            # this next if/else is a bit redundant, but illustrates how the
            # timeout exception is setup
            if err == "timed out":
                sleep(1)
                _logger.info("recv timed out, retry later")
                return False
                # sys.exit(1)
                # continue
            else:
                _logger.info(e)
                return False
                # sys.exit(1)
        except socket.error as e:
            # Something else happened, handle error, exit, etc.
            _logger.info(e)
            return False
            # sys.exit(1)
        else:
            if len(msg) == 0:
                _logger.info("orderly shutdown on server end")
                sys.exit(0)
            else:
                # got a message do something :)
                _logger.info("exit")
                continue
