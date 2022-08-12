#!/usr/bin/env python3

import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
import re
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords
import os
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import PyPDF2
import csv

def getPDFFileContentToTXT(pdfFile):
    myPDFFile = PyPDF2.PdfFileReader(pdfFile)
    
    with open('pdfContenido.txt', 'w') as pdf_output:
        for page in range (myPDFFile.getNumPages()):
            data = myPDFFile.getPage(page).extractText()
            pdf_output.write(data)
    with open('pdfContenido.txt', 'r') as myPDFContent:
        return myPDFContent.read().replace('\n',' ')

def vacanteCSV_str(file,vacante): #requiere el arcvhivo csv de las vacantes y la vacante que se analizara
    df = pd.read_csv(file)
    df = df.fillna(" ") #rellenamos las casillas sin nada con un espacio
    requerimientos = ""
    
    for i in df[vacante]:
        requerimientos = requerimientos +i + " "
    
    return requerimientos

def tokenize1_2_3_4(pdfFileContent,requerimientos):
    
    count = 1
    for letter in range(len(pdfFileContent)): #funcion para limpiar y corregir errores de transformacion a txt
    
        count +=1
        if count == len(pdfFileContent):
            break
    
        l1 = pdfFileContent[letter]
        l2 = pdfFileContent[letter + 1]
        l3 = pdfFileContent[letter + 2]
    
        if l1.islower() == True and l2.isupper() == True and l3.islower() == True: #Errores de \n
            pdfFileContent = pdfFileContent.replace(l1+l2+l3,l1+" "+l2+l3)
        
        if l1.isdigit() == True and l2.isupper() == True and l3.islower() == True: #Numeros pegados a letras mayusculas 
            pdfFileContent = pdfFileContent.replace(l1+l2+l3,l1+" "+l2+l3)
        
    Tokens_1 = word_tokenize(pdfFileContent) 
    Tokens_vacantes_1 = word_tokenize(requerimientos)
    
    punctuation = re.compile(r'[-+/.?!,:;()•@[0-9]') #lista de caracteres que removeremos

    Tokens_2 = []
    for words in Tokens_1:
        word = punctuation.sub("",words)
        if len(word)>0:
            Tokens_2.append(word)
        
    Tokens_vacantes_2 = []
    for words in Tokens_vacantes_1:
        word = punctuation.sub("",words)
        if len(word)>0:
            Tokens_vacantes_2.append(word)
            
    stopw = stopwords.words("spanish") #Removemos las palabras de relleno que no aportan informacion
    Tokens_3 = [word for word in Tokens_2 if word not in stopw] 
    Tokens_vacantes_3 = [word for word in Tokens_vacantes_2 if word not in stopw] 
    
    sbst = SnowballStemmer('spanish')

    Tokens_4 = []
    for words in Tokens_3:
        word = sbst.stem(words)
        Tokens_4.append(word)

    dic_revertir = {}
    Tokens_vacantes_4 = []
    for words in Tokens_vacantes_3:
        word = sbst.stem(words)
        Tokens_vacantes_4.append(word)
        dic_revertir[word] = words
        
    sentence_1 = " ".join(Tokens_4)
    sentence_2 = " ".join(Tokens_vacantes_4)
    
    CountVec = CountVectorizer(ngram_range=(1,1)) # to use bigrams ngram_range=(2,2)
    Count_data = CountVec.fit_transform([sentence_1,sentence_2])
    cv_dataframe = pd.DataFrame(Count_data.toarray(),columns = CountVec.get_feature_names_out())
    
    count = 0
    count2 = 0
    matches = []

    for i,j in zip(cv_dataframe.iloc[0],cv_dataframe.iloc[1]):
        if i >= 1 and j >=1:
            count += 1
            matches.append(cv_dataframe.columns.values[count2])
        count2 += 1
        
    final_score = (count / len(Tokens_vacantes_4))*100
    
    final_matches = []
    for i in matches: #lo que se encontro dentro del curriculum
        final_matches.append(dic_revertir[i])
    
    return round(final_score),final_matches

############################################################################## gui tkinter 

from tkinter import *
from tkinter import ttk
from tkinter import filedialog

