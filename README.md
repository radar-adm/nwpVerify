# nwpVerify

require module :: 
xlrd
pandas
numpy

Add GRIB directory in "data" 
---> format "yyyymm" ... ex. "202003"
---> csv name format : "grib_yyyymmdd.csv" ex."grib_20200301.csv"

----------------////------------------

Add Decode xls in "obs"

--------------- /// ------------------

Line 10 : Choose dataname by 1
'mslp' for Mean Sea Level
'rain' for precipitation
'temp' for Temperature
'rh' for Relative Humidity

Line 11 : matching "yyyymm" in GRIB data
LINE 12 : Decode file path
