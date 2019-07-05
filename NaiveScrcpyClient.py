# coding=utf-8

import numpy as np
import cv2
import os
import socket
import struct
import time
import traceback
import subprocess
import ctypes
from FFmpegWrapper import AVFormatContext, AVCodecContext, AVPacket, AVFrame, read_packet_func
from threading import Thread
from collections import deque


class ScrcpyDecoder:
    def __init__(self, _config):
        self.buff_size = _config.get('buff_size', 0x100000)
        self.lib_path = _config.get('lib_path', 'lib')
        self.img_queue = deque(maxlen=int(_config.get('deque_length', 5)))

        # TCP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = _config.get('adb_port', 61550)

        # pointers
        self.frame_ptr = 0
        self.codec_ctx_ptr = 0
        self.format_ctx_ptr = 0

        # thread and flag
        self.decode_thread = None
        self.should_run = False

    @staticmethod
    def ff_err_tag(cd):
        mk_tag = 0
        for i in reversed(cd):
            mk_tag = mk_tag << 8
            mk_tag |= (ord(i) & 0xff)
        result = -int(mk_tag)
        return result

    def start_decoder(self):
        self.should_run = True
        if self.decode_thread is None:
            self.decode_thread = Thread(target=self._run_decoder)
            self.decode_thread.start()

    def _run_decoder(self):
        try:
            self.sock.settimeout(0.5)
            self.sock.connect(("127.0.0.1", self.port))
        except:
            traceback.print_exc()
            return 1
        self._receive_info()
        lib_file_list = os.listdir(self.lib_path)

        def get_lib_full_path(keyword):
            for i in lib_file_list:
                if keyword in i:
                    return os.path.join(self.lib_path, i)
            print("Could not find runtime %s at %s" % (keyword, self.lib_path))
            return None

        avutil_lib = get_lib_full_path("avutil")
        swresample_lib = get_lib_full_path("swresample")
        avcodec_lib = get_lib_full_path("avcodec")
        avformat_lib = get_lib_full_path("avformat")

        if None in [avutil_lib, swresample_lib, avcodec_lib, avformat_lib]:
            return -2

        lib_avutil = ctypes.CDLL(avutil_lib)
        lib_swresample = ctypes.CDLL(swresample_lib)
        lib_avcodec = ctypes.CDLL(avcodec_lib)
        lib_avformat = ctypes.CDLL(avformat_lib)

        lib_avformat.av_register_all()

        def clean_decoder():
            if self.frame_ptr:
                # print("Free frame")
                lib_avutil.av_free(self.frame_ptr)
                self.frame_ptr = 0
            if self.codec_ctx_ptr:
                # print("Free avcodec")
                lib_avcodec.avcodec_close(self.codec_ctx_ptr)
                self.codec_ctx_ptr = 0
            if self.format_ctx_ptr:
                # print("Free avformat")
                lib_avformat.avformat_close_input(ctypes.byref(self.format_ctx_ptr))
                self.format_ctx_ptr = 0
            self.sock.close()

        find_decoder = lib_avcodec.avcodec_find_decoder_by_name
        find_decoder.restype = ctypes.POINTER(AVCodecContext)
        decoder_list = [b'h264_mmal', b'h264']
        for decoder in decoder_list:
            codec_ptr = find_decoder(ctypes.c_char_p(decoder))
            if codec_ptr:
                print("Found %s decoder" % decoder.decode('utf8'))
                break
        else:
            print("H.264 decoder not found")
            return 1

        alloc_context = lib_avcodec.avcodec_alloc_context3
        alloc_context.restype = ctypes.POINTER(AVCodecContext)
        self.codec_ctx_ptr = alloc_context(codec_ptr)
        if not self.codec_ctx_ptr:
            print("Could not allocate decoder context")
            clean_decoder()
            return 2

        ret = lib_avcodec.avcodec_open2(self.codec_ctx_ptr, codec_ptr, None)
        if ret < 0:
            print("Could not open H.264 decoder")
            clean_decoder()
            return 3

        format_alloc_context = lib_avformat.avformat_alloc_context
        format_alloc_context.restype = ctypes.POINTER(AVFormatContext)
        self.format_ctx_ptr = format_alloc_context()
        if not self.format_ctx_ptr:
            print("Could not allocate format context")
            clean_decoder()
            return 4

        av_malloc = lib_avutil.av_malloc
        av_malloc.restype = ctypes.POINTER(ctypes.c_ubyte)
        buffer_ptr = av_malloc(self.buff_size)
        if not buffer_ptr:
            print("Could not allocate buffer")
            clean_decoder()
            return 5

        def read_packet_wrapper(_, buff, c_size):
            try:
                s, data = self.receive_data(c_size)
                if s == 0:
                    return self.ff_err_tag('EOF ')
                else:
                    ctypes.memmove(buff, data, s)
                    return s
            except:
                traceback.print_exc()
                return self.ff_err_tag('EOF ')

        read_packet_ptr = read_packet_func(read_packet_wrapper)
        av_alloc_ctx = lib_avformat.avio_alloc_context
        av_alloc_ctx.restype = ctypes.c_void_p
        avio_ctx_ptr = av_alloc_ctx(buffer_ptr, self.buff_size, 0, None, read_packet_ptr, None, None)
        if not avio_ctx_ptr:
            print("Could not allocate avio context")
            clean_decoder()
            return 6
        self.format_ctx_ptr.contents.pb = avio_ctx_ptr
        open_input = lib_avformat.avformat_open_input
        ret = open_input(ctypes.byref(self.format_ctx_ptr), None, None, None)
        if ret < 0:
            print("Could not open video stream")
            clean_decoder()
            return 7
        alloc_frame = lib_avutil.av_frame_alloc
        alloc_frame.restype = ctypes.POINTER(AVFrame)
        self.frame_ptr = alloc_frame()
        packet = AVPacket()
        lib_avcodec.av_init_packet(ctypes.byref(packet))

        while self.should_run:
            if not lib_avformat.av_read_frame(self.format_ctx_ptr, ctypes.byref(packet)):
                ret = lib_avcodec.avcodec_send_packet(self.codec_ctx_ptr, ctypes.byref(packet))
                if ret < 0:
                    print("Could not send video packet: %d" % ret)
                    break
                ret = lib_avcodec.avcodec_receive_frame(self.codec_ctx_ptr, self.frame_ptr)
                if not ret:
                    self.push_frame(self.frame_ptr)
                else:
                    print("Could not receive video frame: %d" % ret)
                lib_avcodec.av_packet_unref(ctypes.byref(packet))
            else:
                print("Could not read packet, quit.")
                self.should_run = False
        clean_decoder()
        return 0

    def close_decoder(self):
        self.should_run = False
        if self.decode_thread:
            self.decode_thread.join()
            self.decode_thread = None

    def push_frame(self, frame_ptr):
        frame = frame_ptr.contents
        w = frame.width
        h = frame.height
        img_yuv = np.zeros((h + h // 2, w, 1), dtype=np.uint8)
        img_yuv[:h, :] = np.ctypeslib.as_array(frame.data[0], shape=(h, frame.linesize[0], 1))[:, :w]
        img_u = np.ctypeslib.as_array(frame.data[1], shape=(h // 2, frame.linesize[1], 1))[:, :w // 2]
        img_v = np.ctypeslib.as_array(frame.data[2], shape=(h // 2, frame.linesize[2], 1))[:, :w // 2]
        img_yuv[h:h + h // 4, : w // 2] = img_u[::2, :]
        img_yuv[h + h // 4:, : w // 2] = img_v[::2, :]
        img_yuv[h:h + h // 4, w // 2:] = img_u[1::2, :]
        img_yuv[h + h // 4:,  w // 2:] = img_v[1::2, :]
        img = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR_I420)
        self.img_queue.append(img)

    def get_next_frame(self, latest_image=False):
        if not self.img_queue:
            return None
        else:
            img = self.img_queue.popleft()
            if latest_image:
                while self.img_queue:
                    img = self.img_queue.popleft()
            return img

    def receive_data(self, c_size):
        while self.should_run:
            try:
                data = self.sock.recv(c_size)
                return len(data), data
            except socket.timeout:
                continue
            except:
                return 0, []

    def send_data(self, data):
        return self.sock.send(data)

    def _receive_info(self):
        dummy_byte = self.sock.recv(1)
        if not len(dummy_byte):
            raise ConnectionError("Did not receive Dummy Byte!")
        else:
            print("Connected!")

        device_name = self.sock.recv(64)
        device_name = device_name.decode("utf-8")
        if not len(device_name):
            raise ConnectionError("Did not receive Device Name!")
        print("Device Name: " + device_name)

        res = self.sock.recv(4)
        frame_width, frame_height = struct.unpack(">HH", res)
        print("WxH: " + str(frame_width) + "x" + str(frame_height))


class NaiveScrcpyClient:
    def __init__(self, _config):
        self.config = _config
        self.lib_path = self.config.get('lib_path', 'lib')
        self.adb = self.config.get('adb_path', 'adb')
        self.port = int(self.config.get('adb_port', 61550))

        self.adb_sub_process = None
        self.decoder = None
        self.img_cache = None
        self.landscape = False

        self._connect_and_forward_scrcpy()


    def _connect_and_forward_scrcpy(self):
        try:
            print("Upload JAR...")
            adb_push = subprocess.Popen(
                [self.adb, 'push',
                 'scrcpy-server.jar',
                 '/data/local/tmp/'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.lib_path)
            adb_push_comm = ''.join([x.decode("utf-8") for x in adb_push.communicate() if x is not None])

            if "error" in adb_push_comm:
                print("Is your device/emulator visible to ADB?")
                raise Exception(adb_push_comm)

            subprocess.call(
                [self.adb, 'forward',
                 'tcp:%d' % self.port, 'localabstract:scrcpy'])
            
            '''
            ADB Shell is Blocking, don't wait up for it
            Args for the server are as follows:
            maxSize         (integer, multiple of 8) 0
            bitRate         (integer)
            tunnelForward   (optional, bool) use "adb forward" instead of "adb tunnel"
            crop            (optional, string) "width:height:x:y"
            sendFrameMeta   (optional, bool)

            '''
            print("Run JAR")
            self.adb_sub_process = subprocess.Popen(
                [self.adb, 'shell',
                 'CLASSPATH=/data/local/tmp/scrcpy-server.jar',
                 'app_process', '/', 'com.genymobile.scrcpy.Server',
                 str(int(self.config.get('max_size', 1280))),
                 str(int(self.config.get('bit_rate', 2 ** 30))),
                 "true",
                 str(self.config.get('crop', '-')),
                 "false"],
            )
            time.sleep(2)
        except FileNotFoundError:
            raise FileNotFoundError("Could not find ADB")

    def _disable_forward(self):
        subprocess.call(
            [self.adb, 'forward', '--remove',
             'tcp:%d' % self.port])

    def start_loop(self):
        if self.decoder:
            return 2
        self.decoder = ScrcpyDecoder(self.config)
        try:
            self.decoder.start_decoder()
            return 0
        except ConnectionError:
            traceback.print_exc()
            self.stop_loop()
            return 1

    def stop_loop(self):
        if self.decoder:
            self.decoder.close_decoder()
            self.decoder = None
        if self.adb_sub_process:
            subprocess.Popen(
                [self.adb, 'shell',
                 '`pkill app_process`',
                 ],
                stdout=subprocess.PIPE,
            ).wait()
            self.adb_sub_process.wait()
            self.adb_sub_process = None
        self._disable_forward()

    def get_screen_frame(self):
        img = self.decoder.get_next_frame(True)
        if img is not None:
            self.landscape = img.shape[0] < img.shape[1]
            self.img_cache = img.copy()
        return self.img_cache