def clicked1():

    folder_selected = filedialog.askdirectory(title = "Seleccionar directorio con CV´s")
    archivos = os.listdir(folder_selected)

    global pdfs 
    global dict_final
    pdfs = []
    dict_final ={}

    for i in archivos: #abre todos los archivos con extension pdf y los guerda en pdfs
        arch = folder_selected + "/" + i 
        if arch[-4:] == ".pdf":
            pdfs.append(arch)
            dict_final[i] = ""

    label1.configure(text = "Archivos pdf seleccionados: " + str(len(pdfs)))

def clicked2():
    global file2
    global diff_vacantes
    file2 = filedialog.askopenfilename(title = "Seleccionar archivo Vacantes", filetypes=[("archivos csv","*.csv")])
    label2.configure(text = os.path.basename(file2))
    diff_vacantes = pd.read_csv(file2) #conseguimos los nombres de las columnas del cv para poder ponerlos en el combobox
    diff_vacantes = diff_vacantes.columns.tolist() 

    #combo
    combo.configure(value = diff_vacantes)
    


def clicked3():
    requerimientos = vacanteCSV_str(file2, str(combo_var.get()))

    count = 0
    llaves = list(dict_final.keys())

    for file in pdfs:
        pdfFileContent = getPDFFileContentToTXT(file)
        os.remove("pdfContenido.txt")
        i_score ,j_palabras = tokenize1_2_3_4(pdfFileContent,requerimientos)
        dict_final[llaves[count]] = [i_score,j_palabras] #guardamos la calificacion y las palabras en el diccionario final 
        count += 1

    
    dict_final2 = dict(sorted(dict_final.items(), key=lambda item: item[1], reverse=True)) #ordenas el diccionario 
    llaves = list(dict_final2.keys()) #volvemos a conseguir las llaves del diccionari pero ya ordenado 

    #creamos un csv en donde se almacena toda la informacion 
    salida = open("Resultados.csv", mode = "w", newline = "", encoding = "utf-8")
    csv_writer = csv.writer(salida, delimiter = ",")
    for i in llaves:
        csv_writer.writerow([i, " Puntuacion: ", str(dict_final[i][0]) + "%", "Requisitos encontrados: "] + dict_final[i][1])
    salida.close()

    label3.configure(text = "Archivo Resultados.csv Generado")
    label4.configure(text = os.getcwd())

azul_claro  = "#16aff5"
azul_oscuro =  "#0e78a8"
blanco =  "#feffff"

window = Tk()
window.title("Sautek Procesamiento de lenguajes naturales")
window.geometry("825x275")
window.configure(bg = azul_oscuro)
anchura_bottones = 9
font_labels = ("Futura", 18)
font_buttons = ("Futura", 14)

#button

bt1 = ttk.Button(window, text="CV´s", command = clicked1, width = anchura_bottones)
bt1.place(relx = 0.1, rely = 0.1, anchor = "w")

bt2 = ttk.Button(window, text="Vacantes", command = clicked2, width = anchura_bottones)
bt2.place(relx = 0.1, rely = 0.3, anchor = "w")

bt3 = ttk.Button(window, text="Resultados", command = clicked3, width = anchura_bottones)
bt3.place(relx = 0.1, rely = 0.7, anchor = "w")

#label

label1 = Label(window, text = " ", font = font_labels, bg = azul_oscuro, fg = azul_claro)
label1.place(relx = 0.3, rely = 0.1, anchor = "w")

label2 = Label(window, text = " ", font = font_labels, bg = azul_oscuro, fg = azul_claro)
label2.place(relx = 0.3, rely = 0.3, anchor = "w")

label3 = Label(window, text = " ", font = font_labels, bg = azul_oscuro, fg= blanco)
label3.place(relx = 0.3, rely = 0.5, anchor = "w")

label4 = Label(window, text = " ", font = font_labels, bg = azul_oscuro, fg = blanco)
label4.place(relx = 0.3, rely = 0.7, anchor = "w")

style= ttk.Style()
style.theme_use('classic')
style.configure("TCombobox", fieldbackground= blanco, background= blanco, arrowcolor = azul_claro)
style.configure("Tbutton")

#combobox
combo_var = StringVar()
combo = ttk.Combobox(window, width = 11, textvariable = combo_var, style  = "TCombobox")
combo.place(relx = 0.1, rely = 0.5, anchor = "w")

window.mainloop()

# pyinstaller --onefile --windowed --icon=logo.icns SNLP.py
# /Users/andressaldana/Documents/GitHub/Sautek-Natural-language-programming/Codigo_Exe.py 


