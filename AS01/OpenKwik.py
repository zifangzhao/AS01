import os
import sys
import tkinter as tk
from tkinter import simpledialog
from sys import platform
import h5py

filename=sys.argv[1]
#filename=r'D:\klusta\hybrid_10sec.kwik'
#filename=r'H:\Test_32ch_tetrode\20170430_laser_170430_131343.kwik'
#print(filename)
f = h5py.File(filename,'r') #open kwik file
N_grp=len(f['channel_groups'])
#N_grp=1
filepart=os.path.split(filename)
path=filepart[0]
if N_grp>1:
    print('Group selection mode')
    application_window = tk.Tk()
    application_window.withdraw() #hide main window
    sel_grp = simpledialog.askinteger("Input", "Select a channel group to open:[0-" + str(N_grp-1) + ']',initialvalue='0',
                                     minvalue=0, maxvalue=100)
    application_window.destroy()
    if platform == "linux" or platform == "linux2":
        cmd = 'gnome-terminal --disable-factory --title="Starting kwik-GUI" -x sh -c "PATH=~/anaconda3/envs/phy2/bin:$PATH && phy kwik-gui '
        + filename + ' --channel-group=' +str(sel_grp) + '"'
    elif platform == "win32" or platform == "win64":
        cmd = 'start "Starting kwik-GUI":" cmd /c "C:\%HOMEPATH%\\anaconda3\\Scripts\\activate.bat&conda activate phy2&phy kwik-gui ' + filename + ' --channel-group=' +str(sel_grp) + '"'
        # print(cmd)
    os.system(cmd)
else:
    print('Default mode')
    if platform == "linux" or platform == "linux2":
        cmd = 'gnome-terminal --disable-factory --title="Running kwik-GUI:' + path + '" -x sh -c "PATH=~/anaconda3/envs/phy2/bin:$PATH && phy kwik-gui' + filename +'"'
    elif platform == "win32" or platform == "win64":
        cmd = 'start "Running kwik-GUI:' + path + '" cmd /c "C:\%HOMEPATH%\\anaconda3\\Scripts\\activate.bat&conda activate phy2&phy kwik-gui ' + filename +'"'
        # print(cmd)
    os.system(cmd)