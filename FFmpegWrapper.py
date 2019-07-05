"""
Thanks to Neon22 at:
https://gist.github.com/Neon22
"""

from ctypes import (c_int, c_int64, c_uint64,
                    c_uint8, c_uint, c_size_t, c_char, c_char_p,
                    c_void_p, POINTER, CFUNCTYPE, Structure)


AV_NUM_DATA_POINTERS = 8


class AVCodecContext(Structure):
    pass


class AVRational(Structure):
    pass


class AVIOInterruptCB(Structure):
    pass


class AVPacket(Structure):
    _fields_ = [
        ('buf', c_void_p),
        ('pts', c_int64),
        ('dts', c_int64),
        ('data', POINTER(c_uint8)),
        ('size', c_int),
        ('stream_index', c_int),
        ('flags', c_int),
        ('side_data', c_void_p),
        ('side_data_elems', c_int),
        ('duration', c_int64),
        ('pos', c_int64),
        ('convergence_duration', c_int64)  # Deprecated
    ]


class AVFrame(Structure):
    _fields_ = [
        ('data', POINTER(c_uint8) * AV_NUM_DATA_POINTERS),
        ('linesize', c_int * AV_NUM_DATA_POINTERS),
        ('extended_data', POINTER(POINTER(c_uint8))),
        ('width', c_int),
        ('height', c_int),
        ('nb_samples', c_int),
        ('format', c_int),
        ('key_frame', c_int),
        ('pict_type', c_int),  # or c_uint8
        ('sample_aspect_ratio', AVRational),
        ('pts', c_int64),
        ('pkt_pts', c_int64), # Deprecated
        ('pkt_dts', c_int64),
        ('coded_picture_number', c_int),
        ('display_picture_number', c_int),
        ('quality', c_int),
        ('opaque', c_void_p),
        ('error', c_uint64 * AV_NUM_DATA_POINTERS), #Deprecated
        ('repeat_pict', c_int),
        ('interlaced_frame', c_int),
        ('top_field_first', c_int),
        ('palette_has_changed', c_int),
        ('reordered_opaque', c_int64),
        ('sample_rate', c_int),
        ('channel_layout', c_uint64),
        ('buf', c_void_p * AV_NUM_DATA_POINTERS),
        ('extended_buf', c_void_p),
        ('nb_extended_buf', c_int),
        ('side_data', c_void_p),
        ('nb_side_data', c_int),
        ('flags', c_int),
        ('color_range', c_int),
        ('color_primaries', c_int),
        ('color_trc', c_int),
        ('colorspace', c_int),
        ('chroma_location', c_int),
        ('best_effort_timestamp', c_int64),
        ('pkt_pos', c_int64),
        ('pkt_duration', c_int64),
        #!
        ('metadata', c_void_p),
        ('decode_error_flags', c_int),
        ('channels', c_int),
        ('pkt_size', c_int),
        ('qscale_table', POINTER(c_int)), #Deprecated or c_unit8#!
        ('qstride', c_int), #Deprecated
        ('qscale_type', c_int), #Deprecated
        ('qp_table_buf', c_void_p), #Deprecated
        ('hw_frames_ctx', c_void_p),
        ('opaque_ref', c_void_p),
        #!('private_ref', POINTER(AVBufferRef)),
        #!('width', c_int), # video frames only
        #(!'height', c_int), # video frames only
        #!('crop_top', c_size_t), # video frames only
        #!('crop_bottom', c_size_t), # video frames only
        #!('crop_left', c_size_t), # video frames only
        #!('crop_right', c_size_t) # video frames only
    ]


class AVFormatContext(Structure):
    pass


AVFormatContext._fields_ = [
        ('av_class', c_void_p),
        ('iformat', c_void_p),
        ('oformat', c_void_p),
        ('priv_data', c_void_p),
        ('pb', c_void_p),
        ('ctx_flags', c_int),
        ('nb_streams', c_uint),
        ('streams', c_void_p),
        ('filename', c_char*1024),  # Deprecated
        ('url', c_char_p),
        ('start_time', c_int64),
        ('duration', c_int64),
        ('bit_rate', c_int64),
        ('packet_size', c_uint),
        ('max_delay', c_int),
        ('flags', c_int),
        ('probesize', c_int64),
        ('max_analyze_duration', c_int64),
        ('key', POINTER(c_uint8)),
        ('keylen', c_int),
        ('nb_programs', c_uint),
        ('programs', c_void_p),
        ('video_codec_id', c_int),
        ('audio_codec_id', c_int),
        ('subtitle_codec_id', c_int),
        ('max_index_size', c_uint),
        ('max_picture_buffer', c_uint),
        ('nb_chapters', c_uint),
        ('chapters', c_void_p),
        ('metadata', c_void_p),
        ('start_time_realtime', c_int64),
        ('fps_probe_size', c_int),
        ('error_recognition', c_int),
        ('interrupt_callback', AVIOInterruptCB),
        ('debug', c_int),
        ('max_interleave_delta', c_int64),
        ('strict_std_compliance', c_int),
        ('event_flags', c_int),
        ('max_ts_probe', c_int),
        ('avoid_negative_ts', c_int),
        ('ts_id', c_int),
        ('audio_preload', c_int),
        ('max_chunk_duration', c_int),
        ('max_chunk_size', c_int),
        ('use_wallclock_as_timestamps', c_int),
        ('avio_flags', c_int),
        ('duration_estimation_method', c_uint), #c_uint8
        ('skip_initial_bytes', c_int64),
        ('correct_ts_overflow', c_uint),
        ('seek2any', c_int),
        ('flush_packets', c_int),
        ('probe_score', c_int),
        ('format_probesize', c_int),
        ('codec_whitelist', c_char_p),
        ('format_whitelist', c_char_p),
        ('internal', c_void_p),
        ('io_repositioned', c_int),
        ('video_codec', c_void_p),
        ('audio_codec', c_void_p),
        ('subtitle_codec', c_void_p),
        ('data_codec', c_void_p),
        ('metadata_header_padding', c_int),
        ('opaque', c_void_p),
        ('control_message_cb', CFUNCTYPE(c_int, 
            POINTER(AVFormatContext), c_int, c_void_p,
            c_size_t)),
        ('output_ts_offset', c_int64),
        ('dump_separator', POINTER(c_uint8)),
        ('data_codec_id', c_int),
        # ! one more in here?
        ('protocol_whitelist', c_char_p),
        ('io_open', CFUNCTYPE(c_int, POINTER(AVFormatContext),
                              c_void_p, c_char_p, c_int,
                              c_void_p)),
        ('io_close', CFUNCTYPE(None, POINTER(AVFormatContext), c_void_p)),
        ('protocol_blacklist', c_char_p),
        ('max_streams', c_int)
        ]


read_packet_func = CFUNCTYPE(c_int, c_void_p, POINTER(c_uint8), c_int)
