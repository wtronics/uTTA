import datetime

import numpy as np
import pandas as pd
from astral.sun import sun
from astral import LocationInfo
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def sun_year (dates, location):
    t_sunrise = []
    t_sunset = []
    t_noon = []

    for y_date in dates:
        try:
            s = sun(location, date=y_date)
            t_noon.append(s["noon"].hour * 3600 + s["noon"].minute * 60 + s["noon"].second)
            t_sunrise.append(s["sunrise"].hour * 3600 + s["sunrise"].minute * 60 + s["sunrise"].second)
            t_sunset.append(s["sunset"].hour * 3600 + s["sunset"].minute * 60 + s["sunset"].second)
        except:
            t_noon.append(86400/2)
            t_sunrise.append(0)
            t_sunset.append(86400)

    return t_sunrise, t_sunset, t_noon


def add_location(dates, location, diag):
    s_rise, s_set, noon = sun_year(dates, location.observer)

    diag[0].plot(dates, np.divide(s_rise, 3600), label=location.name + " Sun Rise")
    diag[0].plot(dates, np.divide(s_set, 3600), label=location.name + " Sun Set")
    diag[0].plot(dates, np.divide(noon, 3600), label=location.name + " Noon")

    light_hours = (np.subtract(s_set, s_rise)) / 3600
    today = pd.to_datetime("today").normalize()
    # print(np.argwhere(dates == today)[0][0])

    shortest_sun_min = np.min(light_hours)*60
    todays_sun_min = light_hours[np.argwhere(dates == today)[0][0]]*60
    todays_grad_min = np.diff(light_hours)[np.argwhere(dates == today)[0][0]]*60
    daytime_increase_min = (todays_sun_min - shortest_sun_min)

    print("Shortest Day is {thour:.0f} hours and {tmin:.3f} minutes".format(thour=shortest_sun_min/60, tmin=shortest_sun_min % 60))
    print("Today is {thour:.0f} hours and {tmin:.3f} minutes".format(thour=todays_sun_min/60, tmin=todays_sun_min % 60))

    print("Today is already {tmin:.0f} minutes and {tsec:.2f} seconds longer than on 21.12.".format(tmin=daytime_increase_min,
                                                                                                    tsec=(daytime_increase_min*60000) % 1000))
    print("Todays gradient is {tgradmin:.0f} minutes and {tgradsec:.0f} seconds".format(tgradmin=todays_grad_min, tgradsec=(todays_grad_min * 60) % 60))

    diag[1].plot(dates, light_hours, label=location.name + " Daylight hours")
    diag[2].plot(dates[1:], np.diff(light_hours) * 60, label=location.name)

    dt_max = np.max(np.diff(light_hours) * 60)
    dt_max_date = np.argmax(np.diff(light_hours) * 60)
    dt_min = np.min(np.diff(light_hours) * 60)
    dt_min_date = np.argmin(np.diff(light_hours) * 60)
    print("Highest positive daytime gradient {dtMax:.2f} minutes on {dtMaxDate}, highest decrease {dtMin:.2f} minutes on {dtMinDate}".format(dtMax=dt_max,
                                                                                                                     dtMaxDate=dates[dt_max_date],
                                                                                                                     dtMin=dt_min,
                                                                                                                     dtMinDate=dates[dt_min_date]))


fig, axs = plt.subplots(nrows=3, ncols=1, layout="constrained")
axs[0].set_title("Sun rise and sun set through the year")
axs[0].set_ylabel('Time / [h]')
axs[0].set_xlabel('Date')

axs[1].set_title("Light hours per day")
axs[1].set_ylabel('Time / [h]')
axs[1].set_xlabel('Date')

axs[2].set_title("Light hours per day")
axs[2].set_ylabel('Time / [min]')
axs[2].set_ylim(-10, 10)
axs[2].set_xlabel('Date')

YearDates = pd.date_range(start=pd.to_datetime("31/12/2024", dayfirst=True),
                          end=pd.to_datetime("31/12/2025", dayfirst=True))

city = LocationInfo("Buchbrunn", "Germany", "Europe/Berlin", 49.750000, 10.136000)
add_location(YearDates, city, axs)

#city = LocationInfo("Idre", "Sweden", "Europe/Berlin", 61.856667, 12.716667)
#add_location(YearDates, city, axs)

myFmt = mdates.DateFormatter('%d.%m')

axs[0].legend(loc='upper right')
# axs[0].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
axs[0].xaxis.set_major_locator(mdates.WeekdayLocator(interval=7))
axs[0].xaxis.set_major_formatter(myFmt)
axs[0].grid(which='both')

axs[1].legend()
axs[1].xaxis.set_major_locator(mdates.WeekdayLocator(interval=7))
axs[1].xaxis.set_major_formatter(myFmt)
axs[1].grid(which='both')

axs[2].legend()
axs[2].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
axs[2].xaxis.set_major_formatter(myFmt)
axs[2].grid(which='both')
plt.show()
