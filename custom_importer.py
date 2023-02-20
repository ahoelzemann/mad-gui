from typing import Dict
import warnings
import pandas as pd
from mad_gui import start_gui, BaseImporter, BaseExporter
from mad_gui.models import GlobalData
from PySide2.QtWidgets import QFileDialog
from mad_gui.components.dialogs import UserInformation
from pathlib import Path
import os
import datetime
import numpy as np


class CustomImporter(BaseImporter):
    loadable_file_type = "*.*"

    @classmethod
    def name(cls) -> str:
        ################################################
        ###                   README                 ###
        ### Set your importer's name as return value ###
        ### This name will show up in the dropdown.  ###
        ################################################
        # warnings.warn("The importer has no meaningful name yet."
        #               " Simply change the return string and remove this warning.")
        return "PerCom2023"

    def load_sensor_data(self, file_path: str) -> Dict:
        ##################################################################
        ###                       README                               ###
        ### a) Use the argument `file_path` to load data. Transform    ###
        ###    it to a pandas dataframe (columns are sensor channels,  ###
        ###    as for example "acc_x". Assign it to sensor_data.       ###
        ###                                                            ###
        ### b) load the sampling rate (int or float)                   ###
        ##################################################################

        # warnings.warn("Please load sensor data from your source."
        #               " Just make sure, that sensor_data is a pandas.DataFrame."
        #               " Afterwards, remove this warning.")
        # sensor_data = pd.read_csv(file_path, names=["acc_x", "acc_y", "acc_z"])[1:]
        #
        sampling_rate = 25
        subject_data = []
        paths = get_all_daily_files(file_path)
        binary_files = list(map(readBinFile, paths))
        for path in binary_files:
            subject_data.append(decompress(path))
        # concat every file in subject_data to create an array of data that contains the full day

        subject_data = make_equidistant(subject_data, sampling_rate)
        subject_data = pd.concat(subject_data)
        subject_data = resample_raw_data(subject_data, sampling_rate)

        # sensor_data = pd.read_csv(file_path)[["x_axis", "y_axis", "z_axis"]]
        # warnings.warn("Please load the sampling frequency from your source in Hz"
        #               " Afterwards, remove this warning.")
        # sampling_rate_hz = 1 / sensor_data["time"].diff().mean()

        ##############################################################
        ###                      CAUTION                           ###
        ### If you only want to have one plot you do not need to   ###
        ### change the following lines! If you want several plots, ###
        ### just add another sensor like "IMU foot" to the `data`  ###
        ### dictionary, which again hase keys sensor_data and      ###
        ### and sampling_rate_hz for that plot.                    ###
        ##############################################################
        data = {
            "IMU Wrist": {
                "sensor_data": subject_data[['x_axis', 'y_axis', 'z_axis']],
                "sampling_rate_hz": sampling_rate,
                "start_time": subject_data['index']
            }
        }
        # data = .drop(columns=['B', 'C'])

        return data

    def get_start_time(self, *args, **kwargs) -> datetime.time:
        try:
            start = datetime.datetime.strptime(str(args[1]), '%Y-%m-%d %H:%M:%S.%f').time()
        except:
            start = datetime.datetime.strptime(str(args[1]), '%Y-%m-%d %H:%M:%S').time()
        return start

class CustomExporter(BaseExporter):
    @classmethod
    def name(cls):
        return "Export annotations to csv (MaD GUI example)"

    def process_data(self, global_data: GlobalData):
        directory = QFileDialog().getExistingDirectory(
            None, "Save .csv results to this folder", str(Path(global_data.data_file).parent)
        )
        for plot_name, plot_data in global_data.plot_data.items():
            for label_name, annotations in plot_data.annotations.items():
                if len(annotations.data) == 0:
                    continue
                annotations.data.to_csv(
                    directory + os.sep + plot_name.replace(" ", "_") + "_" + label_name.replace(" ", "_") + ".csv"
                )

        UserInformation.inform(f"The results were saved to {directory}.")


