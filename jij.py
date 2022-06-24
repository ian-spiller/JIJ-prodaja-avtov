from pickle import FALSE, TRUE
from bottleext import *
import psycopg2


from conf_baza import *
conn_string = "host='{0}' dbname='{1}' user='{2}' password='{3}'".format(host, dbname ,user,password) 
baza = psycopg2.connect(conn_string)
cur=baza.cursor()

skrivnost="asdfghjkl12345"

@get("/")
def prijavno():
    return template("prijava.html")

@post("/")
def prijava():
    uporabnisko_ime=request.forms.get("uporabnisko_ime")
    geslo=request.forms.get("geslo")
    print(geslo)
    if uporabnisko_ime=="" or geslo=="":
        return template("prijava.html",napaka="Prosimo izpolnite vsa polja")
    if not preveri(uporabnisko_ime,geslo):
        return template("prijava.html",napaka="Vaše uporabniško ime ali geslo ni pravilno")
    cur.execute("SELECT id,administrator FROM oseba WHERE uporabnisko_ime=%s",(uporabnisko_ime,))
    a=cur.fetchall()
    response.set_cookie("id_uporabnika",(str(a[0][0]),str(a[0][1])),secret=skrivnost)
    if a[0][1]==1:
        redirect(url("izbira_administrator"))
    else:
        redirect(url("izbira"))

@get('/odjava')
def odjava():
    response.delete_cookie('uporabnisko_ime')
    redirect(url(''))

@get("/registracija")
def registracija():
    cur.execute("SELECT id , ime_zavarovalnice FROM zavarovalnica")
    a=cur.fetchall()
    return template("registracija.html",a=a)

@post("/registracija")
def registracija():
    ime=request.forms.get("ime")
    ime=ime.encode("ISO-8859-1")
    ime=ime.decode("utf-8")
    uporabnisko_ime=request.forms.get("uporabnisko_ime")
    uporabnisko_ime=uporabnisko_ime.encode("ISO-8859-1")
    uporabnisko_ime=uporabnisko_ime.decode("utf-8")
    geslo=request.forms.get("geslo")
    geslo=geslo.encode("ISO-8859-1")
    geslo=geslo.decode("utf-8")
    tel=request.forms.get("tel")
    id_zav=request.forms.get("zav")
    cur.execute("SELECT id , ime_zavarovalnice FROM zavarovalnica")
    a=cur.fetchall()
    if ime=="" or uporabnisko_ime=="" or geslo=="" or tel=="" or id_zav=="": 
        return template("registracija.html", napaka="Prosimo izpolnite vsa polja",a=a)
    if preveri_uporab_ime(uporabnisko_ime)==FALSE:
        return template("registracija.html", napaka="To uporabniško ime je že zasedeno",a=a)
    if "Ž" in uporabnisko_ime or "ž" in uporabnisko_ime or "Š" in uporabnisko_ime or "š" in uporabnisko_ime or "Č" in uporabnisko_ime or "č" in uporabnisko_ime:
        return template("registracija.html", napaka="Uporabniško ime nesme vključevati šumnikov",a=a)
    if " " in uporabnisko_ime:
        return template("registracija.html", napaka="Uporabniško ime nesme vključevati presledkov",a=a)
    if " " in geslo:
        return template("registracija.html", napaka="Geslo nesme vključevati presledkov",a=a)
    if len(str(geslo))<5:
        return template("registracija.html", napaka="Geslo mora vsebovati vsaj pet znakov",a=a)
    if len(str(tel))<9 or len(str(tel))>9:
        return template("registracija.html", napaka="Prosimo vnesite resnično telefonsko številko",a=a)
    cur.execute("""INSERT INTO oseba (ime,id_zavarovalnice,telefon,geslo,uporabnisko_ime,administrator) 
        VALUES(%(ime)s, %(zav)s, %(tel)s, %(geslo)s, %(uporabnisko_ime)s,%(administrator)s)""", 
        {"ime":ime,"zav":id_zav,"tel":int(tel),"geslo":geslo,"uporabnisko_ime":uporabnisko_ime,"administrator":0})

    cur.execute("SELECT id,administrator FROM oseba WHERE uporabnisko_ime=%s",(uporabnisko_ime,))
    a=cur.fetchall()
    response.set_cookie("id_uporabnika",(str(a[0][0]),str(a[0][1])),secret=skrivnost)
    baza.commit()
    redirect(url("izbira"))


