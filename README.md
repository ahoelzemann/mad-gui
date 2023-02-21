# How to install the software:

you will need to have git https://git-scm.com/ and anaconda https://www.anaconda.com/ installed
1. make sure that both packages are installed
2. create a virgin python 3.8 environment by executing **_conda create -n mypython38 python=3.8_**  **_!!! you can change the name from mypython38 to something else !!!_**
3. clone this repository by executing **_git clone https://github.com/ahoelzemann/mad-gui-adaptions.git_**
4. cd into the new folder
5. execute the following command in your terminal: **_git submodule update --init --recursive_**
6. activate your new conda environment **_conda activate mypython38_**
7. install all needed requirements by running  **_pip install -r requirements.txt_**
8. run the GUI **_python main.py_**


For more information about the software itself please visit https://github.com/mad-lab-fau/mad-gui
