from flask import Flask, render_template, request, redirect, url_for, flash
import json
import pymssql
# import _mssql

# import PyMySQL
# from flask_mysqldb import MySQL
# import mysql.connector
import os
from fnmatch import fnmatch
from pathlib import Path
import time
import requests

app = Flask(__name__)
app.secret_key = 'many random bytes'

pricedb = pymssql.connect(host=r'V01SQL01', user=r'guest', password=r'guest',database=r'InfopumpDB')
mydb = pymssql.connect(host=r'V01CIS05T-new', user=r'ZoneAppID', password=r'KsAm3rfd23',database=r'ZoneInspection')

# conn = _mssql.connect(server='V01CIS05T-new', user='ZoneAppID', password='KsAm3rfd23', database='ZoneInspection')


@app.route('/')
@app.route('/ZoneConfig')
@app.route('/ZoneConfig/<int:PlantNum>')
def ConfigIndex(PlantNum=0):
    cur = mydb.cursor()
    if PlantNum > 0:
        cur.execute("SELECT * FROM  ZoneInspConfig where plant = %s", (PlantNum))
    else:
        cur.execute("SELECT * FROM  ZoneInspConfig")

    data = cur.fetchall()
    cur.close()
    return render_template('ZoneConfig.html', zones=data)

@app.route('/update',methods=['POST','GET'])
def update():
    if request.method == 'POST':
        id_data = request.form['id']

        ratio = request.form['ratio']
        cur = mydb.cursor()
        # add some logic to check if current value + other zones for same plant/ veh > 1
        # select .125 +sum(ratio) from ZoneInspConfig where Plant = 1 and zoneid <> 1 and veh = 'Camry'
        cur.execute("""
               UPDATE ZoneInspConfig
               SET ratio =%s
               WHERE ZoneID=%s
            """, (ratio, id_data))
        # flash("Data Updated Successfully")
        cur.connection.commit()
        return redirect(url_for('ConfigIndex'))

@app.route('/Pictures')
def PictureConfig():
    cur = mydb.cursor()

    cur.execute("""SELECT  ZonePictureID,  ZoneInspConfig.Plant,  ZoneInspConfig.Veh,  ZoneInspConfig.ZoneDescription, ZonePictures.Link, PicID
                    FROM   ZonePictures INNER JOIN ZoneInspConfig ON ZonePictures.ZoneID = ZoneInspConfig.ZoneID""")
    data = cur.fetchall()
    cur.close()
    return render_template('Pictures.html', pictures=data)

@app.route('/UpdatePicture',methods=['POST','GET'])
def updatePics():
    if request.method == 'POST':
        id_data = request.form['id']

        link = request.form['link']
        cur = mydb.cursor()
        cur.execute("""
               UPDATE ZonePictures
               SET Link =%s
               WHERE ZonePictureID=%s
            """, (link, id_data))
        # flash("Data Updated Successfully")
        cur.connection.commit()
        return redirect(url_for('PictureConfig'))

@app.route('/ZoneInsp/<string:id_data>')
@app.route('/ZoneInsp/<string:id_data>/<string:PlantNum>')
def InspectionIndex(id_data, PlantNum=None):
    cur = mydb.cursor()
    # 2007956
    cur.execute("select SEQ_NUM, body_num, zonedescription, NextSeq, NextBody, NextZone, VEHICLE_ID  from tvfGetVehInspectionPlant ( %s)", (id_data,))
    Inspdata = cur.fetchall()
    # cur.close()

    cur.execute("select * from tvfGetVehInspectionPics ( %s)",
        (id_data,))
    Picdata = cur.fetchall()
    cur.close()
    # x = json.dumps(data)
    # print (json.dumps(data))
    # print(response)
    return render_template('Inspection.html',insps=Inspdata,pics=Picdata)

#simple datatable@app.route('/ZoneConfig')
@app.route('/SimpleDT')
def SimpleDT():
    cur = mydb.cursor()
    cur.execute("SELECT * FROM  ZoneInspConfig")
    data = cur.fetchall()
    cur.close()
    return render_template('simpleDataTable.html',zones=data)


# Price Search
@app.route('/prices')
def Index():
    return render_template('PriceSearch.html')

@app.route('/search', methods = ['POST'])
def search():

    if request.method == "POST":
        part = request.form['part']
        part = "%" + part + "%"

        cur = pricedb.cursor()

        cur.execute("""SELECT  dbo.PARSCIT.ITEM_ID, dbo.PARSCIT.QUANTITY, dbo.PARSCIT.COST
                        ,format(cast(case when COST>0 and QUANTITY >0 then COST/QUANTITY else 0 end as decimal(10,2)),'C', 'en-US' )  AS Each
                        --,cast(COST/QUANTITY as decimal(10,2))*1  AS Each
                        FROM            dbo.PARSCIT INNER JOIN
                                                     (SELECT        MAX(SEQUENCE) AS Expr1, ITEM_ID
                                                       FROM            dbo.PARSCIT AS PARSCIT_1
                                                       WHERE        (ITEM_ID like  %s)
                                                       and QUANTITY >0 and COST > 0
                                                       GROUP BY ITEM_ID) AS dtLastRecord ON dbo.PARSCIT.SEQUENCE = dtLastRecord.Expr1 AND dbo.PARSCIT.ITEM_ID = dtLastRecord.ITEM_ID
                                                       where QUANTITY >0 and COST > 0""",(part))
        data = cur.fetchall()
        cur.close()
        return render_template('PriceSearch.html', prices=data)

@app.route('/insert', methods = ['POST'])
def insert():

    if request.method == "POST":
        flash("Data Inserted Successfully")
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        cur = mydb.cursor()
        # cur = mydb.cursor()
        # print (name, email, phone)
        cur.execute("INSERT INTO students"
                    " (name, email, phone) VALUES (%s, %s, %s)", (name, email, phone))
        cur.connection.commit()
        return redirect(url_for('Index'))

if __name__ == "__main__":
    app.run(debug=True)