@get("/izbira")
def izbira():
    cookie=request.get_cookie("id_uporabnika",secret=skrivnost)
    if cookie is None:
        redirect(url(""))
    return template("izbira.html")

@get("/izbira_administrator")
def izbira_administrator():
    cookie=request.get_cookie("id_uporabnika",secret=skrivnost)
    if cookie is None:
        redirect(url(""))
    return template("izbira_administrator.html")

@get("/filter")
def filter():
    cur.execute("SELECT id , ime_znamke FROM znamka")
    a=cur.fetchall()
    a=[(0,"Vse")]+a
    cur.execute("SELECT * FROM modeli")
    seznam_modelov=cur.fetchall()
    seznam_modelov1=popravi_seznam(seznam_modelov)

    cookie=request.get_cookie("id_uporabnika",secret=skrivnost)
    if cookie is None:
        redirect(url(""))
    uporabnik=int(cookie[1])

    return template("filter.html",znamkeid=a,seznam_modelov=seznam_modelov1,uporabnik=uporabnik)

@get("/rezultati")
def rezultati():
    znamka=request.query["znamka"]
    cena=request.query["cena"]
    stanje=request.query["stanje"]
    oblika=request.query["oblika"]
    kilometri=request.query["kilometri"]
    gorivo=request.query["gorivo"]

    cookie=request.get_cookie("id_uporabnika",secret=skrivnost)
    if cookie is None:
        redirect(url(""))

    id_uporab=cookie[0]
    uporabnik=int(cookie[1])
    cur.execute("SELECT id_zavarovalnice FROM oseba WHERE id=%s",((id_uporab[0])[0],))
    id_zav=cur.fetchall()
    id_zav=id_zav[0]

    cur.execute("SELECT premija1, premija2 FROM zavarovalnica WHERE id=%s",id_zav)
    premija=cur.fetchall()
    
    
    cur.execute("""SELECT ime_znamke FROM oglas 
                    JOIN znamka ON oglas.id_znamke = znamka.id 
                    JOIN serviser ON znamka.id_serviserja = serviser.id
                    JOIN zavarovalnica ON serviser.id_zavarovalnice = zavarovalnica.id
                    WHERE zavarovalnica.id=%s""",id_zav)
    ugoden_servis_znamka=cur.fetchall()
    ugoden_servis_znamka1=[]
    for x in ugoden_servis_znamka:
        if not str(x[0]) in ugoden_servis_znamka1:
            ugoden_servis_znamka1=ugoden_servis_znamka1+[str(x[0])]
    
    model="Vse"
    if znamka!="Vse":
        if request.query["model{}".format(znamka)]!="Vse":
            model=request.query["model{}".format(znamka)]
    else:
        model="Vse"

    cur.execute("SELECT model FROM modeli")
    c=cur.fetchall()
    if model=="Vse":
        model= tuple(c)
    else:
        model=(model,)
    
    cur.execute("SELECT ime_znamke FROM znamka")
    d=cur.fetchall()
    if znamka=="Vse":
        znamka= tuple(d)
    else:
        znamka=(znamka,)
    
    if cena=="":
       cena=(100000000,) 
    else:
        cena=(cena,)

    if stanje=="Vse":
        stanje=("rabljeno","novo","testno")                   
    else:
        stanje=(stanje,) 

    if oblika=="Vse":
        oblika=("SUV","limuzina","karavan","coupe","kabrijolet")                   
    else:
        oblika=(oblika,) 
    
    if kilometri=="":
       kilometri=(1000000000,)
    else:
        kilometri=(kilometri,)

    if gorivo=="Vse":
        gorivo=("bencin","dizel","hibrid","elektrika")                   
    else:
        gorivo=(gorivo,)  
    
    cur.execute("""SELECT ime_znamke, cena, stanje, oblika, kilometri, gorivo, model, id_zavarovalnice FROM oglas 
                    JOIN znamka ON oglas.id_znamke = znamka.id 
                    JOIN serviser ON znamka.id_serviserja = serviser.id
                    JOIN zavarovalnica ON serviser.id_zavarovalnice = zavarovalnica.id
                    WHERE ime_znamke IN %(znamka)s
                    AND cena < %(cena)s
                    AND stanje IN %(stanje)s
                    AND oblika IN %(oblika)s
                    AND kilometri < %(kilometri)s
                    AND gorivo IN %(gorivo)s
                    AND model IN %(model)s
                    """, {'znamka': znamka , 'cena':cena , 'stanje':stanje , 
                            'oblika':oblika, 'kilometri':kilometri , 'gorivo':gorivo,
                            'model':model })
    oglasi=cur.fetchall()
    if len(oglasi)==0:
        napaka = "Za vaše iskanje ni rezultatov"
        return template("rezultati.html",oglasi=oglasi,
            finan_ugodno1=premija[0][0],finan_ugodno2=premija[0][1],
            ugoden_servis_znamka1=ugoden_servis_znamka1,uporabnik=uporabnik,napaka=napaka)
    return template("rezultati.html",oglasi=oglasi,
        finan_ugodno1=premija[0][0],finan_ugodno2=premija[0][1],
        ugoden_servis_znamka1=ugoden_servis_znamka1,uporabnik=uporabnik)

