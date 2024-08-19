import os
import psutil
import sys
import glob
import time


fpath=sys.argv[1]
#fpath=fpath[1:-1]
finfo=fpath.split('/')
filelist=finfo[-1]
filelist_new=filelist.replace(' ','_')
if(filelist != filelist_new):
    os.system('mv "' + filelist +'" "' + filelist_new + '"')
    filelist=filelist_new
    fpath=''
    for x in finfo[:-1]:
        fpath=fpath+ x +'/'
    fpath=fpath+filelist_new
#fpath=fpath.replace(' ','\\ ')
fdat=glob.glob(fpath+'/*.dat')+glob.glob(fpath+'/*.DAT')
# print('"' + fpath+'/*.dat"')
fdat=fdat[0]
fdat_new=os.getcwd() + '/' + filelist + '/' + filelist + '.dat' 
cmd_mov='mv "' + fdat + '" "' +  fdat_new +'"'

# print(cmd_mov)
os.system(cmd_mov)

cmd_ndm="ndm_start proc.xml \"" + filelist + '\"'
print(cmd_ndm)
os.system(cmd_ndm)

os.chdir(os.getcwd()+'/'+ filelist)
fet_files=glob.glob(os.getcwd()+'/*.fet.*')
for i in range(len(fet_files)):
    while psutil.cpu_percent()>90:
        print('CPU load is high, wait 5 second to re-submit the job')
        time.sleep(5)
    file=fet_files[i][fet_files[i].rfind('/')+1:]
    idx=file.find('.fet.')
    file_short=file[0:file.rfind('.')]
    cmd_klu='gnome-terminal -t "Running Clustering:' + file_short[0:file_short.rfind('.')] + ':' +str(i) +'" '
    cmd_klu=cmd_klu+'--tab -- bash -c "KlustaKwik \'' + file_short[0:file_short.rfind('.')] + '\' \'' +  file[idx+5:]  + '\' -MinClusters 20 -MaxClusters 30 -MaxPossibleClusters 50 ;"'
    #print(cmd_klu)
    os.system(cmd_klu)
    print('Job submitted:' + str(i+1) + '/' + str(len(fet_files)))
print('All job submitted! Wait till all tasks finishes')
    