def decompress(bin_file):
    from datetime import datetime

    # value = np.uint8(data)
    hd = bin_file[0: 32]
    accx = []
    accy = []
    accz = []

    ts = np.frombuffer(bin_file[0:8], dtype=np.int64)[0]
    millis = int64_to_str(hd, True)
    GS = 8
    HZ = 12.5
    if hd[8] == 16:
        GS = 8
    elif hd[8] == 8:
        GS = 4
    elif hd[8] == 0:
        GS = 2
    if hd[9] == 0:
        HZ = 12.5
    elif hd[9] == 1:
        HZ = 25
    elif hd[9] == 2:
        HZ = 50
    elif hd[9] == 3:
        HZ = 100
    if HZ == 100:
        HZ = 90  # HACK!!
    delta = False
    deltaval = -1
    packt = 0
    sample = np.zeros(6, dtype='int64')
    # infoStr = "header: " + str(hd) + "\n" do not preceed with #!––
    lbls = []
    itr = 0
    for ii in range(32, len(bin_file) - 3, 3):  # iterate over data
        if (ii - 32) % 7200 == 0:
            pass
            # infoStr += "\n==== new page ====\n"  # mark start of new page
        if not delta:
            if (int(bin_file[ii]) == 255) and (int(bin_file[ii + 1]) == 255) and (packt == 0):  # delta starts
                if int(bin_file[ii + 2]) == 255:
                    pass
                    # infoStr += "\n*" + str((ii + 2)) + "\n"  # error -> this should only happen at the end of a page
                else:
                    # infoStr += "\nd" + value[ii + 2] + ":"
                    delta = True
                    deltaval = int(bin_file[ii + 2])
            else:
                if packt == 0:
                    sample[0] = int(bin_file[ii])
                    sample[1] = int(bin_file[ii + 1])
                    sample[2] = int(bin_file[ii + 2])
                    packt = 1
                else:
                    sample[3] = int(bin_file[ii])
                    sample[4] = int(bin_file[ii + 1])
                    sample[5] = int(bin_file[ii + 2])
                    packt = 0
                    mts = datetime.fromtimestamp(ts / 1000 + itr * (1000 / HZ) / 1000)
                    lbls.append(mts)
                    tmp = np.int16(sample[0] | (sample[1] << 8))
                    accx.append(round((tmp / 4096), 5))
                    tmp = np.int16(sample[2] | (sample[3] << 8))
                    accy.append(round((tmp / 4096), 5))
                    tmp = np.int16(sample[4] | (sample[5] << 8))
                    accz.append(round((tmp / 4096), 5))
                    itr += 1


        else:
            sample[0] = int(bin_file[ii])
            sample[2] = int(bin_file[ii + 1])
            sample[4] = int(bin_file[ii + 2])  # fill LSBs after delta
            mts = datetime.fromtimestamp(ts / 1000 + itr * (1000 / HZ) / 1000)
            lbls.append(mts)
            tmp = np.int16(sample[0] | (sample[1] << 8))
            accx.append(round((tmp / 4096), 5))
            tmp = np.int16(sample[2] | (sample[3] << 8))
            accy.append(round((tmp / 4096), 5))
            tmp = np.int16(sample[4] | (sample[5] << 8))
            accz.append(round((tmp / 4096), 5))
            itr += 1
            deltaval -= 1
            if (deltaval < 0):
                delta = False

    activity_data = np.array([accx, accy, accz], dtype=np.float64).T
    dataframe = pd.DataFrame(data=activity_data, columns=["x_axis", "y_axis", "z_axis"], index=lbls)
    dataframe = dataframe[~dataframe.index.duplicated(keep='first')]

    return dataframe


