run_cmds = '''
python start_servers.py

python gui.py \
--directory_service_addr=http://127.0.0.1:5008 \
--locking_service_addr=http://127.0.0.1:5004 \
--security_service_addr=http://127.0.0.1:5005 \
--transaction_service_addr=http://127.0.0.1:5007 \
--user_id=1 \
--password=test1
'''

from distributed_file_system.client import Client
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--directory_service_addr', type=str, required=True)
parser.add_argument('--locking_service_addr', type=str, required=True)
parser.add_argument('--security_service_addr', type=str, required=True)
parser.add_argument('--transaction_service_addr', type=str, required=True)
parser.add_argument('--user_id', type=int, required=True)
parser.add_argument('--password', type=str, required=True)
args = parser.parse_args()

directory_service_addr = args.directory_service_addr
locking_service_addr = args.locking_service_addr
security_service_addr = args.security_service_addr
transaction_service_addr = args.transaction_service_addr
user_id = args.user_id
password = args.password

client = Client(user_id, password, directory_service_addr, locking_service_addr, security_service_addr, transaction_service_addr)

import Tkinter
from Tkinter import *
from ScrolledText import *
import tkFileDialog
import tkMessageBox
import tkSimpleDialog

root = Tkinter.Tk(className=" Just another Text Editor")
textPad = ScrolledText(root, width=100, height=80)

global open_files
open_files = []
transaction = None

def clean_up():
    save_command()
    for fname in open_files:
        print "closing", fname
        client.close(fname)
    if transaction is not None:
        client.commit_transaction()

    root.destroy()

root.protocol('WM_DELETE_WINDOW', clean_up)

def open_command():
    file_name = tkSimpleDialog.askstring("Open File", "File name:", parent=root)
    if file_name:
        try:
            client.open(file_name,'w')
            open_files.append(file_name)
            contents = client.read(file_name)
            textPad.delete('1.0', END)
            textPad.insert('1.0', contents)

        except Exception, e:
            tkMessageBox.showwarning("Open file", e, parent=root)

def new_command():
    file_name = tkSimpleDialog.askstring("New File", "File name:", parent=root)
    if file_name:
        try:
            client.open(file_name,'w')
            open_files.append(file_name)
            textPad.delete('1.0', END)

        except Exception, e:
            tkMessageBox.showwarning("New file", e, parent=root)

def save_command():
    if len(open_files) != 0:
        data = textPad.get('1.0', END+'-1c')
        client.write(open_files[-1], data)
        
def exit_command():
    if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
        clean_up()

def start_transaction():
    try:
        client.start_transaction()
        transaction = True
        tkMessageBox.showwarning("Start transaction", "Transaction started", parent=root)
    except Exception, e:
        tkMessageBox.showwarning("Start transaction", e, parent=root)

def commit_transaction():
    try:
        save_command()
        for fname in open_files:
            print "closing", fname
            client.close(fname)
        global open_files
        open_files = []

        client.commit_transaction()
        transaction = None
        tkMessageBox.showwarning("Commit transaction", "Transaction committed", parent=root)
    except Exception, e:
        tkMessageBox.showwarning("Commit transaction", e, parent=root)

def cancel_transaction():
    try:
        save_command()
        for fname in open_files:
            print "closing", fname
            client.close(fname)
        global open_files
        open_files = []

        client.cancel_transaction()
        transaction = None
        tkMessageBox.showwarning("Cancel transaction", "Transaction cancelled", parent=root)
    except Exception, e:
        tkMessageBox.showwarning("Cancel transaction", e, parent=root)

menu = Menu(root)
root.config(menu=menu)
filemenu = Menu(menu)
menu.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="New", command=new_command)
filemenu.add_command(label="Open...", command=open_command)
filemenu.add_command(label="Save", command=save_command)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=exit_command)

transactions_menu = Menu(menu)
menu.add_cascade(label="Transactions", menu=transactions_menu)
transactions_menu.add_command(label="Start Transaction", command=start_transaction)
transactions_menu.add_command(label="Commit Transaction", command=commit_transaction)
transactions_menu.add_command(label="Cancel Transaction", command=cancel_transaction)

textPad.pack()
root.mainloop()

