import os
import platform
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar


def test_polaczenia():
    popup = QMessageBox()
    popup.setIcon(QMessageBox.Information)
    popup.setWindowTitle("test polaczenia")



    if platform.system().lower() == "windows":
         response = os.system("ping -n 1 google.com")
    else:
         response = os.system("ping -c 1 google.com")
    


    if response == 0:
        print("Posiadasz polaczenie z internetem")
        
    else:
        print("Nie posiadasz internetu")
        popup.setText("Uwaga nie posiadasz polaczenia z internetem")
        popup.exec_()


# def test_polaczenia_popup():

#     popup = QMessageBox()
#     popup.setIcon(QMessageBox.Information)
#     popup.setWindowTitle("test polaczenia")

#     if platform.system().lower() == "windows":
#         response = subprocess.run(
#     ["ping", "-n", "1", "8.8.8.8"], 
#     stdout=subprocess.PIPE, 
#     stderr=subprocess.PIPE, 
#     startupinfo=startupinfo)
#     else:
#         response = subprocess.run(
#     ["ping", "-c", "1", "8.8.8.8"], 
#     stdout=subprocess.PIPE, 
#     stderr=subprocess.PIPE, 
#     startupinfo=startupinfo)
    
#     if response == 0:
#         popup.setText("Posiadasz polaczenie z internetem")
#         popup.exec_()
    
#     else:
#         popup.setText("Nie Posiadasz polaczenia z internetem")
#         popup.exec_()




        