@get("/objava")
def objava():
    cur.execute("SELECT id , ime_znamke FROM znamka")
    a=[(0,"Izberite")]+cur.fetchall()
    cur.execute("SELECT * FROM modeli")
    seznam_modelov=cur.fetchall()
    seznam_modelov1=popravi_seznam1(seznam_modelov)

    cookie=request.get_cookie("id_uporabnika",secret=skrivnost)
    if cookie is None:
        redirect(url(""))
    uporabnik=int(cookie[1])

    return template("objava.html",znamkeid=a,seznam_modelov=seznam_modelov1, uporabnik=uporabnik)

@post("/objava")
def objava():
    id_uporab=request.get_cookie("id_uporabnika",secret=skrivnost)
    znamka=request.forms.get("znamka")
    cena=request.forms.get("cena")
    stanje=request.forms.get("stanje")
    oblika=request.forms.get("oblika")
    kilometri=request.forms.get("kilometri")
    gorivo=request.forms.get("gorivo")
    letnik=request.forms.get("letnik")

    cur.execute("SELECT id , ime_znamke FROM znamka")
    a=cur.fetchall()

    for x in a:
        if x[1]==znamka:
            znamka_id=x[0]

    model="Izberite"
    if request.forms.get("model{}".format(znamka)) !="Izberite":
        model=request.forms.get("model{}".format(znamka))

    cookie=request.get_cookie("id_uporabnika",secret=skrivnost)
    if cookie is None:
        redirect(url(""))

    uporabnik=int(cookie[1])
            
    if model=="Izberite" or znamka=="" or cena=="" or stanje=="" or oblika=="" or kilometri=="" or gorivo=="" or letnik=="":
        cur.execute("SELECT id , ime_znamke FROM znamka")
        a=[(0,"Izberite")]+cur.fetchall()
        cur.execute("SELECT * FROM modeli")
        seznam_modelov=cur.fetchall()
        seznam_modelov1=popravi_seznam1(seznam_modelov)
        seznam_modelov1=[(1,"Izberite")]+seznam_modelov1
        return template("objava.html",znamkeid=a,seznam_modelov=seznam_modelov1,napaka="Prosimo izpolnite vsa polja",uporabnik=uporabnik)

    cur.execute("INSERT INTO oglas (id_znamke,cena,stanje,oblika,kilometri,gorivo,letnik,model,id_osebe) VALUES(%s, %s, %s, %s, %s,%s,%s,%s,%s)",
        (znamka_id,cena,stanje,oblika,kilometri,gorivo,int(letnik),model,(id_uporab[0])[0]))
    baza.commit()

    if uporabnik==1:
        redirect(url("izbira_administrator"))
    if uporabnik==0:
        redirect(url("izbira"))

@get("/dodaj_znamko")
def dodaj_znamko():
    cur.execute("SELECT id,ime_serviserja FROM serviser")
    cookie=request.get_cookie("id_uporabnika",secret=skrivnost)
    if cookie is None:
        redirect(url(""))
    a=cur.fetchall()
    return template("dodaj_znamko.html",podatki_serviserja=a)

