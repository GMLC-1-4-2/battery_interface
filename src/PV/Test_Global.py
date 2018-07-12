# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 16:06:07 2018

@author: rmahmud
"""

class Derivative(object):
    def __init__(self,f,h=1e-5):
        self.f=f
        self.h=float(h)
        
    def __call__(self,x):
        f,h=self.f,self.h
        return (f(x+h)-f(x))/h
    
class V(object):
    def __init__(self,beta,mu0,n,R):
        self.beta,self.mu0,self.n,self.R=beta,mu0,n,R
        
    def value(self,r):
        beta,mu0,n,R=self.beta,self.mu0,self.n,self.R
        v=(beta/(2.0*mu0))**(1/n)*(n/(n+1))*\
            (R**(1+1/n)-r**(1+1/n))
        return v
    
class Y2(object):
    def value(self,t,v0=None):
        if v0 is not None:
            self.v0=v0
        if not hasattr(self,'v0'):
            print('you can not call value(t)'\
                  ' without first calling value(t,v) to set v0')
        g=9.81
        return self.v0*t-0.5*g*t**2
    def __call__(self,t):
        g=9.81
        return self.v0*t-0.5*g*t**2
    
    
def value(self,t):
    return self['v0']*t-0.5*self['g']*t**2

def formula(self):
    print('v0*t-0.5*g*t**2; v0 = %g' %self['v0'])    
    
def generate_y(v0):
    #v0=5
    g=9.8
    def y(t):
        return v0*t-0.5*g*t**2
    return y

def generate():
    return [lambda t: (v0,t) for v0 in [0,1,2,10]]

class Account(object):
    def __init__(self,name,account_number,initial_amount):
        self.name=name
        self.no=account_number
        self.balance=initial_amount
        
    def deposit(self,amount):
        self.balance+=amount
        
    def withdraw(self,amount):
        self.balance-=amount
        
    def dumb(self):
        s='%s, %s, balance: %s' %(self.name, self.no,self.balance)
        print(s)
        
class Person(object):
    def __init__(self,name,mobile_phone=None,office_phone=None,
                 private_phone=None,email=None):
        self.name=name
        self.mobile=mobile_phone
        self.office=office_phone
        self.private=private_phone
        self.email=email
        
    def add_mobile_phone(self,number):
        self.mobile=number
        
    def add_office_phone(self,number):
        self.office=number
        
    def add_private_phone(self,number):
        self.private=number
        
    def add_email(self,address):
        self.email=address
        
    def dump(self):
        s=self.name+'\n'
        if self.mobile is not None:
            s+='mobile phone:    %s\n' %self.mobile
        if self.office is not None:
            s+='office phone:    %s\n' %self.office
        if self.private is not None:
            s+='private phone:    %s\n' %self.private
        if self.email is not None:
            s+='email address:    %s\n' %self.email
        print(s)
        
class Circle(object):
    
    def __init__(self,x0,y0,R):
        self.x0=x0
        self.y0=y0
        self.R=R
        
    def area(self):
        pi=3.14
        return pi*self.R**2
    def circumference(self):
        from math import pi
        return 2*pi*self.R
    
class Derivative_sympy(object):
    def __init__(self,f):
        from sympy import Symbol, diff, lambdify
        x=Symbol('x')
        sympy_f=f(x)
        sympy_dfdx=diff(sympy_f,x)
        self.__call__=lambdify([x],sympy_dfdx)
        
def test_Derivative_sympy():
    def g(t):
        return t**3
    
    dg=Derivative_sympy(g)
    t=2
    exact=3*t**2
    computed=dg(t)
    tol=1e-14
    assert abs(exact-computed)<tol
    
    def h(y):
        from math import exp, sin
        return exp(-y)*sin(2*y)
    from sympy import exp, sin
    dh=Derivative_sympy(h)
    from math import cos, pi
    y=pi
    exact=-exp(-y)*sin(2*y)+exp(-y)*2*cos(2*y)
    computed=dh(y)
    assert abs(exact-computed)<tol
    
def trapezoidal(f,a,x,n):
    h=(x-a)/float(n)
    I=0.5*f(a)
    for i in range(1,n):
        I+=f(a+i*h)
    I+=0.5*f(x)
    I*=h
    return I

class Integral(object):
    def __init__(self,f,a,n=100):
        self.f,self.a,self.n=f,a,n
        
    def __call__(self,x):
        return trapezoidal(self.f,self.a,x,self.n)
    
class PhoneBook(object):
    def __init__(self):
        self.contacts={}
        
    def add(self,name,mobile=None,office=None,
            private=None, email=None):
        p=Person(name,mobile,office,private,email)
        self.contacts[name]=p
    def __str__(self):
        s=''
        for p in sorted(self.contacts):
            s+=str(self.contacts[p])+'\n'
        return s
    def __call__(self,name):
        return self.contacts(name)
    
    
class Polynomial(object):
    def __init__(self,coefficinets):
        self.coeff=coefficinets
         
    def __call__(self,x):
        s=0
        for i in range(len(self.coeff)):
            s+=self.coeff[i]*x**i
        return s
    
    def __add__(self,other):
        if len(self.coeff)>len(other.coeff):
            result_coeff=self.coeff[:]
            for i in range(len(other.coeff)):
                result_coeff[i]+=other.coeff[i]
        else:
            result_coeff=other.coeff[:]
            for i in range(len(self.coeff)):
                result_coeff[i]+=self.coeff[i]
        return Polynomial(result_coeff)

    
    def __sub__(self,other):
        if len(self.coeff)>len(other.coeff):
            result_coeff=self.coeff[:]
            for i in range(len(other.coeff)):
                result_coeff[i]+=-1*other.coeff[i]
        else:
            result_coeff=other.coeff[:]
            for i in range(len(self.coeff)):
                result_coeff[i]+=-1*self.coeff[i]
        return Polynomial(result_coeff)

    def __mul__(self,other):
        import numpy
        c=self.coeff
        d=other.coeff
        M=len(c)-1
        N=len(d)-1
        result_coeff=numpy.zeros(N+M+1)
        for i in range(0,M+1):
            for j in range(0,N+1):
                result_coeff[i+j]+=c[i]*d[j]
        return Polynomial(result_coeff)
    
    def differentiate(self):
        for i in range(1,len(self.coeff)):
            self.coeff[i-1]=i*self.coeff[i]
        del self.coeff[-1]
        
    def derivative(self):
        dpdx = Polynomial(self.coeff[:])
        dpdx.differentiate()
        return dpdx
    
    def __str__(self):
        s=''
        for i in range(len(self.coeff)):
            if self.coeff[i]!=0:
                s+=' + %g*x^%d' %(self.coeff[i],i)
            
        s=s.replace('+-','-')
        s=s.replace('x^0','1')
        s=s.replace(' 1*',' ')
        s=s.replace('x^1','x')
        if s[0:3]==' + ':
            s=s[3:]
        if s[0:3]== ' - ':
            s='-'+s[3:]
        return s

class MyClass(object):
    def __init__(self):
        self.data=2
    def __str__(self):
        return 'In __str__: %s' %str(self.data)
    def __repr__(self):
        return 'MyClass()'
    
class Vec2D(object):
    def __init__(self,x,y):
        self.x=x
        self.y=y
    
    def __add__(self,other):
        return Vec2D(self.x+other.x,self.y+other.y)
    
    def __sub__(self,other):
        return Vec2D(self.x-other.x,self.y-other.y)
    
    def __mul__(self,other):
        return (self.x*other.x+self.y*other.y)    
    
    def __abs__(self):
        from math import sqrt
        return sqrt(self.x**2+self.y**2)    
    
    def __eq__(self,other):
        from numpy import allclose
        return allclose(self.x,other.x) and allclose(self.y,other.y)
    
    def __str__(self):
        s='(%g, %g)' %(self.x, self.y)
        return s
        
    def __ne__(self,other):
        return not self.__eq__(other)
    
    def __pow__(self,other):
        raise NotImplementedError('self**power not implemented yet')
            
    def dump(self):
        print(self.__dict__)
        
class A(object):
    def __init__(self,value):
        self.v=value
        
    def dump(self):
        print(self.__dict__)
        
from math import sin, cos, exp, pi
import numpy as np
x=np.linspace(0,2,201)
r=np.zeros(len(x))

for i in range(len(x)):
    r[i]=sin(pi*x[i])*cos(x[i])*exp(-x[i])**2+2+x[i]**2
    
from numpy import sin, cos, exp, pi
    
rr=sin(pi*x)*cos(x)*exp(-x**2)+2+x**2
        
        
from numpy import exp, linspace
from matplotlib.pyplot import *

def f(t):
    return t**2*exp(-t**2)

t=linspace(0,3,51)
y=f(t)

#plot(t,y)
#show()


    

    

class Parabola(object):
    def __init__(self,c0,c1,c2):
        self.c0=c0
        self.c1=c1
        self.c2=c2
        
    def __call__(self,x):
        return self.c0+self.c1*x+self.c2**2
        
    def table(self,L,R,n):
        s=''
        import numpy as np
        for x in np.linspace(L,R,n):
            y=self(x)
            s+='%12g %12g \n' %(x,y)
        return s
    
class Line(Parabola):
    def __init__(self,c0,c1):
        Parabola.__init__(self,c0,c1,0)
        
class FuncWithDerivatives(object):
    def __init__(self,h=1.0e05,a=None,b=None):
        self.h=h
        self.a=a
        self.b=b
        
    def __call__(self,x):
        raise NotImplementedError\
        ('__cal__ missing in class %s' %self.__class__.__name__)
        
    def df(self,x):
        h=self.h
        return ((self(x+h)-self(x-h))/2.0*h)       
    
    def ddf(self,x):
        h=self.h
        return ((self(x+h)-2*self(x)+self(x-h))/(2.0*float(h)))
    
class MyComplecatedClass(FuncWithDerivatives):
    def __init__(self,p,q,r,h=1.0e-5):
        FuncWithDerivatives.__init__(self,h)
        self.p,self.q,self.r=p,q,r
    
    def __call__(self,x):
        from numpy import log, tanh, cos
        return log(abs(self.p*tanh(self.q*x*cos(self.r*x))))
    
    
import csv    
import numpy as np
Year_Target=2017
Day_Target = 31
Month_Target=12

File_Name='467381_39.73_-105.14_2015.csv'


with open(File_Name, newline='') as csvfile:
    read_csv = csv.reader(csvfile, delimiter=' ', quotechar='|')
    rows_in_csv=[]
    for row in read_csv:
        rows_in_csv+=row
        
rows_in_csv=rows_in_csv[82:]
Year=[]
Month=[]
Day=[]
Hour=[]
Minute=[]
DNI=[]
Temp=[]
Number_of_Entries=len(rows_in_csv)
for i in range(Number_of_Entries):
    temp_row=rows_in_csv[i]
    Year.append(int(temp_row[0:temp_row.find(',')]))
    temp_row=temp_row[temp_row.find(',')+1:]
    Month.append(int(temp_row[0:temp_row.find(',')]))
    temp_row=temp_row[temp_row.find(',')+1:]
    Day.append(int(temp_row[0:temp_row.find(',')]))
    temp_row=temp_row[temp_row.find(',')+1:]
    Hour.append(int(temp_row[0:temp_row.find(',')]))
    temp_row=temp_row[temp_row.find(',')+1:]
    Minute.append(int(temp_row[0:temp_row.find(',')]))
    temp_row=temp_row[temp_row.find(',')+1:]
    DNI.append(float(temp_row[0:temp_row.find(',')]))
    temp_row=temp_row[temp_row.find(',')+1:] 
    Temp.append(float(temp_row[0:temp_row.find(',')]))
    
    

np_array_Month = np.array(Month)  
np_array_Day=np.array(Day) 
#%% 
item_index_Month = np.where(np_array_Month==Month_Target)
item_index_Month=np.array(item_index_Month)
Month_Search_Low_Index=item_index_Month[0,0]
if Month_Target<12:
    item_index_Month = np.where(np_array_Month==Month_Target)
    item_index_Month=np.array(item_index_Month)
    Month_Search_Low_Index=item_index_Month[0,0]
    
    item_index_Month = np.where(np_array_Month==Month_Target+1)
    item_index_Month=np.array(item_index_Month)
    Month_Search_High_Index=item_index_Month[0,0]-1
else:
    item_index_Month = np.where(np_array_Month==Month_Target)
    item_index_Month=np.array(item_index_Month)
    Month_Search_Low_Index=item_index_Month[0,0]
    Month_Search_High_Index=len(Month)
    
Day=Day[Month_Search_Low_Index:Month_Search_High_Index]
Hour=Hour[Month_Search_Low_Index:Month_Search_High_Index]
Minute=Minute[Month_Search_Low_Index:Month_Search_High_Index]
DNI=DNI[Month_Search_Low_Index:Month_Search_High_Index]
Temp=Temp[Month_Search_Low_Index:Month_Search_High_Index]

#%%
item_index_Day = np.where(np_array_Day==Day_Target)
item_index_Day=np.array(item_index_Day)
Day_Search_Low_Index=item_index_Day[0,0]
import calendar
if Day_Target<calendar.monthrange(Year_Target,Month_Target)[1]:
 
    item_index_Day = np.where(np_array_Day==Day_Target+1)
    item_index_Day=np.array(item_index_Day)
    Day_Search_High_Index=item_index_Day[0,0]-1
else:
    Day_Search_High_Index=len(Day)
    
Day=Day[Day_Search_Low_Index:Day_Search_High_Index]
Hour=Hour[Day_Search_Low_Index:Day_Search_High_Index]
Minute=Minute[Day_Search_Low_Index:Day_Search_High_Index]
DNI=DNI[Day_Search_Low_Index:Day_Search_High_Index]
Temp=Temp[Day_Search_Low_Index:Day_Search_High_Index]

Time_=[]
for i in range(len(Hour)):
    Time_.append(Hour[i]+Minute[i]/60)
#%%plot


import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()


ax1.plot(Time_,DNI, 'b-')
ax1.set_xlabel('time (Hr)')
# Make the y-axis label, ticks and tick labels match the line color.
ax1.set_ylabel('W/m2', color='b')
ax1.tick_params('y', colors='b')
ax1.legend(['Irradiance'])
s='Daye: %g/%g/%g' %(Month_Target,Day_Target,Year_Target)


ax2 = ax1.twinx()

ax2.plot(Time_,Temp, 'r.')
ax2.set_ylabel('$^0$C', color='r')
ax2.tick_params('y', colors='r')
ax2.legend(['Temperature'])
ax2.text(.02, np.max(Temp)-2, s, style='italic',
        bbox={'facecolor':'red', 'alpha':0.5, 'pad':1})

fig.tight_layout()
plt.show()


#%%


import collections

def get_iterable(x):
    if isinstance(x, collections.Iterable):
        return x
    else:
        return (x,)
    
x=1
x=get_iterable(x)

for x1 in x:
    print(x1)
    
from BEq_PV import BEq_PV
a=BEq_PV
Fleet_PV=a.service_response([135,2e4],[1e3],False)
print('P_grid = '+repr(Fleet_PV.P_grid))
print('Q_grid = '+repr(Fleet_PV.Q_grid))
print('P_service = '+repr(Fleet_PV.P_service))
print('Q_service = '+repr(Fleet_PV.Q_service))
print('E_t0 = '+repr(Fleet_PV.E_t0))
print('c = '+repr(Fleet_PV.c))
print('P_output = '+repr(Fleet_PV.P_output))
print('Q_output = '+repr(Fleet_PV.Q_output))
print('P_grid_max = '+repr(Fleet_PV.P_grid_max))
print('Q_grid_max = '+repr(Fleet_PV.Q_grid_max))
print('P_grid_min = '+repr(Fleet_PV.P_grid_min))
print('Q_grid_min = '+repr(Fleet_PV.Q_grid_min))
print('P_service_max = '+repr(Fleet_PV.P_service_max))
print('Q_service_max = '+repr(Fleet_PV.Q_service_max))
print('P_service_min = '+repr(Fleet_PV.P_service_min))
print('Q_service_min = '+repr(Fleet_PV.Q_service_min))
print('del_t_hold = '+repr(Fleet_PV.del_t_hold))
print('t_restore = '+repr(Fleet_PV.t_restore))
print('SP = '+repr(Fleet_PV.SP))
print('N_reqprint = '+repr(Fleet_PV.N_req))

#%%

from datetime import datetime, timedelta
ts=datetime.utcnow()
sim_step=timedelta(hours=1)
import Weather
import Devices_
import BEq_PV
import PV_Inverter_Data
import Aggregator_Command
Command_to_Device=Aggregator_Command.Aggregator_Command(100, 0,10000)
def Grid_Param():
    f = 60.1
    V = 1.1
    return f, V
[P_grid,Q_grid,P_service,Q_service,E_t0,c,P_output,Q_output,P_grid_max,Q_grid_max,\
         P_grid_min,Q_grid_min,P_service_max,Q_service_max,P_service_min,Q_service_min,del_t_hold,\
         t_restore,SP,N_req]=Devices_.Device_PV(ts,sim_step,Weather,Grid_Param,Command_to_Device,False)

#%%
from datetime import datetime, timedelta
from fleet_interface import FleetInterface
a=FleetInterface()
b=a.forecast([100,200])
b.P_injected
b.P_injected_max
b.Q_injected
b.Q_injected_max
 
 
 
