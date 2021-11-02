
from jinja2 import Environment, FileSystemLoader
from flask import Flask, flash, url_for, render_template, request , redirect, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re, random, copy
from owlready2 import *
import rdflib
import numpy as np
import pandas as pd
from IPython.display import display, HTML

app = Flask (__name__)







app.secret_key = "12345"

 
app.config["MYSQL_HOST"] ='localhost'
app.config["MYSQL_USER"] ='root'
app.config["MYSQL_PASSWORD"] ='gadissuci25'
app.config["MYSQL_DB"] ='database_ITS'

mysql = MySQL(app)

graph = default_world.as_rdflib_graph()

nilai_siswa = 0
hasil = 0

onto = get_ontology("worked_exampel.owl").load()
PREFIX = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX dt: <http://www.semanticweb.org/thepermana/ontologies/2021/2/worked_Example_terbaru_2#>"""

graph1 = graph.get_context(onto)
pd.options.display.max_colwidth =1000


@app.route('/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = 'wrong username or password'
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'nis' in request.form and 'password' in request.form:
        # Create variables for easy access
        nis = request.form['nis']
        password = request.form['password']
         # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM login WHERE nis = %s AND password = %s', (nis, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['nis'] = account['nis']
            session['nama'] = account['nama']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg='')

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('nis', None)
   session.pop('nama', None)

   # Redirect to login page
   return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'nis' in request.form and 'nama' in request.form and 'password' in request.form:
        # Create variables for easy access
        nis = request.form['nis']
        nama = request.form['nama']
        password = request.form['password']
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM login WHERE nis = %s', (nis,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO login VALUES (NULL, %s, %s, %s)', (nis, nama, password,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            
            graph1 = graph.get_context(onto)
            
            graph1.update(PREFIX + """ INSERT { dt:"""+ nama + """ rdf:type dt:siswa.
                    dt:"""+ nama +""" dt:hasScore "0"^^xsd:float.}
                    WHERE {}""")
            onto.save("worked_exampel.owl", format="ntriples")
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:

        #CHANGE-1
        session['student_model_index'] = 0

        # User is loggedin show them the home page
        return render_template('home.html', nis=session['nis'], nama = session['nama'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    global hasil
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM login WHERE nis = %s', (session['nis'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account, hasil=hasil)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

soal_pretest = {
 #Format is 'question':[options]
 'Tentukan penyelesaian dari x+29 = 45':['x=29','x=74','x=16','x=45'],
 'Tentukan akar-akar dari x^2+ x-12 = 0':['x=4 and x= -3','x=-4 and x=3','x=4 and x = 3','x-4 and x = -3'],
 'Tentukan akar-akar dari 2x^2 +5x-3=0':['x=1/2 and x= -3','x=3 and x=-1/2','x=-3 and x = -1/2','=3 and x = -3'],
 'Tentukan jumlah akar-akar dari x^2 + 6x - 7 = 0':['6','-6','7','-7'],
 'Bagaimanakah sifat akar-akar persamaan berikut x^2 + 2x + 2 = 0':['real','unreal/imaginer','positive','negative'],
 
}

questions = copy.deepcopy(soal_pretest)

def shuffle(q):
 """
 This function is for shuffling 
 the dictionary elements.
 """
 selected_keys = []
 i = 0
 while i < len(q):
  current_selection = random.choice(list(q.keys()))
  if current_selection not in selected_keys:
   selected_keys.append(current_selection)
   i = i+1
 return selected_keys

""" 
@app.route('/pretest')
def pretest():
    if 'loggedin' in session:
        questions_shuffled = shuffle(questions)
    for i in questions.keys():
        random.shuffle(questions[i])
    return render_template('main.html', q = questions_shuffled, o = questions, index = i )
"""
@app.route('/pretest')
def pretest():
    
    return render_template('quiz2.html' )


@app.route('/quiz_pretest', methods=['POST', 'GET'])
def quiz_pretest():
    jmlh_soal = 15
    global hasil
    for i in [jmlh_soal] : 
        score = 0
        if request.form['question1'] == "a":
            score = score + 1
            hasil = "benar" + " " + str(score)
            
        if request.form['question2'] == "c":
            score = score + 1
            hasil = "benar" + " " + str(score)
        
        if request.form['question3'] == "d":
            score = score + 1
            hasil = "benar" + " " + str(score)
            
        if request.form['question4'] == "b":
            score = score + 1
            hasil = "benar" + " " + str(score)
        
        if request.form['question5'] == "b":
            score = score + 1
            hasil = "benar" + " " + str(score)
        if request.form['question6'] == "d":
            score = score + 1
            hasil = "benar" + " " + str(score)
            
        if request.form['question7'] == "d":
            score = score + 1
            hasil = "benar" + " " + str(score)
        
        if request.form['question8'] == "c":
            score = score + 1
            hasil = "benar" + " " + str(score)
            
        if request.form['question9'] == "c":
            score = score + 1
            hasil = "benar" + " " + str(score)
        
        if request.form['question10'] == "a":
            score = score + 1
            hasil = "benar" + " " + str(score)
        if request.form['question11'] == "c":
            score = score + 1
            hasil = "benar" + " " + str(score)
            
        if request.form['question12'] == "a":
            score = score + 1
            hasil = "benar" + " " + str(score)
        
        if request.form['question13'] == "d":
            score = score + 1
            hasil = "benar" + " " + str(score)
            
        if request.form['question14'] == "b":
            score = score + 1
            hasil = "benar" + " " + str(score)
        
        if request.form['question15'] == "b":
            score = score + 1
            hasil = "benar" + " " + str(score)
        else:
            score = score
            hasil = "benar  : " + " " + str(score)
        return render_template('hasilpretest.html', hasil = hasil)

    

@app.route('/excercise')
def excercise():
    if 'loggedin' in session:
        global nilai_siswa
        nilai_siswa = float(nilai_siswa)
        jumlah_soal = 6
        i = 1
        
        while i <= jumlah_soal :
            
            
            # User is loggedin show them the home page
            #menampilkan soal 1
            query_soal1= graph1.query(PREFIX + """ 
            SELECT DISTINCT ?q1 ?soal1
                WHERE { ?q1 dt:hasSoal ?soal1. FILTER(?q1=dt:q1)}
            """)
            for q1 in query_soal1:
                    soal1 = ( q1.soal1)


            #menentukan soal kedua kompetensi 1
            query_soal2= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?q2 ?soal2
                    WHERE { ?q2 dt:hasSoal ?soal2. FILTER(?q2=dt:q2)}
            """)
            for q2 in query_soal2:
                    soal2 = ( q2.soal2)

            #menentukan soal kompetensi 2
            query_soal5= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?q5 ?soal5
                    WHERE { ?q5 dt:hasSoal ?soal5. FILTER(?q5=dt:q5)}
            """)
            for q5 in query_soal5:
                soal5 = q5.soal5


            #menentukan soal kompetensi 2
            query_soal6= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?q6 ?soal6
                    WHERE { ?q6 dt:hasSoal ?soal6. FILTER(?q6=dt:q6)}
            """)
            for q6 in query_soal6:
                soal6 = q6.soal6

            #menentukan soal kompetensi 3
            query_soal10= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?q10 ?soal10
                    WHERE { ?q10 dt:hasSoal ?soal10. FILTER(?q10=dt:q10)}
            """)
            for q10 in query_soal10:
                soal10 = q10.soal10

            #menentukan soal kompetensi 3
            query_soal11= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?q11 ?soal11
                    WHERE { ?q11 dt:hasSoal ?soal11. FILTER(?q11=dt:q11)}
            """)
            for q11 in query_soal11:
                soal11 = q11.soal11
            # ------------------------------------------------


            i += 1
            return render_template('excercise.html', nilai_siswa = nilai_siswa, soal1=soal1, soal2=soal2, soal5=soal5, soal6=soal6, soal10=soal10, soal11=soal11, iterator_soal = session['student_model_index'])
        
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
    



@app.route('/student_model', methods=['POST', 'GET'])
def student_model():
    session['state']=False
    if 'loggedin' in session:
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM login WHERE nis = %s', (session['nis'],))
        account = cursor.fetchone()
        nama = account['nama']
        # User is loggedin show them the home page
        global nilai_siswa
        logit = 0
        betha= [0.25,0.25,0.36, 0.36, 0.39, 0.39]
        gamma= [0.71, 0.71, 0.74,0.74,  0.48, 0.48]
        rho= [0.29, 0.29, 0.26, 0.26, 0.53, 0.53]
    
        query_nilai_lama = graph1.query(PREFIX + """ 
                        SELECT DISTINCT ?q0 ?soal0
                            WHERE { ?q0 dt:hasScore ?soal0. FILTER(?q0=dt:"""+nama+""")} """)
        
        #nilai_lama = 0
        for n in query_nilai_lama: 
            nilai_lama = str(n.soal0)
            
        jumlah_soal = 6
        
        
        jawaban =["-7", "-5/2","real berbeda", "-2 atau 2", "-3/2 atau 2", "9"]
        
        #CHANGE-2
        i = session['student_model_index']
        print(i)
        
        while i < jumlah_soal: 
            print(i)
            print(jawaban[i])
            score = 0
            sum_sigma_gamma_rho = 0

            
            if request.form['jawaban'] == jawaban[i]:
                session['state']=True
                
                #sum_sigma_gamma_rho = 0
                j = 0
                print(j)

                #CHANGE-3
                while j <= i :
                    sigma_gamma_rho = (gamma[j] * 1) + (rho[j] * 0)
                    sum_sigma_gamma_rho += sigma_gamma_rho
                    j += 1
                    s_model = betha[i] + sum_sigma_gamma_rho
                #print("PFA_student_model")
                #print(round(s_model,2))
                logit = 1/(1+np.exp(-s_model))
                #print("LOGIT_student_model")      
                #print(round(logit,2))
                total_seratus = logit * 100
                nilai_siswa = round(total_seratus,2)
                

                nilai_siswa = str(nilai_siswa)
                graph1.update(PREFIX+""" 
                            DELETE {
                                    dt:"""+nama+""" dt:hasScore \""""+nilai_lama+"""\"^^xsd:float.
                                    }
                            INSERT { 
                                    dt:"""+nama+""" dt:hasScore \""""+nilai_siswa+"""\"^^xsd:float. 
                                    } 
                            WHERE {
                                    dt:"""+nama+""" rdf:type dt:siswa.
                                    } """)  
                onto.save("worked_exampel.owl", format="ntriples")
                flash('benar!')
                
                i+=1

                #CHANGE-4
                session['student_model_index'] = i
                
                return render_template('student_model_benar.html', nilai_siswa = nilai_siswa,  nama = session['nama'])
                
            else:
                
                #CHANGE-5
                j=0

                sum_sigma_gamma_rho = sum_sigma_gamma_rho
                logit = logit
                while j <= i:
                    sigma_gamma_rho = (gamma[j] * 0) + (rho[j] * 1)
                    sum_sigma_gamma_rho += sigma_gamma_rho
                    j += 1
                    s_model = betha[i] + sum_sigma_gamma_rho
                #print("PFA_student_model")
                #print(round(s_model,2))
                logit = 1/(1+np.exp(-s_model))
                #print("LOGIT_student_model")  
                #print(round(logit,2))
                total_seratus = logit * 100
                nilai_siswa = round(total_seratus,2)
                
                
                nilai_siswa = str(nilai_siswa)
                graph1.update(PREFIX+""" 
                            DELETE {
                                    dt:"""+nama+""" dt:hasScore \""""+nilai_lama+"""\"^^xsd:float.
                                    }
                            INSERT { 
                                    dt:"""+nama+""" dt:hasScore \""""+nilai_siswa+"""\"^^xsd:float. 
                                    } 
                            WHERE {
                                    dt:"""+nama+""" rdf:type dt:siswa.
                                    } """)  
                onto.save("worked_exampel.owl", format="ntriples")
                flash('salah!')
                session['state']=False

                
                #CHANGE-6
                session['student_model_index'] = i

                return render_template('student_model_salah.html', nilai_siswa = nilai_siswa,  nama = session['nama'])
            return render_template('student_model_benar.html', nilai_siswa = nilai_siswa,  nama = session['nama'])

        #return render_template('home.html', nis=session['nis'], nama = session['nama'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))





@app.route('/next_soal', methods=['POST', 'GET'])
def next_soal():
    if 'loggedin' in session:
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM login WHERE nis = %s', (session['nis'],))
        account = cursor.fetchone()
        nama = account['nama']
        # User is loggedin show them the home page
        global nilai_siswa
        nilai_siswa = float(nilai_siswa)
        return redirect(url_for('excercise'))

@app.route('/get_hint', methods=['POST', 'GET'])
def get_hint():
    global nilai_siswa
    nilai_siswa = float(nilai_siswa)
    
    #soal 1 hint 1
    query_soal1_hint1= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint1
                        WHERE { ?hint dt:hasHint1 ?hint1. FILTER(?hint=dt:q1)}
                    """)
    for s1h1 in query_soal1_hint1 :
        soal1hint1 = s1h1.hint1
    # soal 1 hint2
    query_soal1_hint2= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint2
                        WHERE { ?hint dt:hasHint2 ?hint2. FILTER(?hint=dt:q1)}
                    """)
    for s1h2 in query_soal1_hint2 :
        soal1hint2 = s1h2.hint2
        
                
    #soal 1 hint 3
    query_soal1_hint3= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint3
                        WHERE { ?hint dt:hasHint3 ?hint3. FILTER(?hint=dt:q1)}
                    """)
    for s1h3 in query_soal1_hint3 :
        soal1hint3 = s1h3.hint3
        
    #soal 2 hint 1
    query_soal2_hint1= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint1
                        WHERE { ?hint dt:hasHint1 ?hint1. FILTER(?hint=dt:q2)}
                    """)
    for s2h1 in query_soal2_hint1 :
        soal2hint1 = s2h1.hint1
        
    # soal 2 hint2
    query_soal2_hint2= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint2
                        WHERE { ?hint dt:hasHint2 ?hint2. FILTER(?hint=dt:q2)}
                    """)
    for s2h2 in query_soal2_hint2 :
        soal2hint2 = s2h2.hint2
        
                
    #soal 2 hint 3
    query_soal2_hint3= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint3
                        WHERE { ?hint dt:hasHint3 ?hint3. FILTER(?hint=dt:q2)}
                    """)
    for s2h3 in query_soal2_hint3 :
        soal2hint3 = s2h3.hint3
    
    #soal 3 hint 1
    query_soal3_hint1= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint1
                        WHERE { ?hint dt:hasHint1 ?hint1. FILTER(?hint=dt:q5)}
                    """)
    for s3h1 in query_soal3_hint1 :
        soal3hint1 = s3h1.hint1
    # soal 3 hint2
    query_soal3_hint2= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint2
                        WHERE { ?hint dt:hasHint2 ?hint2. FILTER(?hint=dt:q5)}
                    """)
    for s3h2 in query_soal3_hint2 :
        soal3hint2 = s3h2.hint2
        
                
    #soal 3 hint 3
    query_soal3_hint3= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint3
                        WHERE { ?hint dt:hasHint3 ?hint3. FILTER(?hint=dt:q5)}
                    """)
    for s3h3 in query_soal3_hint3 :
        soal3hint3 = s3h3.hint3
        
    #soal 4 hint 1
    query_soal4_hint1= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint1
                        WHERE { ?hint dt:hasHint1 ?hint1. FILTER(?hint=dt:q6)}
                    """)
    for s4h1 in query_soal4_hint1 :
        soal4hint1 = s4h1.hint1
    # soal 4 hint2
    query_soal4_hint2= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint2
                        WHERE { ?hint dt:hasHint2 ?hint2. FILTER(?hint=dt:q6)}
                    """)
    for s4h2 in query_soal4_hint2 :
        soal4hint2 = s4h2.hint2
        
                
    #soal 4 hint 3
    query_soal4_hint3= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint3
                        WHERE { ?hint dt:hasHint3 ?hint3. FILTER(?hint=dt:q6)}
                    """)
    for s4h3 in query_soal4_hint3 :
        soal4hint3 = s4h3.hint3
        
        
    #soal 5 hint 1
    query_soal5_hint1= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint1
                        WHERE { ?hint dt:hasHint1 ?hint1. FILTER(?hint=dt:q10)}
                    """)
    for s5h1 in query_soal5_hint1 :
        soal5hint1 = s5h1.hint1
    # soal 5 hint2
    query_soal5_hint2= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint2
                        WHERE { ?hint dt:hasHint2 ?hint2. FILTER(?hint=dt:q10)}
                    """)
    for s5h2 in query_soal5_hint2 :
        soal5hint2 = s5h2.hint2
        
                
    #soal 5 hint 3
    query_soal5_hint3= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint3
                        WHERE { ?hint dt:hasHint3 ?hint3. FILTER(?hint=dt:q10)}
                    """)
    for s5h3 in query_soal5_hint3 :
        soal5hint3 = s5h3.hint3
    
    #soal 6 hint 1
    query_soal6_hint1= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint1
                        WHERE { ?hint dt:hasHint1 ?hint1. FILTER(?hint=dt:q11)}
                    """)
    for s6h1 in query_soal6_hint1 :
        soal6hint1 = s6h1.hint1
    
    # soal 6 hint2
    query_soal6_hint2= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint2
                        WHERE { ?hint dt:hasHint2 ?hint2. FILTER(?hint=dt:q11)}
                    """)
    for s6h2 in query_soal6_hint2 :
        soal6hint2 = s6h2.hint2
        
                
    #soal 6 hint 3
    query_soal6_hint3= graph1.query(PREFIX + """ 
                SELECT DISTINCT ?hint ?hint3
                        WHERE { ?hint dt:hasHint3 ?hint3. FILTER(?hint=dt:q11)}
                    """)
    for s6h3 in query_soal6_hint3 :
        soal6hint3 = s6h3.hint3
        
    return render_template('get_hint.html', iterator_soal = session['student_model_index'], soal1hint1= soal1hint1, soal1hint2=soal1hint2, soal1hint3 = soal1hint3, query_soal1_hint3=query_soal1_hint3, nilai_siswa=nilai_siswa, soal2hint1= soal2hint1, soal2hint2=soal2hint2, soal2hint3 = soal2hint3, soal3hint1= soal3hint1, soal3hint2=soal3hint2, soal3hint3 = soal3hint3, soal4hint1= soal4hint1, soal4hint2=soal4hint2, soal4hint3 = soal4hint3, soal5hint1= soal5hint1, soal5hint2=soal5hint2, soal5hint3 = soal5hint3, soal6hint1= soal6hint1, soal6hint2=soal6hint2, soal6hint3 = soal6hint3)   
    
