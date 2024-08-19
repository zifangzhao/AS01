import os
import psutil
import sys
import glob
import time


fpath=sys.argv[1]
#fpath=fpath[1:-1]
finfo=fpath.split('/')
filelist=finfo[-1]


fnsx=glob.glob(fpath+'/*.ns5')+glob.glob(fpath+'/*.ns6')
cmd_nsx2dat='/usr/local/bin/cereloop/nsx2dat "'+fnsx[0] +'"'
os.system(cmd_nsx2dat)

fdat=glob.glob(fpath+'/*.dat')+glob.glob(fpath+'/*.DAT')
fdat=fdat[0]
fdat_new=os.getcwd() + '/' + filelist + '/' + 'proc-30000.dat' 
cmd_mov='mv ' + fdat.replace(' ','\ ') + ' ' +  fdat_new.replace(' ','\ ') +''
os.system(cmd_mov)

os.system('cp "' + os.getcwd() + '/proc.xml" "' + os.getcwd() + '/' + filelist + '/proc.xml"')
os.chdir(os.getcwd()+'/'+ filelist)

cmd_ndm="ndm_resample proc.xml"

os.system(cmd_ndm)

os.system('mv proc-30000.dat ' + filelist + '.dat') 


