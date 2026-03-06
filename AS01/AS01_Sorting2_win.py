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

def QueryState(path):
    files=os.listdir(path)
    ns6found=0;
    ns6file=[];
    kwikfound=0
    kwikfile=[]
    datfound=0
    datfile=[]
    for x in files:
        if x.find('.kwik')!=-1:
            kwikfound=1
            kwikfile=path+'/'+x
        if x.find('.dat')!=-1:
            datfound=1
            datfile=path+'/'+x
        if x.find('.ns6')!=-1:
            ns6found=1
            ns6file=path+'/'+x
    if kwikfound:
        return 3,datfile,kwikfile,ns6file
    if datfound:
        return 2,datfile,kwikfile,ns6file
    if ns6found:
        return 1,datfile,kwikfile,ns6file
    return 0,datfile,kwikfile,ns6file

def SelectProbeFile():
    prbfile=tkBro.askopenfilename(initialdir = "/usr/local/bin/cereloop/map/",title = "Select Probe file(*.prb)",filetypes = (("probe files","*.prb"),))
    tkTextPrbPath.config(text=prbfile)
def AddFile():
    dirlist=(tkBro.askopendirnames())
    color=['white','grey', 'yellow', 'lawn green']
    for x in dirlist:
        tkFilelist.insert(tk.END, x)
        state=QueryState(x)
        tkFilelist.itemconfig(tk.END, bg=color[state[0]])

def UpdateFileState():
    color=['white','grey', 'yellow', 'lawn green']
    for x in range(tkFilelist.size()):
        state=QueryState(tkFilelist.get(x))
        tkFilelist.itemconfig(x, bg=color[state[0]])
    return 0

def DelFile():
    sel=tkFilelist.curselection()
    for x in sel[::-1]:
        tkFilelist.delete(x)

def ProcessFiles():
    threads.clear() #clear threading list
    threads_states.clear()
    for x in range(tkFilelist.size()):
        t = threading.Thread(target=StartProcess,args=(tkFilelist.get(x),),name=x)
        threads.append(t)
        threads_states.append(0)
    t=threading.Thread(target=SubmitJobs)
    threads.append(t)
    threads_states.append(0)
    t.start()
    return 0

def SubmitJobs():
    for x in range(len(threads)-1):
        cpu, mem ,running = QueryUsage()
        while(cpu>70 or mem>70 or running>4):
            time.sleep(5)
        threads[x].start()
        threads_states[x] = 1
    return 0

def StartProcess(path):
    rst=QueryState(path)
    if rst[0]==1: #NS6 file found
        cmd='gnome-terminal --disable-factory --title="Running Format Conversion:' + path + '" -x sh -c "PATH=/usr/local/bin/cereloop:$PATH && cd \'' + path + '\' && nsx2dat \'' + rst[3] +'\'"'
        #print(cmd)
        os.system(cmd)
        rst = QueryState(path)
        temp_file='temp30k.dat'
        shutil.move(rst[1],path+ "/" +temp_file)
        fh=open(rst[3],'rb')
        fh.seek(310,0);
        Nch=struct.unpack('I',fh.read(4))
        fh.close()
        #print(Nch)
        cmd='gnome-terminal --disable-factory --title="Running Format Conversion:' + path + '" -x sh -c "cd \'' + path + '\' && process_resample -c 2 -f 30000,20000 -n '  + str(Nch[0]) + ' ' + temp_file+ ' \'' + rst[1] +'\'"'
        #print(cmd)
        os.system(cmd)
        cmd='rm \'' + path + '/' + temp_file + '\''
        #print(cmd)
        os.system(cmd)
        rst = QueryState(path) #check again
    if rst[0]==2: #DAT file found
        if(tkTextPrbPath['text']==''):
            tk.messagebox.showwarning(title="Probe file not selected",message="Select a probe map first!")
            return -1
        PrmGeneration(path,rst[1],tkTextPrbPath['text'])
        cmd='gnome-terminal --disable-factory --title="Running Spike Sorting:' + path + '" -x sh -c "PATH=~/anaconda3/envs/phy2/bin:$PATH && cd \'' + path + '\' && klusta \'' + path + '/process.prm\'"'
        #print(cmd)
        os.system(cmd)
    return 0
def KillProcess():
    return 0

def PrmGeneration(path,datfile,prbfile):
    try:
        shutil.copy(prbfile,path) #copy probe file to local folder
    finally:
        loader = importlib.machinery.SourceFileLoader('channel_groups', prbfile)
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        Nch=sum([len(mod.channel_groups[x]['channels']) for x in range(len(mod.channel_groups))])
        (filepath, tempfilename) = os.path.split(datfile)
        (filename, extension) = os.path.splitext(tempfilename)
        (filepath, tempfilename) = os.path.split(prbfile)
        (prbname, extension) = os.path.splitext(tempfilename)
        f_temp=open("/usr/local/bin/cereloop/process.prm",'r')
        # f_temp = open("H:\data\Sorting\CAS\data.prm", 'r')
        lines=f_temp.readlines()
        f_temp.close()
        f_new=open(path+'/process.prm',"w")
        print(filename)
        f_new.write("experiment_name = '"+ filename + "'\n")
        f_new.write("prb_file = '" + prbname + ".prb'\n")
        f_new.write("Nch = " + str(Nch) + "\n")
        [f_new.write(x) for x in lines]
        f_new.close()
        return 0

