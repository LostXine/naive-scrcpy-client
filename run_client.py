# coding=utf-8

from NaiveScrcpyClient import *


def run_client(_config):
    client = NaiveScrcpyClient(_config)
    ret = client.start_loop()
    if ret:
        return ret
    while True:
        try:
            img = client.get_screen_frame()
            if img is not None:
                cv2.imshow("img", img)
            c = cv2.waitKey(10)
            if c in [27, 13]:
                break
        except KeyboardInterrupt:
            break
    client.stop_loop()
    cv2.destroyAllWindows()
    return 0


if __name__ == '__main__':
    config = {
        "max_size": 640,
        "bit_rate": 2 ** 30,
        "crop": "-",
        "adb_path": "adb",
        "adb_port": 61550,
        "lib_path": "lib",
        "buff_size": 0x10000,
        "deque_length": 5
    }
    run_client(config)
