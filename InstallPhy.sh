#!/bin/bash
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --set show_channel_urls yes
conda create -n phy2 python=3.7 pip numpy matplotlib scipy scikit-learn h5py cython pillow -y
conda activate phy2
pip install phy --pre --upgrade
pip install klusta klustakwik2
pip install klusta phy phycontrib --upgrade
pip install psutil
pip install tkfilebrowser