def QueryUsage():
    cpu=psutil.cpu_percent()
    mem=psutil.virtual_memory().percent
    running=0
    pbCPU['value'] = cpu
    pbMEM['value'] = mem
    if len(threads) > 0:
        cnt = len(threads)-1
        finished=sum([x==2 for x in threads_states])
        running = sum([x == 1 for x in threads_states])
        pbPROG['value'] = finished/cnt*100
        color = ['white', 'yellow', 'lawn green', 'orange']
        for x in range(cnt):
            if threads_states[x] == 1:
                if(threads[x].is_alive() is True):
                    tkFilelist.itemconfig(x, bg=color[3])
                else:
                    threads_states[x] = 2
                    tkFilelist.itemconfig(x, bg=color[2])
        if(finished == cnt):
            # threads.clear()
            # threads_states.clear()
            UpdateFileState()
    else:
        pbPROG['value']=0
        UpdateFileState()

    return cpu,mem,running

def UpdateUsage():
    QueryUsage()
    usageTimer = threading.Timer(1, UpdateUsage)
    usageTimer.start()
    return 0

def PreviewFile(event):
    for x in tkFilelist.curselection():
        rst=QueryState(tkFilelist.get(x))
        if rst[0]==3:
            cmd='PATH=~/anaconda3/envs/phy2/bin:$PATH && echo $PATH && phy kwik-gui \''+rst[2] + '\''
            #print(cmd)
            os.system(cmd)
    return 0

def PrbGenerator():
    return 0
# main GUI definition starts here
threads = []
threads_states=[]
win=tk.Tk()
win.minsize(800,600)
win.title('AS01 Automatic Spike Sorting System')

#menu definition
menubar=tk.Menu(win)
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Probe file generator", command=PrbGenerator)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=win.quit)
menubar.add_cascade(label="File", menu=filemenu)
win.config(menu=menubar)

#right side function area
tkText1=tk.Label(win,text='Files to be processed                          ')
tkText2=tk.Label(win,text='CPU Usage',width=12)
tkText3=tk.Label(win,text='Memory Usage',width=12)
tkText4=tk.Label(win,text='Progress',width=12)
tkText5=tk.Label(win,text='Probe File:')
tkTextPrbPath=tk.Label(win, text='')

scrollbar=tk.Scrollbar(win)

tkFilelist=tk.Listbox(win,selectmode='extended',width=100,yscrollcommand=tk)
tkFilelist.bind("<Double-Button-1>",PreviewFile)

tkButtonSelectProbeFile=tk.Button(win,text='Select Probe File',command=SelectProbeFile,width=20,height=3)
tkButtonAddFile=tk.Button(win,text='Add File to List',command=AddFile,width=20,height=3)
tkButtonDelFile=tk.Button(win,text='Remove Selection', command=DelFile,width=20,height=3)
tkButtonStart=tk.Button(win,text='Start Processing', command=ProcessFiles,width=20,height=3)
tkButtonStop=tk.Button(win,text='Stop Processing', command=KillProcess,width=20,height=3)

pbCPU=ttk.Progressbar(win,maximum=100,value=0)
pbMEM=ttk.Progressbar(win,maximum=100,value=0)
pbPROG=ttk.Progressbar(win,maximum=100,value=0)

#Stack GUI together

tkText1.pack(side=tk.TOP)
tkFilelist.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=5,pady=10)
scrollbar.pack(side=tk.LEFT,fill=tk.Y)
tkText5.pack(side=tk.TOP)
tkTextPrbPath.pack(side=tk.TOP)
tkButtonSelectProbeFile.pack(side=tk.TOP,padx=5)
tkButtonAddFile.pack(side=tk.TOP,padx=5)
tkButtonDelFile.pack(side=tk.TOP,padx=5)
tkButtonStart.pack(side=tk.TOP,padx=5)
# tkButtonStop.pack(side=tk.TOP,padx=5)
tkText2.pack(side=tk.TOP)
pbCPU.pack(side=tk.TOP,pady=5)
tkText3.pack(side=tk.TOP)
pbMEM.pack(side=tk.TOP,pady=5)
tkText4.pack(side=tk.TOP)
pbPROG.pack(side=tk.TOP,pady=5)

#create CPU/MEM update
UpdateUsage() #start updating usage meters
win.mainloop()
