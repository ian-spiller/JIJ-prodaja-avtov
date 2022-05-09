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