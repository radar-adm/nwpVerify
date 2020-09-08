import pandas as pd

from datetime import datetime
from datetime import timedelta
import os
import numpy as np
import xlrd

# dataName : [mslp , rain , temp , rh]
dataName = 'mslp'
month_ = '202003'
obs = './obs/2020-03-01-Decode.xls'
csvGRIBpath = './data/' + month_

def getData_in_xlSheet(xsheet):
    
    start_collect_data = False

    station_set = ["Northern\nStation Name" , \
                   "Northeastern\nStation Name" , \
                   "Central\nStation Name" , \
                   "Eastern\nStation Name" , \
                   "Southern(east coast)\nStation Name" , \
                   "Southern(west coast)\nStation Name" ]

    start_callect_data = False
    preparing_to_stop = "wait"
    stn = []
    mslpRow = []
    tempRow = []
    precRow = []
    rhumRow = []

    ridx = 0
    while True:
        row = xsheet.row(ridx)
        station_pos = row[0]
        if start_callect_data:
            if str(station_pos) != "empty:''":
                mslp = row[1].value
                temp = row[2].value
                prec = row[7].value
                rhum = row[9].value
                
                stnName = row[0].value.replace('(' , '')
                stnName = stnName.replace(')' ,'')
                stnName = stnName.replace(' ','')
                stnName = stnName.lower()
                stn.append(stnName)
                mslpRow.append(mslp)
                tempRow.append(temp)
                precRow.append(prec)
                rhumRow.append(rhum)

        if station_pos.value in station_set:
            start_callect_data = True

        if str(station_pos) == "empty:''":
            start_callect_data = False

        if station_pos.value == "Southern(west coast)\nStation Name":
            preparing_to_stop = "preparing"

        if row[0].value == "Satun":
            break
                
        ridx += 1
        
    return stn , mslpRow , tempRow , precRow , rhumRow

def autoFilledData(olst):
    for tup in enumerate(olst):
        idx = tup[0]
        oitem = tup[1]
        if idx == 0 and oitem == '-':
            olst[idx] = olst[idx + 1]
        if oitem == '-':
            olst[idx] = olst[idx - 1]
    return olst

def autoFilledPrecipitation(olst):
    for tup in enumerate(olst):
        idx = tup[0]
        oitem = tup[1]
        if oitem == '-':
            olst[idx] = 0
        if oitem == 'T':
            olst[idx] = 0.1
    return olst


with open('./latlonstn.csv' , 'r') as dummy:
    buffer = dummy.read()
metadata = buffer.split('\n')
del metadata[-1]
stnTbl = []
for row in metadata:
    info = row.split(',')
    stnTbl.append([info[1] , info[3] , info[5]])

stnHeader = ['lng' , 'lat' , 'stnName']
dfStn = pd.DataFrame( stnTbl , columns = stnHeader )

stnLower = []
for stn in list(dfStn['stnName'].values):
    text = stn.replace(' ','').lower()
    stnLower.append(text)
dfStn['stnNameLower'] = stnLower

filelist = sorted(os.listdir(csvGRIBpath))
header = []
tbl = []
for fn in filelist:
    xtime = datetime.strptime(fn , 'grib_%Y%m%d.csv')
    dtime = datetime.strftime(xtime , '%Y-%m-%d')
    with open(os.path.join(dmPath_ , fn) , 'r') as dummy:
        buff = dummy.read()
    data = buff.split('\n')
    del data[-1]
    tbl.append(data)
    header.append(dtime)
tbl = np.transpose(np.float32(tbl)) / 100
df = pd.DataFrame(tbl , columns = header)
dfGRIB = pd.concat([dfStn , df] , axis = 1)
csv_grib_output = dataName + '.' + dm + '.grib2.csv'
dfGRIB.to_csv(csv_grib_output , index = False)

xl_workbook = xlrd.open_workbook(obs)
sheet_names = xl_workbook.sheet_names()

mslpTBL = []
tempTBL = []
precTBL = []
rhumTBL = []

date = ['stnNameLower']
for name in sheet_names:
    if name.isnumeric():
        date.append(name)
        day = int(name)
        xl_sheet = xl_workbook.sheet_by_name(name)
        stnlist , mslp , temp , prec , rhum = getData_in_xlSheet(xsheet = xl_sheet)
        mslp = autoFilledData(mslp)
        temp = autoFilledData(temp)
        prec = autoFilledData(prec)
        rhum = autoFilledData(rhum)
        mslpTBL.append(np.array(mslp))
        tempTBL.append(np.array(temp))
        precTBL.append(np.array(prec))
        rhumTBL.append(np.array(rhum))
        
mslpTBL.insert(0 , stnlist)
mslpTBL = np.array(mslpTBL).T
tempTBL.insert(0 , stnlist)
tempTBL = np.array(tempTBL).T
precTBL.insert(0 , stnlist)
precTBL = np.array(precTBL).T
rhumTBL.insert(0 , stnlist)
rhumTBL = np.array(rhumTBL).T

dfObserver_MSLP = pd.DataFrame( mslpTBL , columns = date)
dfObserver_TEMP = pd.DataFrame( tempTBL , columns = date)
dfObserver_PREC = pd.DataFrame( precTBL , columns = date)
dfObserver_RHUM = pd.DataFrame( rhumTBL , columns = date)

if dataName == 'mslp':
    dfDECODE = pd.merge(dfStn , dfObserver_MSLP, on='stnNameLower', how='left')
if dataName == 'rain':
    dfDECODE = pd.merge(dfStn , dfObserver_TEMP, on='stnNameLower', how='left')
if dataName == 'temp':
    dfDECODE = pd.merge(dfStn , dfObserver_PREC, on='stnNameLower', how='left')
if dataName == 'rh':
    dfDECODE = pd.merge(dfStn , dfObserver_RHUM, on='stnNameLower', how='left')

csv_decode_output = dataName + '.' + month_ + '.decode.csv'
dfDECODE.to_csv(csv_decode_output , index = False)

decodeDataset = np.float32(dfDECODE.values[:,4:])
forecastDataset = np.float32(dfGRIB.values[:,4:])

RMSE = np.round( np.sqrt(np.mean((decodeDataset - forecastDataset)**2 , axis = 1)) , 2)

dfStn['RMSE'] = RMSE
dfStn.to_csv(dataName + '.' + month_ + '.verify.csv' , index = False)