def int64_to_str(a, signed):
    import math

    negative = signed and a[7] >= 128
    H = 0x100000000
    D = 1000000000
    h = a[4] + a[5] * 0x100 + a[6] * 0x10000 + a[7] * 0x1000000
    l = a[0] + a[1] * 0x100 + a[2] * 0x10000 + a[3] * 0x1000000
    if negative:
        h = H - 1 - h
        l = H - l

    hd = math.floor(h * H / D + l / D)
    ld = (((h % D) * (H % D)) % D + l) % D
    ldStr = str(ld)
    ldLength = len(ldStr)
    sign = ''
    if negative:
        sign = '-'
    if hd != 0:
        result = sign + str(hd) + ('0' * (9 - ldLength))
    else:
        result = sign + ldStr

    return result


def readBinFile(path):
    bufferedReader = open(path, "rb")
    return bufferedReader.read()


def make_equidistant(subject_files, new_freq):
    # true_freqs = []
    new_freq_ms = int(((1 / new_freq) * 1000))

    for fc in range(len(subject_files)):
        current_df = subject_files[fc]
        if fc != len(subject_files) - 1:
            next_df = subject_files[fc + 1]

            current_df = current_df.append(next_df.iloc[0], ignore_index=False)
            t = pd.date_range(start=current_df.index[0],
                              end=current_df.index[-1],
                              periods=current_df.shape[0])
            current_df = current_df.set_index(t)[:-1]

        else:
            new_range = pd.date_range(current_df.index[0], current_df.index[-1],
                                      freq=str(round(new_freq_ms)) + "ms")

            current_df = current_df.set_index(pd.DatetimeIndex(new_range))

        subject_files[fc] = current_df
        # true_freqs.append(round(np.mean(checkfordrift(current_df))))

    return subject_files


def checkfordrift(df):
    timestamps = df.index
    counter = 1
    true_freqs = []
    last = None
    for entry in timestamps:
        second = entry.second
        if last is not None:
            if second != last:
                true_freqs.append(counter)
                counter = 1
            else:
                counter = counter + 1
        last = second

    return true_freqs


def resample_raw_data(data: pd.DataFrame, new_freq):
    new_freq_ms = int(((1 / new_freq) * 1000))
    data = data.resample(str(round(new_freq_ms)) + "ms").mean()
    data = data.interpolate()
    data = data.reset_index()
    # datetime.datetime.strptime(data.index, '%H:%M:%S.%f')

    return data


def get_all_daily_files(file_path):
    import glob
    import pathlib

    path = pathlib.Path(file_path).parent.resolve()
    try:
        bangle_id, filename = file_path.split("/")[-1].split("_")
    except:
        filename = file_path.split("/")[-1].split("_")[0]
    day = filename[5:9]
    all_file_paths = glob.glob(str(path) + "/" + "*.bin")
    daily_files = []
    if 'bangle_id' in locals():
        for file in all_file_paths:
            filename = file.split("/")[-1]
            if filename.__contains__(day) and filename.__contains__("_d"):
                daily_files.append(file)
    else :
        for file in all_file_paths:
            filename = file.split("/")[-1]
            if filename.__contains__(day):
                daily_files.append(file)
    daily_files = sorted(daily_files)

    return daily_files

# pseude code zum Einlesen der Binärdateien
# _____________________________________________


# Erklärung:
# 1.) Du musst zunächst jede Binärdatei einzeln dekomprimieren und
# 2.) anschließend zu einem einzigen Array konkatenieren.
# 3.) make_equidistant berechnet dir equidistante Zeitstempel zwischen den Samples. Das muss gemacht werden,
#       weil die Sensoren nicht 100% zuverlässig mit der gewünschten Frequenz samplen und oftmals vereinzelnd Samples fehlen.
# 4.) resample_raw_data resampled dir dann die Daten mit der gewünschten Frequenz und den neuen Zeitstempeln.

# Sag bescheid, wenn du was nicht verstehst oder du Bugs findest. Vielleicht findest du auch noch die eine oder andere Zeile Code, die optimiert werden kann.
