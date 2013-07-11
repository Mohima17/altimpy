import datetime as dt
import altimpy as ap

t1 = dt.datetime(   1, 1, 1, 0, 0, 0)
t2 = dt.datetime(   1, 1, 1, 0, 0, 1)
t3 = dt.datetime(   1, 1, 1, 0, 1, 0)
t4 = dt.datetime(   1, 1, 1, 1, 0, 0)
t5 = dt.datetime(2000, 1, 1, 0, 0, 0)
t6 = dt.datetime(2000, 1, 1, 0, 0, 1)
t7 = dt.datetime(2000, 1, 1, 0, 1, 0)
t8 = dt.datetime(2000, 1, 1, 1, 0, 0)

y1 = ap.date2year(t1)
y2 = ap.date2year(t2)
y3 = ap.date2year(t3)
y4 = ap.date2year(t4)
y5 = ap.date2year(t5)
y6 = ap.date2year(t6)
y7 = ap.date2year(t7)
y8 = ap.date2year(t8)

d1 = ap.year2date(y1)
d2 = ap.year2date(y2)
d3 = ap.year2date(y3)
d4 = ap.year2date(y4)
d5 = ap.year2date(y5)
d6 = ap.year2date(y6)
d7 = ap.year2date(y7)
d8 = ap.year2date(y8)

print t1, d1, y1
print t2, d2, y2
print t3, d3, y3
print t4, d4, y4
print t5, d5, y5
print t6, d6, y6
print t7, d7, y7
print t8, d8, y8