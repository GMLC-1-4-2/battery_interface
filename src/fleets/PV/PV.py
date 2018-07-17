# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 13:41:32 2018

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""
def PV(G,T):
#PROGRAM STARTS HERE

# PV MODEL calculation 

# The theory used in this program for modeling the PV device is found 
# in many sources in the litterature and is well explained in Chapter 1 of
#"Power Electronics and Control Techniques" by Nicola Femia, Giovanni 
# Petrone, Giovanni Spagnuolo and Massimo Vitelli. 
    
    import PV_Panel_Data
    import math
    import numpy
    import matplotlib.pyplot as plt
    
    [Iscn,Vocn , Imp ,Vmp , Pmax_e ,Kv , Ki ,Ns ]=PV_Panel_Data.data_M2453BB()
    
    Gn = 1000               #Nominal irradiance [W/m^2] @ 25oC
    Tn = 25 + 273.15        #Nominal operating temperature [K]
    
    #Egap = 2.72370016e-19;  % Bandgap do silício amorfo em J (=1.7 eV)
    Egap = 1.8e-19          # Bandgap do silício cristalino em J (=1.124 eV)
    
    ns = Ns # for compatibility
    
    Ipvn = Iscn
    
    #G = 700
    T = T+273
    Ipv = Ipvn * G/Gn * (1 + Ki * (T-Tn))
    
    k = 1.3806503e-23   #%Boltzmann [J/K]
    q = 1.60217646e-19  #%Electron charge [C]
    
    Vt =  k*T /q
    Vtn = k*Tn/q
    
    a = (Kv - Vocn/Tn) / ( ns * Vtn * ( Ki/Ipvn - 3/Tn - Egap/(k*numpy.power(Tn,2) ) ))
    Ion=Ipvn /(math.exp(Vocn/(a*ns*Vtn))-1)
    C = Ion /  (numpy.power(Tn,3) * math.exp (-1*Egap / (k * Tn)))
    Io = C * numpy.power(Tn,3)* math.exp(-Egap/k/T)
    Rs = (a * ns * Vtn * math.log (1-Imp/Ipvn)+Vocn - Vmp)/Imp
    Rp = 9999999999 #% Rp = infinite
    
    # PROGRAM ENDS HERE
    
    
    #%% I-V and P-V CURVES of the calculated model at STC
    
    #% In this part of the program we are solving the I-V equation for several 
    #% (V,I) pairs and ploting the curves using the model previously calculated
    
    #% G =  700;               %Irradiance for evaluating the model 
    #% T =  25 + 273.15;        %Temperature for evaluating the model 
    
    #del V
    #del I
    
    nv = 50 #; % número de pontos da curva
    V=[]
    for x in range(nv):
        V.append(x*Vocn/nv) #V = 0:Vocn/nv:Vocn;  % Voltage vector
        
    I=[]
    g=[]
    glin=[]
    I_=[]
    for x in range(int(len(V))):
        I.append(0)
        g.append([])
        glin.append([])
        I_.append([])
    
    for j in range(int(len(V))):
        #g[j]=Ipv-Io*Ipv-Io*(math.exp((V[j])+I[j]*Rs)/Vt/ns/a)-1)-(V[j]+I[j]*Rs)/Rp-I[j];
        #print(V[j],I[j],end=' ')
        g[j]=(Ipv-Io*Ipv-Io*(math.exp((V[j]+I[j]*Rs)/(Vt*ns*a))-1)-(V[j]+I[j]*Rs)/Rp-I[j])
        while math.fabs(g[j])>.001:
            g[j]=(Ipv-Io*(math.exp((V[j]+I[j]*Rs)/Vt/ns/a)-1)-(V[j]+I[j]*Rs)/Rp-I[j])
            glin[j]=(-Io*Rs/Vt/ns/a*math.exp((V[j]+I[j]*Rs)/Vt/ns/a)-Rs/Rp-1)
            I_[j]=(I[j] - g[j]/glin[j])
            I[j]=I_[j]
          #  print(g[j],glin[j],I_[j],end=' ')
            
    
            
        
    #for j = 1 : size(V,2) %Calculates for all voltage values 
        
     # % Solves g = I - f(I,V) = 0 with Newton-Raphson
      
      #g(j) = Ipv-Io*(exp((V(j)+I(j)*Rs)/Vt/ns/a)-1)-(V(j)+I(j)*Rs)/Rp-I(j);
      
      #while (abs(g(j)) > 0.001)
          
      #g(j) = Ipv-Io*(exp((V(j)+I(j)*Rs)/Vt/ns/a)-1)-(V(j)+I(j)*Rs)/Rp-I(j);
      #glin(j) = -Io*Rs/Vt/ns/a*exp((V(j)+I(j)*Rs)/Vt/ns/a)-Rs/Rp-1;
      #I_(j) = I(j) - g(j)/glin(j);
      #I(j) = I_(j);   
      
      #end  
    
    #end
    for x in range(len(I)):
        if I[x]<0:
            I[x]=0
            
    P=[]
    for x in range(len(V)):
    #    if I[x]<0:
     #       I[x]=0
        P.append(I[x]*V[x])
        
        
        
            
    #I(I<0)=0;
    
    #P=I.*V;
    
    #%% I-V and P-V curves
     
     #% I-V curve
    
     
     #figure(3) 
     #grid on
     #hold on 
     #title('I-V curve');
     #xlabel('V [V]');
     #ylabel('I [A]');
     #xlim([0 max(V)*1.1]);
    #%  ylim([0 max(I)*1.1]);
     
     #plot(V,I,'LineWidth',2,'Color','blue') %
     #hold on
     #plot([0 Vmp Vocn ],[Iscn Imp 0 ],'o','LineWidth',2,'MarkerSize',5,'Color','blue') 
     #text(1,max(I)-.2,[num2str(G) 'W/M^2'])
     
      
     #% P-V curve
     #figure(4) 
     #grid on
     #hold on 
     #title('P-V curve');
     #xlabel('V [V]');
     #ylabel('P [W]');
     #xlim([0 max(V)*1.1]);
    #%  ylim([0 max(V.*I)*1.1]);
       
     #plot(V,V.*I,'LineWidth',2,'Color','blue') %
     
     #plot([0 Vmp Vocn ],[0 Pmax_e 0 ],'o','LineWidth',2,'MarkerSize',5,'Color','blue') 
     #ylim([0 280]) 
    #%  ytick([0 40 120 160 200 240 280])
     
     
    #disp(sprintf('Method 2 - Simplified model without Rp\n '));
    #disp(sprintf('     Rp = %f',Rp));
    #disp(sprintf('     Rs = %f',Rs));
    #disp(sprintf('      a = %f',a));
    #disp(sprintf('      T = %f',T-273.15));
    #disp(sprintf('      G = %f',G));
    #disp(sprintf(' Pmax,e = %f  (experimental)',Pmax_e));
    #disp(sprintf('    Ipv = %f',Ipvn));
    #disp(sprintf('    Isc = %f',Iscn));
    #disp(sprintf('    Ion = %g',Ion));
    #disp(sprintf('\n\n')); 
    
    
    
    Pmpp=numpy.max(P)
    if Pmpp==0:
        Vmpp=Vocn
    else:    
        Vmpp=V[numpy.abs(P-numpy.max(P)).argmin()]
    
    return Pmpp,Vmp
    #fig, ax1 = plt.subplots()
    #ax1.plot(V, I, 'b-',[],[])
    #ax1.set_xlabel('V[V]')
     #Make the y-axis label, ticks and tick labels match the line color.
    #ax1.set_ylabel('I[I]', color='b')
    #ax1.tick_params('y', colors='b')
        #ax2 = ax1.twinx()
    #ax2.plot(V,P, 'r')
    #ax2.set_ylabel('P[W]', color='r')
    #ax2.tick_params('y', colors='r')
    
    #fig.tight_layout()
    #plt.show()
        

    #text(Vmpp,Pmpp+10,[num2str(G) 'W/M^2'])
