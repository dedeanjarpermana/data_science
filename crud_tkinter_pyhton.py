
import sqlite3
from tkinter import *
from tkinter import ttk


window = Tk()
window.title("Dumbldedore School")
window.geometry("1080x720")
storeName = "list student"
my_tree = ttk.Treeview(window)


def reverse(tuples):
    new_tup = tuples[::-1]
    return new_tup


def insert( id, name, surname):
    conn = sqlite3.connect("sekolah.db")
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS 
    list_siswa(itemId TEXT, itemName TEXT, itemSurname TEXT)""" )

    cursor.execute("INSERT INTO list_siswa VALUES (' " + str(id) + " ',  ' " + str(name) + " ' ,   ' " + str(surname) + " ')")
    conn.commit()


def delete(data):
    conn = sqlite3.connect("sekolah.db")
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS 
        list_siswa(itemId TEXT, itemName TEXT, itemSurname TEXT)""")

    cursor.execute("DELETE FROM list_siswa WHERE itemId = ' " + str(data) + " ' ")
    conn.commit()


def update(id, name, surname,  idName):
    conn = sqlite3.connect("sekolah.db")
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS 
        list_siswa(itemId TEXT, itemName TEXT, itemSurname TEXT)""")

    cursor.execute("UPDATE list_siswa SET itemId = ' " + str(id) + " ',   itemName = ' " + str(name) + " ',  itemSurname = ' " + str(surname) +  " ' WHERE itemId= ' "+str(idName)+" ' ")
    conn.commit()


def read():
    conn = sqlite3.connect("sekolah.db")
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS 
        list_siswa(itemId TEXT, itemName TEXT, itemSurname TEXT)""")

    cursor.execute("SELECT * FROM list_siswa")
    results = cursor.fetchall()
    conn.commit()
    return results


def insert_data():
    itemId = str(entryId.get())
    itemName = str(entryName.get())
    itemSurname = str(entrySurname.get())
   
    if itemId == "" or itemName == " ":
        print("Error Inserting Id")
    if itemName == "" or itemName == " ":
        print("Error Inserting Name")
    if itemSurname == "" or itemSurname == " ":
        print("Error Inserting Surname")
    
    else:
        insert(str(itemId), str(itemName), str(itemSurname))

    for data in my_tree.get_children():
        my_tree.delete(data)

    for result in reverse(read()):
        my_tree.insert(parent='', index='end', iid=result, text="", values=(result), tag="orow")

    my_tree.tag_configure('orow', background='#EEEEEE')
    my_tree.grid(row=1, column=5, columnspan=4, rowspan=5, padx=10, pady=10)


def delete_data():
    selected_item = my_tree.selection()[0]
    deleteData = str(my_tree.item(selected_item)['values'][0])
    delete(deleteData)

    for data in my_tree.get_children():
        my_tree.delete(data)

    for result in reverse(read()):
        my_tree.insert(parent='', index='end', iid=result, text="", values=(result), tag="orow")

    my_tree.tag_configure('orow', background='#EEEEEE')
    my_tree.grid(row=1, column=5, columnspan=4, rowspan=5, padx=10, pady=10)

def update_data():
    selected_item = my_tree.selection()[0]
    update_name = my_tree.item(selected_item)['values'][0]
    update(entryId.get(), entryName.get(), entrySurname.get(), update_name)

    for data in my_tree.get_children():
        my_tree.delete(data)

    for result in reverse(read()):
        my_tree.insert(parent='', index='end', iid=result, text="", values=(result), tag="orow")

    my_tree.tag_configure('orow', background='#EEEEEE')
    my_tree.grid(row=1, column=5, columnspan=4, rowspan=5, padx=10, pady=10)




titleLabel = Label(window, text=storeName, font=('Arial bold', 30), bd=2)
titleLabel.grid(row=0, column=0, columnspan=8, padx=20, pady=20)

idLabel = Label(window, text="ID", font=('Arial bold', 15))
nameLabel = Label(window, text="Name", font=('Arial bold', 15))
surnameLabel = Label(window, text="Surname", font=('Arial bold', 15))
idLabel.grid(row=1, column=0, padx=10, pady=10)
nameLabel.grid(row=2, column=0, padx=10, pady=10)
surnameLabel.grid(row=3, column=0, padx=10, pady=10)

entryId = Entry(window, width=25, bd=5, font=('Arial bold', 15))
entryName = Entry(window, width=25, bd=5, font=('Arial bold', 15))
entrySurname = Entry(window, width=25, bd=5, font=('Arial bold', 15))

entryId.grid(row=1, column=1, columnspan=3, padx=5, pady=5)
entryName.grid(row=2, column=1, columnspan=3, padx=5, pady=5)
entrySurname.grid(row=3, column=1, columnspan=3, padx=5, pady=5)

buttonEnter = Button(
    window, text="Add", padx=5, pady=5, width=5,
    bd=3, font=('Arial', 15), bg="#0099ff", command=insert_data)
buttonEnter.grid(row=5, column=1, columnspan=1)

buttonUpdate = Button(
    window, text="Update", padx=5, pady=5, width=5,
    bd=3, font=('Arial', 15), bg="#ffff00", command=update_data)
buttonUpdate.grid(row=5, column=2, columnspan=1)
  
buttonDelete = Button(
    window, text="Delete", padx=5, pady=5, width=5,
    bd=3, font=('Arial', 15), bg="#e62e00", command=delete_data)
buttonDelete.grid(row=5, column=3, columnspan=1)



my_tree['columns'] = ("ID", "Name", "Surname")
my_tree.column("#0", width=0, stretch=NO)
my_tree.column("ID", anchor=W, width=100)
my_tree.column("Name", anchor=W, width=200)
my_tree.column("Surname", anchor=W, width=150)
my_tree.heading("ID", text="ID", anchor=W)
my_tree.heading("Name", text="Name", anchor=W)
my_tree.heading("Surname", text="Surname", anchor=W)


my_tree.tag_configure('orow', background='#EEEEEE', font=('Arial bold', 15))
my_tree.grid(row=1, column=5, columnspan=4, rowspan=5, padx=10, pady=10)


window.mainloop()

