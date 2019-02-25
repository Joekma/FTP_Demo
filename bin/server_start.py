import os
import sys

import core.FTP_server

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_PATH)

if __name__ == '__main__':
    core.FTP_server.main()
