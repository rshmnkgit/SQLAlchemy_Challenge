import numpy as np
import os
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
os.chdir(os.path.dirname(os.path.abspath(__file__)))
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Function to convert the query result set into 
# a list of dictionaries, to be jsonified
#################################################
def query_to_dictlist(keylist, obj):
    result_list = []
    for row in obj:
        mydict = {}
        for i in range(0,len(keylist)):
            mydict[keylist[i]] = row[i]
        result_list.append(mydict)
    return result_list

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################          
#  Home Page ====================================
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"<h1>Step 2 - Climate App</h1>"
        f"<p>Copy the link and paste it on the adress bar after the ip address</p>"
        f"<h3>Available Links:</h3>"
        f"<ol>"
        # <a href="https://www.w3schools.com">Visit W3Schools.com!</a>
        f"<p><li> Precipitation of Hawaii</p>"
        f'<p>/api//v1.0//precipitation</li></p>'
        f"<p><li> List of all Stations</p>"
        f'<p>/api//v1.0//station</li></p>'
        f"<p><li> Temperature Readings of Hawaii between 2016-08-23 and 2017-08-23</p>"
        f'<p>/api//v1.0//tobs</li></p>'
        f"<p><li> Temperature starting from a specific date. <br>"
        f" Replace the word <strong>start</strong> in the address bar </em>  with a start date (any date between <strong>2010-01-01</strong> and <strong>2017-08-23</strong>) in the format 'yyyy-mm-dd'</p>"
        f'<p>/api//v1.0//start</li></p>'
        f"<p><li> Temperature between two specific dates <br>"
        f" Replace the words <strong>start</strong> and <strong>end</strong> in the address bar </em> (with any dates between <strong>2010-01-01</strong> and <strong>2017-08-23</strong>) in the format 'yyyy-mm-dd'</p>"
        f'<p>/api//v1.0//start/end</li></p>'
        f"</ol>"
    )

#=============== Precipitation =================================
# Convert the query results to a dictionary using `date` as the key and `prcp` as the value.
# Return the JSON representation of your dictionary.
#===============================================================
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    maxdate_str = session.query(func.max(Measurement.date)).scalar()
    last_date = dt.datetime.strptime(maxdate_str, '%Y-%m-%d').date()                  
    yearago_date = last_date.replace(year = last_date.year -1)

    result_set = session.query(Measurement.prcp, Measurement.date).\
                filter(Measurement.prcp != "None").\
                filter(Measurement.date >= yearago_date).\
                filter(Measurement.date <= last_date).all()

    session.close()

    # Create a dictionary from the row data and append to a list 
    precipitation_data = query_to_dictlist(['date','precp'], result_set)

    return jsonify(precipitation_data)


#===================  Stations Data  ====================
#  Return a JSON list of stations from the dataset.
#========================================================
@app.route("/api/v1.0/station")
def station():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all stations
    results = session.query(Station.name, Station.station, Station.latitude, Station.longitude).all()
    session.close()

    # Create a dictionary from the row data and append to a list 
    keylist = ['name', 'station', 'latitude', 'longitude']
    station_data = query_to_dictlist(keylist, results)
    return jsonify(station_data)


#===================  Temperature Data  =============================
# Query the dates and temperature observations of the most active station for the last year of data.
# Return a JSON list of temperature observations (TOBS) for the previous year.
#====================================================================
@app.route("/api/v1.0/tobs")
def tobs():
    # Create a session to retrieve data from DB
    session = Session(engine)
    
    # Get the most active station
    most_active = session.query(Measurement.station, func.count(Measurement.station)).\
            filter(Measurement.station == Station.station).\
            group_by(Measurement.station).\
            order_by(func.count(Measurement.station).desc()).first()

    # Get the start and end dates for the last year data
    maxdate_str = session.query(func.max(Measurement.date)).first()
    last_date = dt.datetime.strptime(maxdate_str[0], '%Y-%m-%d').date()                  
    yearago_date = last_date - dt.timedelta(days=365)

    # Query the last year temperature observation data for this station
    tobs_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active.station).\
        filter(Measurement.date.between(yearago_date, last_date)).all()
    session.close()

    # Create a dictionary from the row data and append to a list 
    temperature_data = query_to_dictlist(['date', 'tobs'], tobs_data)
    return jsonify(temperature_data)

#===============  Given Start Date ==============================
# When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` 
# for all dates greater than and equal to the start date
#================================================================
@app.route("/api/v1.0/<start>")
def startdate(start):
    session = Session(engine)
    result_set = session.query(func.min(Measurement.date), func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                filter(Measurement.date >= start).all()
    session.close()

    # Create a dictionary from the row data and append to a list 
    key_list = ['start date', 'min temp', 'avg temp', 'max temp']
    temp_data = query_to_dictlist(key_list, result_set)
    
    return jsonify(temp_data)

#============  Given Start and End Dates  =======================================
# When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` 
# for dates between the start and end date inclusive
#=================================================================================
@app.route("/api/v1.0/<start>/<end>")
def startoend(start, end):
    session = Session(engine)
    result_set = session.query(func.min(Measurement.date), func.max(Measurement.date), func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    session.close()

    # Create a dictionary from the row data and append to a list 
    key_list = ['start date', 'end date', 'min temp', 'avg temp', 'max temp']
    temp_data = query_to_dictlist(key_list, result_set)
    
    return jsonify(temp_data)


##################################################
# Main Function,  Start the application
##################################################
if __name__ == '__main__':
    app.run(debug=True)