@app.route('/frameset')
def frameset():
    return render_template('frameset2.html')

def pretty_print(top_theree_Hasil_sorting_kompetensi1):
    return display(HTML(top_theree_Hasil_sorting_kompetensi1.to_html().replace("\\n","<br>")))

@app.route('/recommender_worked_example', methods=['POST', 'GET'])
def recommender_worked_example():
    
    global nilai_siswa
    nilai_siswa = float(nilai_siswa)
    
    graph1 = graph.get_context(onto)
    # menampilkan soal worked example kompetensi 1
    query14= graph1.query(PREFIX + """ 

        SELECT ?SoalWorkedExample
            WHERE { ?item dt:hasSoalWE ?SoalWorkedExample.
            ?item dt:hasKompetensi ?kompetensi.

            FILTER(?kompetensi=dt:kompetensi1) } """)
    for q14 in query14:
        soal_worked_example1 = q14.SoalWorkedExample
        
    
    # menampilkan soal kompetensi 1
    query101= graph1.query(PREFIX + """ 

        SELECT ?soal
            WHERE { ?item dt:hasSoal ?soal.
            ?item dt:hasKompetensi ?kompetensi.

            FILTER(?kompetensi=dt:kompetensi1) } """)

    for q101 in query101:
        soal_kompetensi_1 = q101.soal

    df1 = pd.DataFrame(query14, columns = ['soalworkedexample'])
    df2 = pd.DataFrame(query101, columns = ['soal'])
    # menampilkan bobot soal hanya dengan kompetensi 1
    query60= graph1.query( """ 

                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX dt: <http://www.semanticweb.org/thepermana/ontologies/2021/2/worked_Example_terbaru_2#>

                SELECT  ?weight
                    WHERE { ?x dt:hasWeight ?weight.
                           ?x dt:hasKompetensi ?kompetensi. FILTER(?kompetensi=dt:kompetensi1) }
    """ )

    for q60 in query60:
        bobot_soal_kompetensi_1 = q60.weight
    
    # menampilkan bobot worked example dengan hanya dengan kompetensi 1
    query65= graph1.query( """ 

                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX dt: <http://www.semanticweb.org/thepermana/ontologies/2021/2/worked_Example_terbaru_2#>

                SELECT  ?weight
                    WHERE { ?x dt:hasWeightQuestion ?weight.
                           ?x dt:hasKompetensi ?kompetensi. FILTER(?kompetensi=dt:kompetensi1) }
    """ )

    for q65 in query65:
        bobot_we_kompetensi_1 = q65.weight
        
    # membuat data frame untuk kompetensi 1
    df30 = pd.DataFrame(query60, columns = ['bobot_we']) 
    df31 = pd.DataFrame(query65, columns = ['bobot_que']) 
    df32 = pd.DataFrame(query101, columns = ['soal']) 
    df33 = pd.DataFrame(query14, columns = ['soalworkedexample'])
    frames31 = [df30, df31,df32, df33] 

    df4 = pd.concat(frames31, axis=1, join="inner")
    #print("data")
    #print(type(df4))
    #df4

    # buat matrixnya untuk soal dan worked example yang related terhadap kompetensi 1
    df_result4 = pd.DataFrame(np.zeros((len(df4.bobot_we), len(df4.bobot_que))))

    list_result = []

    for i in range(len(df4.bobot_we)):
        tmp_mltp4 = []
        for j in range(len(df4.bobot_que)):
            multiplied4 = (float(df4.bobot_we[i]) * float(df4.bobot_que[j])) / (float(df4.bobot_we[i]) + float(df4.bobot_que[j]))
    #         print(multiplied4)
            result = {
                "jaccard": multiplied4,
                "contoh pengerjaan:": df4.soalworkedexample[j]
            }
    #         print(result)
            list_result.append(result)

    #print(list_result)
    #         tmp_mltp4.append(multiplied4)
    #     df_result4[i] = tmp_mltp4

    # print("Hasil Perkalian jaccard formula : ")
    # print(df_result4)

    df_result_final = pd.DataFrame(list_result)
    

    #display(df_result_final)
    Hasil_sorting_kompetensi1=df_result_final.sort_values(by=['jaccard'], ascending=False)
    Hasil_sorting_kompetensi1_drop = Hasil_sorting_kompetensi1.drop(['jaccard'], axis=1)
    
    #menampilkan 2 teratas 
    top_theree_Hasil_sorting_kompetensi1= Hasil_sorting_kompetensi1_drop[:2]
    
    # fungsi di bawah ini berhasil mengjilangkan \n
    top_theree_Hasil_sorting_kompetensi1 = top_theree_Hasil_sorting_kompetensi1.replace('\n',' ', regex=True)
    number1 = top_theree_Hasil_sorting_kompetensi1.iloc[0] 
    number2 = top_theree_Hasil_sorting_kompetensi1.iloc[1]
    number1_1 = number1.to_string(header=False)
    number1_2 = number2.to_string(header=False)
    top_3_we_kompetensi_1 = top_theree_Hasil_sorting_kompetensi1.to_string(header=False)
    
   
    #fungsi yang berhasil memebuat data text di dataframe berbaris-baris,
    #pretty_print(top_theree_Hasil_sorting_kompetensi1)
    
   
    
    # ==================================== kompetensi 2 =============================== #
    graph1 = graph.get_context(onto)
    # menampilkan soal worked example kompetensi 2
    query15= graph1.query(PREFIX + """ 

        SELECT ?SoalWorkedExample
            WHERE { ?item dt:hasSoalWE ?SoalWorkedExample.
            ?item dt:hasKompetensi ?kompetensi.

            FILTER(?kompetensi=dt:kompetensi2) } """)

    for q15 in query15:
        soal_we_kompetensi_2 = q15.SoalWorkedExample
        
    graph1 = graph.get_context(onto)
    # menampilkan soal  kompetensi 2
    query102= graph1.query(PREFIX + """ 

        SELECT ?soal
            WHERE { ?item dt:hasSoal ?soal.
            ?item dt:hasKompetensi ?kompetensi.

            FILTER(?kompetensi=dt:kompetensi2) } """)

    for q102 in query102:
        soal_kompetensi_2 = q102.soal
        
    df11 = pd.DataFrame(query15, columns = ['soalworkedexample']) 
    df12 = pd.DataFrame(query102, columns = ['soal'])
    
    # menampilkan bobot soal hanya dengan kompetensi 2
    query61= graph1.query( """ 

                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX dt: <http://www.semanticweb.org/thepermana/ontologies/2021/2/worked_Example_terbaru_2#>

                SELECT  ?weight
                    WHERE { ?x dt:hasWeight ?weight.
                           ?x dt:hasKompetensi ?kompetensi. FILTER(?kompetensi=dt:kompetensi2) }
    """ )

    for q61 in query61:
        bobot_soal_kompetensi_2 = q61.weight
    
    # menampilkan bobot worked example dengan hanya dengan kompetensi 1
    query66= graph1.query( """ 

                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX dt: <http://www.semanticweb.org/thepermana/ontologies/2021/2/worked_Example_terbaru_2#>

                SELECT  ?weight
                    WHERE { ?x dt:hasWeightQuestion ?weight.
                           ?x dt:hasKompetensi ?kompetensi. FILTER(?kompetensi=dt:kompetensi2) }
    """ )

    for q66 in query66:
        bobot_we_kompetensi_2 = q66.weight
    
    # membuat data frame untuk kompetensi 1
    df40 = pd.DataFrame(query61, columns = ['bobot_we']) 
    df41 = pd.DataFrame(query66, columns = ['bobot_que']) 
    df42 = pd.DataFrame(query102, columns = ['soal']) 
    df43 = pd.DataFrame(query15, columns = ['soalworkedexample'])
    frames32 = [df40, df41,df42, df43] 


    df5 = pd.concat(frames32, axis=1, join="inner")
    
    #buat matrixnya untuk soal dan worked example yang related terhadap kompetensi 2
    df_result5 = pd.DataFrame(np.zeros((len(df5.bobot_we), len(df5.bobot_que))))

    list_result2 = []

    for i in range(len(df5.bobot_we)):
        tmp_mltp5 = []
        for j in range(len(df5.bobot_que)):
            multiplied5 = (float(df5.bobot_we[i]) * float(df5.bobot_que[j])) / (float(df5.bobot_we[i]) + float(df5.bobot_que[j]))
    #         print(multiplied4)
            result2 = {
                "jaccard": multiplied5,
                "contoh pengerjaan :": df5.soalworkedexample[j]
            }
    #         print(result)
            list_result2.append(result2)

    # print(list_result)
    #         tmp_mltp4.append(multiplied4)
    #     df_result4[i] = tmp_mltp4

    # print("Hasil Perkalian jaccard formula : ")
    # print(df_result4)
    #pd.set_option('display.max_colwidth', None) 
    df_result_final2 = pd.DataFrame(list_result2)
    pd.options.display.max_colwidth =1000
    #a= df_result_final2.set_option('display.max_coldwidth', None)
    #display(df_result_final2)

    Hasil_sorting_kompetensi2=df_result_final2.sort_values(by=['jaccard'], ascending=False)

    #menampilkan 3 teratas  KOMPETENSI 2
    

    Hasil_sorting_kompetensi2_drop = Hasil_sorting_kompetensi2.drop(['jaccard'], axis=1)
    top_theree_Hasil_sorting_kompetensi2= Hasil_sorting_kompetensi2_drop[:2]
    top_theree_Hasil_sorting_kompetensi2 = top_theree_Hasil_sorting_kompetensi2.replace('\n',' ', regex=True)
    number3 = top_theree_Hasil_sorting_kompetensi2.iloc[0] 
    number4 = top_theree_Hasil_sorting_kompetensi2.iloc[1]
    number2_1 = number3.to_string(header=False)
    number2_2 = number4.to_string(header=False)
    
    top_3_we_kompetensi_2 = top_theree_Hasil_sorting_kompetensi2.to_string(header=False)
    
    

    
    
    
    
    #===================================== kompetensi 3 ===================================== #
    graph1 = graph.get_context(onto)
    # menampilkan soal worked example kompetensi 3
    query16= graph1.query(PREFIX + """ 

        SELECT ?SoalWorkedExample
            WHERE { ?item dt:hasSoalWE ?SoalWorkedExample.
            ?item dt:hasKompetensi ?kompetensi.

            FILTER(?kompetensi=dt:kompetensi3) } """)

    for q16 in query16:
        soal_we_kompetensi_3 = q16.SoalWorkedExample
        
        graph1 = graph.get_context(onto)
    # menampilkan soal example kompetensi 3
    query103= graph1.query(PREFIX + """ 

        SELECT ?soal
            WHERE { ?item dt:hasSoal ?soal.
            ?item dt:hasKompetensi ?kompetensi.

            FILTER(?kompetensi=dt:kompetensi3) } """)

    for q103 in query103:
        soal_kompetensi_3 = q103.soal
        
    df25 = pd.DataFrame(query16, columns = ['soalworkedexample'])
    df26 = pd.DataFrame(query103, columns = ['soal'])
    

    # menampilkan bobot soal hanya dengan kompetensi 3
    query62= graph1.query( """ 

                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX dt: <http://www.semanticweb.org/thepermana/ontologies/2021/2/worked_Example_terbaru_2#>

                SELECT  ?weight
                    WHERE { ?x dt:hasWeight ?weight.
                           ?x dt:hasKompetensi ?kompetensi. FILTER(?kompetensi=dt:kompetensi3) }
    """ )

    for q62 in query62:
        bobot_soal_kompetensi_3 = q62.weight
        
        
        # menampilkan bobot worked example dengan hanya dengan kompetensi 3
    query67= graph1.query( """ 

                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX dt: <http://www.semanticweb.org/thepermana/ontologies/2021/2/worked_Example_terbaru_2#>

                SELECT  ?weight
                    WHERE { ?x dt:hasWeightQuestion ?weight.
                           ?x dt:hasKompetensi ?kompetensi. FILTER(?kompetensi=dt:kompetensi3) }
    """ )

    for q67 in query67:
        bobot_we_kompetensi_3 = q67.weight

        
    # membuat data frame untuk kompetensi 3
    df50 = pd.DataFrame(query62, columns = ['bobot_que']) 

    df51 = pd.DataFrame(query67, columns = ['bobot_we']) 
    df52 = pd.DataFrame(query103, columns = ['soal']) 
    df53 = pd.DataFrame(query16, columns = ['soalworkedexample'])
    frames31 = [df50, df51,df52, df53] 


    df6 = pd.concat(frames31, axis=1, join="inner")
    
    #buat matrixnya untuk soal dan worked example yang related terhadap kompetensi 3
    df_result6 = pd.DataFrame(np.zeros((len(df6.bobot_we), len(df6.bobot_que))))

    list_result3 = []

    for i in range(len(df6.bobot_we)):
        tmp_mltp6 = []
        for j in range(len(df6.bobot_que)):
            multiplied6 = (float(df6.bobot_we[i]) * float(df6.bobot_que[j])) / (float(df6.bobot_we[i]) + float(df6.bobot_que[j]))
    #         print(multiplied4)
            result3 = {
                "jaccard": multiplied6,
                "contoh pengerjaan :": df6.soalworkedexample[j]
            }
    #         print(result)
            list_result3.append(result3)

    # print(list_result)
    #         tmp_mltp4.append(multiplied4)
    #     df_result4[i] = tmp_mltp4

    # print("Hasil Perkalian jaccard formula : ")
    # print(df_result4)

    df_result_final3 = pd.DataFrame(list_result3)

    #display(df_result_final3)
    
    

    Hasil_sorting_kompetensi3=df_result_final3.sort_values(by=['jaccard'], ascending=False)
    Hasil_sorting_kompetensi3_drop = Hasil_sorting_kompetensi3.drop(['jaccard'], axis=1)
    top_theree_Hasil_sorting_kompetensi3= Hasil_sorting_kompetensi3_drop[:2]
    
    top_theree_Hasil_sorting_kompetensi3 = top_theree_Hasil_sorting_kompetensi3.replace('\n',' ', regex=True)
    number5 = top_theree_Hasil_sorting_kompetensi3.iloc[0] 
    number6 = top_theree_Hasil_sorting_kompetensi3.iloc[1]
    number3_1 = number5.to_string(header=False)
    number3_2 = number6.to_string(header=False)
    
    top_3_we_kompetensi_2 = top_theree_Hasil_sorting_kompetensi2.to_string(header=False)
    
    
    #===================================== if else recommender  ===================================== #
    
   
    
    
    return render_template('recommender.html', iterator_soal = session['student_model_index'], nilai_siswa =nilai_siswa, number1_1=number1_1, number1_2 = number1_2, number2_1=number2_1, number2_2 = number2_2, number3_1=number3_1, number3_2 = number3_2)



import werkzeug.serving
werkzeug.serving.run_simple("localhost", 8036, app)