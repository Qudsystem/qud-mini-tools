import tkinter as tk 
from tkinter import messagebox 
import os 
  
# Creating master tkinter window 
master = tk.Tk() 
master.title ("Eng/ Hasan Orabi ")

  
# This Function will be used to ask user if he/she wants to check the password 
def check_password(): 
  
    # WPA and WPS Network Passwords are stored in this dictionary, users should enter the exact name of the network they want to hack 
    passwords = {'orabi': '09876543@#', 'TPLink': '12345678', 'oppo': 'hello123', 'Belkin': 'helloworld', 'Hello': '01065016','Oppo':'0106516200@#'} 
       
    # Get the name of the network  
    net_name = entry.get() 
  
    # Get the password for the entered network name 
    passw = passwords.get(net_name) 
      
    # creating tkinter window 
    window = tk.Tk() 
      
    # This will create a label widget 
    # Label widgets are used to create text labels 
    l1 = tk.Label(window, text ='The Password for this Network is : ' +str( passw)) 
    l1.pack()  
  
    b1 = tk.Button(window, text ='OK', command = window.destroy) 
    b1.pack()   
          
    window.mainloop() 
  
# Setting geometry of master 
master.geometry("250x250") 
  
# This will create a label widget 
# Label widgets are used to create text labels 
l1 = tk.Label(master, text ='Enter Name Of Network:- ') 
l1.pack() 
  
# This will create an entry widget 
# Entry widgets are used to input data 
entry = tk.Entry(master) 
entry.pack() 
  
# This will create a button widget 
# Button widgets are used to trigger a function on a click event 
b1 = tk.Button(master, text ='Check Password', command = check_password) 
b1.pack()
master.mainloop()