@post("/dodaj_znamko")
def dodaj_znamko():
    dodana_znamka=request.forms.get("dodana_znamka")
    model=request.forms.get("model")
    id_serviserja=request.forms.get("id_serviserja")
    
    cur.execute("SELECT id,ime_serviserja FROM serviser")
    a=cur.fetchall()

    if "Ž" in dodana_znamka or "ž" in dodana_znamka or "Š" in dodana_znamka or "š" in dodana_znamka or "Č" in dodana_znamka or "č" in dodana_znamka:
        return template("dodaj_znamko.html", napaka="Ime znamke nesme vključevati šumnikov",a=a)

    if dodana_znamka=="":
        return template("dodaj_znamko.html",podatki_serviserja=a,napaka="Prosimo izpolnite vsa polja")

    if "Ž" in model or "ž" in model or "Š" in model or "š" in model or "Č" in model or "č" in model:
        return template("dodaj_znamko.html", napaka="Ime modela nesme vključevati šumnikov",a=a)

    if model=="":
        return template("dodaj_znamko.html",podatki_serviserja=a,napaka="Prosimo izpolnite vsa polja")

    cur.execute("SELECT ime_znamke FROM znamka")
    b=cur.fetchall()
    if dodana_znamka in b:
        return template("dodaj_znamko.html",podatki_serviserja=a,napaka="Ta znamka že obstaja")

    cur.execute("INSERT INTO znamka (ime_znamke,id_serviserja) VALUES(%s, %s)",
        (dodana_znamka,id_serviserja))
    baza.commit()

    cur.execute("SELECT id FROM znamka WHERE ime_znamke=%s",(dodana_znamka,))
    id_znamka=cur.fetchall()
    print(id_znamka)
    cur.execute("INSERT INTO modeli VALUES(%s, %s)",
        (id_znamka[0][0],model))
    baza.commit()
    redirect(url("izbira_administrator"))

@get("/dodaj_model")
def dodaj_model():
    cookie=request.get_cookie("id_uporabnika",secret=skrivnost)
    if cookie is None:
        redirect(url(""))

    cur.execute("SELECT id , ime_znamke FROM znamka")
    a=cur.fetchall()
    return template("dodaj_model.html",seznam_znamk=a)

@post("/dodaj_model")
def dodaj_model():
    znamka=request.forms.get("znamka")
    dodan_model=request.forms.get("dodan_model")

    cur.execute("SELECT id , ime_znamke FROM znamka")
    a=cur.fetchall()

    if dodan_model=="":
        return template("dodaj_model.html",seznam_znamk=a,napaka="Prosimo izpolnite vsa polja")
    
    if "Ž" in dodan_model or "ž" in dodan_model or "Š" in dodan_model or "š" in dodan_model or "Č" in dodan_model or "č" in dodan_model:
        return template("dodaj_znamko.html", napaka="Ime znamke nesme vključevati šumnikov",a=a)

    cur.execute("INSERT INTO modeli VALUES(%s, %s)",
        (znamka,dodan_model))
    baza.commit()
    redirect(url("izbira_administrator"))

@get("/dodaj_administratorja")
def dodaj_administratorja():
    cookie=request.get_cookie("id_uporabnika",secret=skrivnost)
    if cookie is None:
        redirect(url(""))
    
    cur.execute("SELECT uporabnisko_ime FROM oseba WHERE administrator=0")
    a=cur.fetchall()
    return template("dodaj_administratorja.html",seznam_oseb=a)

@post("/dodaj_administratorja")
def dodaj_administratorja():
    oseba=request.forms.get("oseba")
    cur.execute("UPDATE oseba SET administrator = 1 WHERE uporabnisko_ime = %s",(oseba,))
    baza.commit()
    redirect(url("izbira_administrator"))

def preveri_uporab_ime(ime):
    cur.execute("SELECT uporabnisko_ime FROM oseba")
    a=cur.fetchall()
    for x in a:
        if x[0]==ime:
            return FALSE

def preveri(ime,geslo):
    cur.execute("SELECT uporabnisko_ime , geslo FROM oseba")
    a=cur.fetchall()
    for x in a:
        if x[0]==ime and x[1]==geslo:
            return TRUE

def popravi_seznam(seznam):
    popravljen_seznam=[]
    for x in range(0,len(seznam)):
        a=0
        for y in range(0,x):
            if (seznam[x])[0] == (seznam[y])[0]:
                a=a+1
        if a==0:
            popravljen_seznam=popravljen_seznam+[(((seznam[x])[0]),"Vse")] + [seznam[x]]
        else:
            popravljen_seznam=popravljen_seznam+[seznam[x]]
    return popravljen_seznam

def popravi_seznam1(seznam):
    popravljen_seznam=[]
    for x in range(0,len(seznam)):
        a=0
        for y in range(0,x):
            if (seznam[x])[0] == (seznam[y])[0]:
                a=a+1
        if a==0:
            popravljen_seznam=popravljen_seznam+[(((seznam[x])[0]),"Izberite")] + [seznam[x]]
        else:
            popravljen_seznam=popravljen_seznam+[seznam[x]]
    return popravljen_seznam

run(host="localhost", port=8080, reloader=True)