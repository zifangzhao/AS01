import os
import psutil
import sys
import glob
import time
import threading
import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog as tkFile
import tkinter.ttk as ttk
import tkfilebrowser as tkBro
import shutil
import struct
import importlib.util
import importlib.machinery
from openNSX import NsxFile
from PRM_template import *
from sys import platform
import re
from tkinter import simpledialog
import h5py


class GUIMain:
    def __init__(self):
        self.threads = []
        self.threads_manager = []
        self.threads_states = []
        self.thread_flag = 0
        self.file_state_color = ['white', 'lightgrey', 'gold', 'palegreen', 'orange','skyblue']
        self.file_state_name = ['no supported file found', 'vendor specific file found', 'dat file found',
                                'kwik file found', 'processing','preparing']

        self.win = tk.Tk()
        self.win.minsize(800, 600)
        self.win.title('AS01 Automatic Spike Sorting System')

        # menu definition
        menubar = tk.Menu(self.win)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Probe file generator", command=self.PrbGenerator)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.win.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.win.config(menu=menubar)

        # right side function area
        self.tkText1 = tk.Label(self.win, text='Files to be processed', width=110, anchor='w')
        self.tkText2 = tk.Label(self.win, text='CPU Usage', width=12)
        self.tkText3 = tk.Label(self.win, text='Memory Usage', width=12)
        self.tkText4 = tk.Label(self.win, text='Progress', width=12)
        self.tkText5 = tk.Label(self.win, text='Probe File:', width=20, anchor='w')
        self.tkTextPrbPath = tk.Label(self.win, text='', width=25)

        scrollbar = tk.Scrollbar(self.win)

        self.tkFilelist = tk.Listbox(self.win, selectmode='extended', width=80, yscrollcommand=tk)
        self.tkFilelist.bind("<Double-Button-1>", self.PreviewKwikFile)
        # bind listbox for deselecting all after lose focus
        self.tkFilelist.bind('<FocusOut>', lambda e: self.tkFilelist.selection_clear(0, tk.END))
        self.tkFileLegend = tk.Listbox(self.win, selectmode='extended', width=24, height=7, yscrollcommand=tk)
        for x in range(len(self.file_state_name)):
            self.tkFileLegend.insert(tk.END, self.file_state_name[x])
            self.tkFileLegend.itemconfig(tk.END, bg=self.file_state_color[x])

        self.tkButtonSelectProbeFile = tk.Button(self.win, text='Select Probe File', command=self.SelectProbeFile,
                                                 width=20,
                                                 height=3)
        self.tkButtonParameterSetting = tk.Button(self.win, text='Parameter Setting', command=self.ParameterControl,
                                                  width=20,
                                                  height=3)
        self.tkButtonAddFile = tk.Button(self.win, text='Add File to List', command=self.AddFile, width=20, height=3)
        self.tkButtonDelFile = tk.Button(self.win, text='Remove Selection', command=self.DelFile, width=20, height=3)
        self.tkButtonStart = tk.Button(self.win, text='Start Processing', command=self.StartProcessFiles, width=20,
                                       height=3)
        self.tkButtonStop = tk.Button(self.win, text='Stop Processing', command=self.KillProcess, width=20, height=3,
                                      state='disabled')

        self.pbCPU = ttk.Progressbar(self.win, maximum=100, value=0)
        self.pbMEM = ttk.Progressbar(self.win, maximum=100, value=0)
        self.pbPROG = ttk.Progressbar(self.win, maximum=100, value=0)

        # Stack GUI together

        self.tkText1.pack(side=tk.TOP)
        self.tkFilelist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=2)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.tkText5.pack(side=tk.TOP)
        self.tkTextPrbPath.pack(side=tk.TOP)
        self.tkButtonSelectProbeFile.pack(side=tk.TOP, padx=5)
        self.tkButtonParameterSetting.pack(side=tk.TOP, padx=5)
        self.tkButtonAddFile.pack(side=tk.TOP, padx=5)
        self.tkButtonDelFile.pack(side=tk.TOP, padx=5)
        self.tkButtonStart.pack(side=tk.TOP, padx=5)
        self.tkButtonStop.pack(side=tk.TOP, padx=5)
        self.tkText2.pack(side=tk.TOP)
        self.pbCPU.pack(side=tk.TOP, pady=5)
        self.tkText3.pack(side=tk.TOP)
        self.pbMEM.pack(side=tk.TOP, pady=5)
        self.tkText4.pack(side=tk.TOP)
        self.pbPROG.pack(side=tk.TOP, pady=5)
        self.tkFileLegend.pack(side=tk.TOP, pady=5)


        self.UpdateCoreUsage()  # start updating usage meters

        # create class for parameter setting
        self.param_control = GUIParameterControl(self.win)

        self.win.mainloop()

    def QueryFileState(self, path):
        files = os.listdir(path)
        ns6found = 0
        ns6file = []
        kwikfound = 0
        kwikfile = []
        datfound = 0
        datfile = []
        threadfound = 0
        procfound=0
        for x in files:
            if x.find('AS01.proc') != -1:
                procfound = 1
            if x.find('AS01.state') != -1:
                threadfound = 1
            if x.find('.kwik') != -1:
                kwikfound = 1
                kwikfile = path + '/' + x
            if x.find('.dat') != -1:
                datfound = 1
                datfile = path + '/' + x
            if x.find('.ns6') != -1:
                ns6found = 1
                ns6file = path + '/' + x
        if procfound:
            return 5, datfile, kwikfile, ns6file
        if threadfound:
            return 4, datfile, kwikfile, ns6file
        if kwikfound:
            return 3, datfile, kwikfile, ns6file
        if datfound:
            return 2, datfile, kwikfile, ns6file
        if ns6found:
            return 1, datfile, kwikfile, ns6file
        return 0, datfile, kwikfile, ns6file

    def SelectProbeFile(self):
        prbfile = tkBro.askopenfilename(initialdir="/usr/local/bin/cereloop/map/", title="Select Probe file(*.prb)",
                                        filetypes=(("probe files", "*.prb"),))
        self.tkTextPrbPath.config(text=prbfile)

    def AddFile(self):
        dirlist = (tkBro.askopendirnames())
        for x in dirlist:
            self.tkFilelist.insert(tk.END, x)
            state = self.QueryFileState(x)
            self.tkFilelist.itemconfig(tk.END, bg=self.file_state_color[state[0]])

    def UpdateFileState(self):
        for x in range(self.tkFilelist.size()):
            state = self.QueryFileState(self.tkFilelist.get(x))
            self.tkFilelist.itemconfig(x, bg=self.file_state_color[state[0]])
        return 0

    def DelFile(self):
        sel = self.tkFilelist.curselection()
        for x in sel[::-1]:
            self.tkFilelist.delete(x)

    def StartProcessFiles(self):
        self.thread_flag = 0  # send stop signal to all threads
        if self.threads_manager != []:
            tk.messagebox.showwarning(title="Action might needed",
                                      message="Close any previous opened command windows before continuing")

        self.tkButtonSelectProbeFile.config(state='disabled')
        self.tkButtonAddFile.config(state='disabled')
        self.tkButtonDelFile.config(state='disabled')
        self.tkButtonStart.config(state='disabled')
        self.tkButtonStop.config(state='normal')

        self.threads.clear()  # clear threading list
        self.threads_states.clear()

        self.threads_preprocessing = threading.Thread(target=self.Preprocessing)
        self.threads_preprocessing.start()
    def Preprocessing(self):
        # Stopping any existing job-submitter

        for x in range(self.tkFilelist.size()):
            # StartProcess(self.tkFilelist.get(x))
            path = self.tkFilelist.get(x)
            rst = self.QueryFileState(path)
            self.run_greenlight = 0


            if rst[0] == 1:  # NS6 file need to be converted
                # create a temp file to indicate file is being processed
                s = os.path.sep
                f = open(path + s + 'AS01.proc', 'w')
                f.close()
                self.UpdateFileState()
                nsxfile = NsxFile(rst[3])
                nsxfile.ConvertToDat(
                    res_fs=self.param_control.GetSamplingRate())  # resample to the fs specified in param_control
                Nch = nsxfile.channel_count

                if platform == "linux" or platform == "linux2":
                    cmd = 'rm "' + path + s + 'AS01.proc"'
                elif platform == "win32" or platform == "win64":
                    cmd = 'del "' + path + s + 'AS01.proc"'
                os.system(cmd)
                rst = self.QueryFileState(path)  # check again

            if rst[0] == 2:  # DAT file(only) found
                if self.tkTextPrbPath['text'] == '':
                    tk.messagebox.showwarning(title="Probe file not selected", message="Select a probe map first!")
                    return -1
                self.run_greenlight = 1
            if rst[0] == 3:  # Kwik found
                answer = tk.messagebox.askyesno(title="Calculated file found",
                                                message="Sorting data found in " + path + ", re-process data?")
                if answer == True:
                    self.run_greenlight = 1
            if rst[0] == 4:  # running thread found
                answer = tk.messagebox.askyesno(title="Process might still ongoing",
                                                message="File might be still under processing " + path + ", re-process data?")
                if answer == True:
                    self.run_greenlight = 1

            if self.run_greenlight == 1:
                # create a temp file to indicate file is being processed
                s = os.path.sep
                f = open(path + s + 'AS01.state', 'w')
                f.close()
                self.UpdateFileState()
                t = threading.Thread(target=self.ProcessData, args=(self.tkFilelist.get(x),), name=x)
                self.threads.append(t)
                self.threads_states.append(0)

        # Execute a new job-submitter
        self.thread_flag = 1
        self.threads_manager = threading.Thread(target=self.SubmitJobs)
        self.threads_manager.start()
        return 0

    def SubmitJobs(self):
        for x in range(len(self.threads)):
            cpu, mem, running = self.QueryCoreUsage()
            while (cpu > 70 or mem > 70 or running > 4):
                time.sleep(1)  # wait until resource become available
                if self.thread_flag == 0:
                    self.ProcessFinishup()
                    return -1
            if self.thread_flag == 0:
                self.ProcessFinishup()
                return -1
            self.threads[x].start()
            self.threads_states[x] = 1
            time.sleep(60)  # wait at least 60s to start another job
        self.ProcessFinishup()
        return 0

    def ProcessData(self, path):
        rst = self.QueryFileState(path)
        self.run_greenlight = 1
        if self.run_greenlight == 1:
            self.PrmGeneration(path, rst[1], self.tkTextPrbPath['text'])

            if platform == "linux" or platform == "linux2":
                cmd = 'gnome-terminal --disable-factory --title="Running Spike Sorting:' + path + '" -x sh -c "PATH=~/anaconda3/envs/phy2/bin:$PATH && cd \'' + path + '\' && klusta \'' + path + '/process.prm\' --legacy-output --overwrite && rm AS01.state"'
            elif platform == "win32" or platform == "win64":
                cmd = 'start "Running Spike Sorting:' + path + '" cmd /c "C:\%HOMEPATH%\\anaconda3\\Scripts\\activate.bat&conda activate phy2&cd /d ' + path + '&klusta process.prm --legacy-output --overwrite & del AS01.state"'
            # print(cmd)
            os.system(cmd)
            self.UpdateFileState() #update file display state
            # check if command is successfully executed

        return 0

    def KillProcess(self):
        self.thread_flag = 0
        self.ProcessFinishup()
        return 0

    def ProcessFinishup(self):
        self.tkButtonSelectProbeFile.config(state='normal')
        self.tkButtonAddFile.config(state='normal')
        self.tkButtonDelFile.config(state='normal')
        self.tkButtonStart.config(state='normal')
        self.tkButtonStop.config(state='disabled')
        return 0

    def PrmGeneration(self, path, datfile, prbfile):
        try:
            shutil.copy(prbfile, path)  # copy probe file to local folder
        finally:
            #extract information from .prb file
            loader = importlib.machinery.SourceFileLoader('channel_groups', prbfile)
            spec = importlib.util.spec_from_loader(loader.name, loader)
            mod = importlib.util.module_from_spec(spec)
            loader.exec_module(mod)
            Nch = sum([len(mod.channel_groups[x]['channels']) for x in range(len(mod.channel_groups))])
            (filepath, tempfilename) = os.path.split(datfile)
            (filename, extension) = os.path.splitext(tempfilename)
            (filepath, tempfilename) = os.path.split(prbfile)
            (prbname, extension) = os.path.splitext(tempfilename)

            #generate PRM file
            # f_temp=open("/usr/local/bin/cereloop/process.prm",'r')
            # f_temp = open("H:\data\Sorting\CAS\data.prm", 'r')
            # lines=f_temp.readlines()
            # f_temp.close()
            # lines = PRM_template
            f_new = open(path + '/process.prm', "w")
            f_new.write(self.param_control.ParseParamtoText(filename,prbname+'.prb',Nch))
            # print(filename)
            # f_new.write("experiment_name = '" + filename + "'\n")
            # f_new.write("prb_file = '" + prbname + ".prb'\n")
            # f_new.write("Nch = " + str(Nch) + "\n")
            # [f_new.write(x) for x in lines]
            f_new.close()

            return 0

    def QueryCoreUsage(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        running = 0
        self.pbCPU['value'] = cpu
        self.pbMEM['value'] = mem
        if len(self.threads) > 1:
            cnt = len(self.threads) - 1
            finished = sum([x == 2 for x in self.threads_states])
            running = sum([x == 1 for x in self.threads_states])
            self.pbPROG['value'] = finished / cnt * 100
            if (finished == cnt):
                # threads.clear()
                # threads_states.clear()
                self.UpdateFileState()
        else:
            self.pbPROG['value'] = 0
            self.UpdateFileState()

        return cpu, mem, running

    def UpdateCoreUsage(self):
        self.QueryCoreUsage()
        usageTimer = threading.Timer(1, self.UpdateCoreUsage)
        usageTimer.start()
        return 0

    def PreviewKwikFile(self):
        for x in self.tkFilelist.curselection():
            rst = self.QueryFileState(self.tkFilelist.get(x))
            if rst[0] == 3:
                filename=rst[2]
                f = h5py.File(filename, 'r')  # open kwik file
                N_grp = len(f['channel_groups'])

                filepart = os.path.split(filename)
                path = filepart[0]
                if N_grp > 1:
                    application_window = tk.Tk()
                    sel_grp = simpledialog.askinteger("Input",
                                                      "Select a channel group to open:[0-" + str(N_grp - 1) + ']',
                                                      parent=application_window,
                                                      minvalue=0, maxvalue=100)
                    application_window.destroy()
                    if platform == "linux" or platform == "linux2":
                        cmd = 'gnome-terminal --disable-factory --title="Starting kwik-GUI" -x sh -c "PATH=~/anaconda3/envs/phy2/bin:$PATH && phy kwik-gui '
                        + filename + ' --channel-group=' + str(sel_grp) + '"'
                    elif platform == "win32" or platform == "win64":
                        cmd = 'start "Starting kwik-GUI":" cmd /c "C:\%HOMEPATH%\\anaconda3\\Scripts\\activate.bat&conda activate phy2&phy kwik-gui ' + filename + ' --channel-group=' + str(
                            sel_grp) + '"'
                        # print(cmd)
                    os.system(cmd)
                else:
                    if platform == "linux" or platform == "linux2":
                        cmd = 'gnome-terminal --disable-factory --title="Running Spike Sorting:' + path + '" -x sh -c "PATH=~/anaconda3/envs/phy2/bin:$PATH && phy kwik-gui' + filename + '"'
                    elif platform == "win32" or platform == "win64":
                        cmd = 'start "Running Spike Sorting:' + path + '" cmd /c "C:\%HOMEPATH%\\anaconda3\\Scripts\\activate.bat&conda activate phy2&phy kwik-gui ' + filename + '"'
                        # print(cmd)
                    os.system(cmd)

                # if platform == "linux" or platform == "linux2":
                #     tmpcmd = 'PATH=~/anaconda3/envs/phy2/bin:$PATH && echo $PATH && phy kwik-gui \'' + rst[2] + '\''
                # elif platform == "win32" or platform == "win64":
                #     tmpcmd = 'start "Opening sorting GUI:" cmd /c "C:\\Users\\Frank-G5\\anaconda3\\Scripts\\activate.bat & conda activate phy2 & phy kwik-gui ' + \
                #              rst[2] + '"'
                # # print(cmd)
                # os.system(tmpcmd)
        return 0

    def ParameterControl(self):
        self.param_control.user_input()
        self.win.wait_window(self.param_control.win)
        return 0

    def PrbGenerator(self):
        return 0


class GUIParameterControl:
    def __init__(self, parent):
        self.PRMtext = ""
        self.paramlist_traces = [['voltage_gain', '10.0'], ['sample_rate', '20000'], ['dtype', '\'int16\'']]
        self.paramlist_spikes = [['filter_low', '500'], ['filter_high_factor', '0.48'], ['filter_butter_order', '3'],
                                 ['filter_lfp_low', '0'], ['filter_lfp_high', '300']
            , ['chunk_size_seconds', '1'], ['chunk_overlap_seconds', '0.015'], ['n_excerpts', '50'],
                                 ['excerpt_size_seconds', '1'], ['threshold_strong_std_factor', '4.5']
            , ['threshold_weak_std_factor', '2.0'], ['connected_component_join_size', '1'], ['extract_s_before', '16']
            , ['extract_s_after', '16'], ['n_features_per_channel', '3'], ['pca_n_waveforms_max', '1000'],
                                 ['detect_spikes', '\'negative\'']]
        self.paramlist_kk = [['num_starting_clusters', '100']]
        self.parent=parent
    
    def update_params(self):
        p_trace=([x.get() for x in self.tk_string_param_traces])
        p_spike=([x.get() for x in self.tk_entry_param_spikes])
        p_kk=([x.get() for x in self.tk_entry_param_kk])
        for x in range(len(p_trace)):
            self.paramlist_traces[x][1]=p_trace[x]
        for x in range(len(p_spike)):
            self.paramlist_spikes[x][1]=p_spike[x]
        for x in range(len(p_kk)):
            self.paramlist_kk[x][1]=p_kk[x]
    
    def user_input(self):
        self.win = tk.Toplevel(self.parent)
        self.win.minsize(450, 600)
        self.win.title = "Parameter Control"

        # add widget to window
        # seperator
        self.tk_label_group1 = tk.Label(self.win, text='File Parameters', width=20, height=2, anchor='w')
        self.tk_label_group1.grid(column=0, row=0)
        # label
        self.tk_label_param_traces = [tk.Label(self.win, text=x[0] + ' = ', width=30, anchor='e') for x in
                                      self.paramlist_traces]
        n_param_traces = len(self.tk_label_param_traces)
        [self.tk_label_param_traces[x].grid(column=0, row=x + 1) for x in range(n_param_traces)]
        # input
        self.tk_string_param_traces = [tk.StringVar(self.win, value=x[1]) for x in self.paramlist_traces]
        self.tk_entry_param_traces = [tk.Entry(self.win, textvariable=x, width=30) for x in self.tk_string_param_traces]
        [self.tk_entry_param_traces[x].grid(column=1, row=x + 1) for x in range(n_param_traces)]

        # group2
        # separator
        self.tk_label_group2 = tk.Label(self.win, text='Spike Sorting Parameters', width=20, height=2, anchor='w')
        self.tk_label_group2.grid(column=0, row=n_param_traces + 1)
        # label
        self.tk_label_param_spikes = [tk.Label(self.win, text=x[0] + ' = ', width=30, anchor='e') for x in
                                      self.paramlist_spikes]
        n_param_spikes = len(self.tk_label_param_spikes)
        [self.tk_label_param_spikes[x].grid(column=0, row=x + n_param_traces + 2) for x in range(n_param_spikes)]
        # input
        self.tk_string_param_spikes = [tk.StringVar(self.win, value=x[1]) for x in self.paramlist_spikes[:-1]]
        self.tk_entry_param_spikes = [tk.Entry(self.win, textvariable=x, width=30) for x in self.tk_string_param_spikes]
        # combobox style
        self.tk_entry_param_spikes.append(ttk.Combobox(self.win, values=['\'negative\'', '\'positive\''], width=27))
        self.tk_entry_param_spikes[-1].current(0)
        [self.tk_entry_param_spikes[x].grid(column=1, row=x + n_param_traces + 2) for x in range(n_param_spikes)]

        # group3
        # seperator
        self.tk_label_group3 = tk.Label(self.win, text='KlustaKwik Parameters', width=20, height=2, anchor='w')
        self.tk_label_group3.grid(column=0, row=n_param_traces + n_param_spikes + 2)
        # label
        self.tk_label_param_kk = [tk.Label(self.win, text=x[0] + ' = ', width=30, anchor='e') for x in
                                  self.paramlist_kk]
        n_param_kk = len(self.tk_label_param_kk)
        [self.tk_label_param_kk[x].grid(column=0, row=x + n_param_traces + n_param_spikes + 2) for x in
         range(n_param_kk)]
        # input
        self.tk_string_param_kk = [tk.StringVar(self.win, value=x[1]) for x in self.paramlist_kk]
        self.tk_entry_param_kk = [tk.Entry(self.win, textvariable=x, width=30) for x in self.tk_string_param_kk]
        [self.tk_entry_param_kk[x].grid(column=1, row=x + n_param_traces + n_param_spikes + 2) for x in
         range(n_param_kk)]

        # button
        self.tkButtonOK = tk.Button(self.win, text='Ok', command=self.SubmitParam, width=20, height=2,
                                    state='normal')
        self.tkButtonCancel = tk.Button(self.win, text='Cancel', command=self.win.destroy, width=20, height=2,
                                        state='normal')
        self.tkButtonOK.grid(column=0, row=n_param_traces + n_param_spikes + n_param_kk + 3, pady=15)
        self.tkButtonCancel.grid(column=1, row=n_param_traces + n_param_spikes + n_param_kk + 3, pady=15)

    def SubmitParam(self):
        # Check  parameter first
        test = [re.match(r'^-?\d+\.?\d*$', x.get()) != None for x in self.tk_string_param_traces[0:-1]]
        test1 = [re.match(r'^-?\d+\.?\d*$', x.get()) != None for x in self.tk_entry_param_spikes[0:-1]]
        test2 = [re.match(r'^\d+$', x.get()) != None for x in self.tk_entry_param_kk]
        test_idx = [i for i, val in enumerate(test) if val == False]
        test1_idx = [i for i, val in enumerate(test1) if val == False]
        test2_idx = [i for i, val in enumerate(test2) if val == False]
        msglist = []
        if test_idx != []:
            ([msglist.append('\t\t' + self.paramlist_traces[x][0] + '\n') for x in test_idx])
        if test1_idx != []:
            ([msglist.append('\t\t' + self.paramlist_spikes[x][0] + '\n') for x in test1_idx])
        if test2_idx != []:
            ([msglist.append('\t\t' + self.paramlist_kk[x][0] + '\n') for x in test2_idx])
        if msglist != []:
            msg = ' '.join(msglist)
            tk.messagebox.showerror(title='Check Parameter', message='Incorrect parameters:\n' + msg)
        else:
            self.update_params()
            self.win.destroy()

    def ParseParamtoText(self, filebase, prb_file,Nch):
        temp_txt = []
        temp_txt.append("experiment_name = \'" + filebase +'\'\n')
        temp_txt.append("prb_file = \'" + prb_file +'\'\n')
        temp_txt.append("Nch = " + str(Nch) + '\n')
        temp_txt.append("traces = dict(\n")
        temp_txt.append("\traw_data_files=[experiment_name + \'.dat\'],\n")
        temp_txt.append("\tn_channels=Nch,\n")
        [temp_txt.append("\t" + self.paramlist_traces[x][0] + ' = ' + self.paramlist_traces[x][1] + ",\n") for x in
         range(len(self.paramlist_traces))]
        temp_txt.append(")\n")

        temp_txt.append("spikedetekt = dict(\n")
        [temp_txt.append("\t" + self.paramlist_spikes[x][0] + ' = ' + self.paramlist_spikes[x][1] + ",\n") for x in
         range(len(self.paramlist_spikes))]
        temp_txt.append(")\n")

        temp_txt.append("klustakwik2 = dict(\n")
        [temp_txt.append("\t" + self.paramlist_kk[x][0] + ' = ' + self.paramlist_kk[x][1] + ",\n") for x in
         range(len(self.paramlist_kk))]
        temp_txt.append(")\n")
        self.PRMtext = "".join(temp_txt)
        return self.PRMtext

    def GetSamplingRate(self):
        fs=int(self.paramlist_traces[1][1])
        print("samplingRate=" +str(fs))
        return fs
# main GUI definition starts here
gui = GUIMain()
