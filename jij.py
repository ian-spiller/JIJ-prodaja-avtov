from pickle import FALSE, TRUE
from bottle import *
import psycopg2


from conf_baza import *
conn_string = "host='{0}' dbname='{1}' user='{2}' password='{3}'".format(host, dbname ,user,password) 
baza = psycopg2.connect(conn_string)
cur=baza.cursor()

skrivnost="asdfghjkl12345"

@get("/prijava")
def prijavno_okno():
    return template("prijava.html")

@post("/prijava")
def prijava():
    uporabnisko_ime=request.forms.get("uporabnisko_ime")
    geslo=request.forms.get("geslo")
    if uporabnisko_ime is None or geslo is None:
        return """<p> Prosimo izplonite vsa polja</p>"""
    if not preveri(uporabnisko_ime,geslo):
        """<p> Napačni podatki za prijavo. Poskusite <a href="/prijava">še enkrat</a> ali pa se <a href="/registracija">registrirajte</a> </p>"""
    cur.execute("SELECT id  FROM oseba WHERE uporabnisko_ime=%s",(uporabnisko_ime,))
    a=cur.fetchall()
    response.set_cookie("id_uporabnika",a,secret=skrivnost)
    redirect("/izbira")

@get('/odjava')
def odjava_get():
    response.delete_cookie('uporabnisko_ime')
    redirect('/prijava')

@get("/registracija")
def registracija():
    cur.execute("SELECT id , ime_zavarovalnice FROM zavarovalnica")
    a=cur.fetchall()
    return template("registracija.html",a=a)

@post("/registracija")
def reg():
    ime=request.forms.get("ime")
    uporabnisko_ime=request.forms.get("uporabnisko_ime")
    geslo=request.forms.get("geslo")
    tel=request.forms.get("tel")
    id_zav=request.forms.get("zav")
    if preveri_uporab_ime(uporabnisko_ime)==FALSE:
        return """<p>Uporabniško ime je zasedeno</p>"""
    cur.execute("INSERT INTO oseba VALUES(%s, %s, %s, %s, %s)",(ime,id_zav,tel,geslo,uporabnisko_ime))
    cur.execute("SELECT id FROM oseba WHERE uporabnisko_ime=%s",(uporabnisko_ime,))
    a=cur.fetchall()
    response.set_cookie("id_uporabnika",a,secret=skrivnost)
    baza.commit()
    redirect("/izbira")

@get("/izbira")
def izbira():
    return template("izbira.html")

@get("/filter")
def filter():
    cur.execute("SELECT id , ime_znamke FROM znamka")
    a=cur.fetchall()
    a=[(0,"Vse")]+a
    cur.execute("SELECT * FROM modeli")
    seznam_modelov=cur.fetchall()
    seznam_modelov1=popravi_seznam(seznam_modelov)
    seznam_modelov1=[(1,"Vse")]+seznam_modelov1
    return template("filter.html",znamkeid=a,seznam_modelov=seznam_modelov1)

@get("/rezultati")
def rezultati():
    znamka=request.query["znamka"]
    znamka=znamka.encode("ISO-8859-1")
    znamka=znamka.decode("utf-8")
    cena=request.query["cena"]
    stanje=request.query["stanje"]
    oblika=request.query["oblika"]
    kilometri=request.query["kilometri"]
    gorivo=request.query["gorivo"]

    id_uporab=request.get_cookie("id_uporabnika",secret=skrivnost)
    cur.execute("SELECT id_zavarovalnice FROM oseba WHERE id=%s",((id_uporab[0])[0],))
    id_zav=cur.fetchall()
    id_zav=id_zav[0]
    print(id_zav)

    cur.execute("SELECT premija1, popust FROM zavarovalnica WHERE id=%s",id_zav)
    premija_popust1=cur.fetchall()
    finan_ugodno1=(1-(premija_popust1[0])[1])*((premija_popust1[0])[0])
    cur.execute("SELECT premija1 FROM zavarovalnica WHERE id != %s",id_zav)
    a1=cur.fetchall()


    cur.execute("SELECT premija2, popust FROM zavarovalnica WHERE id=%s",id_zav)
    premija_popust2=cur.fetchall()
    finan_ugodno2=(1-(premija_popust2[0])[1])*((premija_popust2[0])[0])
    cur.execute("SELECT premija2 FROM zavarovalnica WHERE id != %s",id_zav)
    a2=cur.fetchall()
    
    cur.execute("""SELECT ime_znamke FROM oglas 
                    JOIN znamka ON oglas.id_znamke = znamka.id 
                    JOIN serviser ON znamka.id_serviserja = serviser.id
                    JOIN zavarovalnica ON serviser.id_zavarovalnice = zavarovalnica.id
                    WHERE zavarovalnica.id=%s""",id_zav)
    ugoden_servis_znamka=cur.fetchall()
    ugoden_servis_znamka1=[]
    for x in ugoden_servis_znamka:
        ugoden_servis_znamka1=ugoden_servis_znamka1+[str(x[0])]
    print(ugoden_servis_znamka1)


    cur.execute("SELECT ime_znamke FROM znamka")
    b=cur.fetchall()
    model="Vse"
    for x in range(1,len(b)+1):
        if request.query["model{}".format(x)]!="Vse":
            model=request.query["model{}".format(x)]

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
    return template("rezultati.html",oglasi=oglasi,
        finan_ugodno1=finan_ugodno1,finan_ugodno2=finan_ugodno2,seznam_premij1=a1,seznam_premij2=a2,
        ugoden_servis_znamka1=ugoden_servis_znamka1)

def preveri_uporab_ime(ime):
    cur.execute("SELECT ime FROM oseba")
    a=cur.fetchall()
    for x in a:
        if x[0]==ime:
            return FALSE

def preveri(ime,geslo):
    cur.execute("SELECT ime , geslo FROM oseba")
    a=cur.fetchall()
    for x in a:
        if x[0]==ime and x[1]==geslo:
            return TRUE

def popravi_seznam(seznam):
    popravljen_seznam=[seznam[0]]
    for x in range(1,len(seznam)):
        if (seznam[x])[0] is not (seznam[x-1])[0]:
            popravljen_seznam=popravljen_seznam+[(((seznam[x])[0]),"Vse")] + [seznam[x]]
        else:
            popravljen_seznam=popravljen_seznam+[seznam[x]]
    return popravljen_seznam


run(host="localhost", port=8080, reloader=True)