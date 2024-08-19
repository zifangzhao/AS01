import numpy as np
import os
from scipy import signal as sg
import struct


class NsxFile:
    def __init__(self, filename):
        self.filename = filename
        header_items = ['FileTypeID', 'FileSpec', 'BytesInHeaders', 'Label', 'Comment'
            , 'Period', 'TimeResolution', 'TimeOrigin', 'ChannelCount']
        header_bytes = [8, 2, 4, 16, 256, 4, 4, 16, 4]
        offsets = np.append(0, np.cumsum(header_bytes))
        self.header = {header_items[x]: np.fromfile(filename, dtype=np.uint8, count=header_bytes[x], offset=offsets[x])
                       for x in range(len(header_items))}
        ffid = struct.unpack('8c', self.header['FileTypeID'])
        tempstr = ""
        for x in ffid:
            tempstr += str(x.decode("UTF-8"))
        print(self.filename + " File type:" + tempstr)
        self.FileTypeID = tempstr
        self.BytesInHeaders = struct.unpack('<I', self.header['BytesInHeaders'])[0]
        self.channel_count = struct.unpack('<I', self.header['ChannelCount'])[0]
        self.sampling_rate = struct.unpack('<I', self.header['TimeResolution'])[0]
        self.file_bytes = os.path.getsize(filename)

        # read data package information
        pkg_offset = self.BytesInHeaders
        data_locations = []
        if (self.FileTypeID == 'NEURALSG'):
            data_locations = [[pkg_offset, self.file_bytes]]
            data = np.fromfile(filename, dtype=dtype, count=batchsize + overlap, offset=offset)
        else:
            header_items = ['id', 'timestamp', 'number_of_points']
            header_def = {'NEURALCD': [1, 4, 4], 'BRSMPGRP': [1, 8, 4]}
            header_bytes = header_def[self.FileTypeID]  # header lens depends on the file version
            header_offsets = np.append(0, np.cumsum(header_bytes))
            header_len = header_offsets[-1]
            while (pkg_offset < self.file_bytes):
                # decode data package header
                offsets = [x + pkg_offset for x in header_offsets]  # locate byte in data header
                section_header = {header_items[x]: np.fromfile(self.filename, dtype=np.uint8, count=header_bytes[x],
                                                               offset=offsets[x]) for x in range(len(header_items))}
                header = struct.unpack('c', section_header['id'])[0]
                data_section_points = struct.unpack('L', section_header['number_of_points'])[0]
                if (header == b'\x01'):
                    data_locations += [[offsets[-1], data_section_points * self.channel_count * 2]]
                else:
                    data_locations += [[pkg_offset, self.file_bytes]]
                    data_section_points = (self.file_bytes - pkg_offset) / 2
                pkg_offset += header_len + data_section_points * self.channel_count * 2  # advance to next block
            print('Segments found:' + str(len(data_locations)))
            # print(str((data_locations)))
        self.data_locations = data_locations  # Inital offset and duration in bytes

    def ReadData(self, offset, length):  # offset is in bytes, length is in samples
        data = np.zeros((length, 1))  # pre-allocate memory
        data_section_durations = [x[1] for x in self.data_locations]  # durations of each data segments
        data_section_init_offsets = np.append(0,
                                              np.cumsum(data_section_durations))  # initial data index of each segments
        rd_cnt = 0  # pointer for data buffer
        while length > 0:  # loop until read enough bytes
            curr_section = np.argmax(
                data_section_init_offsets > offset) - 1  # locate the first data block contains the required data
            if curr_section == -1:
                return data[0:rd_cnt, 0]
            offset_in_section = offset - data_section_init_offsets[curr_section]
            offset_in_file = offset_in_section + self.data_locations[curr_section][0]
            curr_duration = int((self.data_locations[curr_section][1] - offset_in_section) / 2)
            # print('offset in section:'+ str(offset_in_section)+'offset in file:'+str(offset_in_file) + "cur_section:" + str(curr_section))
            if (length < curr_duration):
                rd_len = length
            else:
                rd_len = curr_duration

            temp = np.fromfile(self.filename, dtype=np.int16, count=rd_len, offset=offset_in_file)
            data[rd_cnt:rd_cnt + temp.size, 0] = temp
            rd_cnt += temp.size
            offset += temp.size * 2
            length -= temp.size
        return data

    def ConvertToDat(self, res_fs=0, filename_output=''):
        if filename_output is '':
            filename_output = self.filename[0:self.filename.rfind('.')] + '.dat';
        if res_fs == 0:
            res_fs = self.sampling_rate
        batchsize = self.sampling_rate * self.channel_count * 100

        filesize = self.file_bytes
        dataunit = 2
        raw_fs = self.sampling_rate
        Nch = self.channel_count
        batchsize = Nch * raw_fs * 100
        overlapTime = 1
        overlap = Nch * overlapTime * raw_fs

        offset = 0
        dtype = np.int16
        conv = 1
        data = self.ReadData(offset, batchsize + overlap)
        data = np.reshape(data.T, (-1, Nch))
        if (res_fs == raw_fs):
            data_lfp = data
        else:
            data_lfp = sg.resample_poly(data, res_fs, raw_fs)
        data_lfp[0:data_lfp.shape[0] - overlapTime * res_fs, ].astype(dtype).tofile(filename_output)
        offset += (batchsize - overlap) * dataunit  # second block should shart with the first batch size - overlap
        # print('offset'+ str(offset))
        with open(filename_output, mode='ba+') as f:  # reopenfile in append mode
            while conv:
                data = self.ReadData(offset, batchsize + 2 * overlap)
                rd_len = len(data)
                data = np.reshape(data.T, (-1, Nch))

                if (res_fs == raw_fs):
                    print('Concatenating... Output:' + filename_output + ' Progress:' + str(offset) + '/' + str(
                        self.file_bytes))
                    data_lfp = data
                else:
                    print('Resampling to:' + str(res_fs) + 'Hz Output:' + filename_output + ' Progress:' + str(
                        offset) + '/' + str(self.file_bytes))
                    data_lfp = sg.resample_poly(data, res_fs, raw_fs)
                # print('In' + str(data.size) + ' Out' + str(data_lfp.size))
                if (rd_len == (batchsize + 2 * overlap)):  # check if file reach to the EOF
                    data_lfp[overlapTime * res_fs:data_lfp.shape[0] - overlapTime * res_fs, ].astype(dtype).tofile(
                        f)  # clip overlap area, save the rest
                    offset += batchsize * dataunit  # advance to next block
                else:
                    data_lfp[overlapTime * res_fs:, ].astype(dtype).tofile(f)
                    conv = 0
                    print('Done!')
