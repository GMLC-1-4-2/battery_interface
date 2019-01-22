# PEM Electrolyzer model v0.1.2
"""
Includes Compressor model and energy efficiency based on input Power curves

"""
from math import log10, exp
from pandas import read_csv
from numpy import polyfit, zeros, RankWarning
from matplotlib.pyplot import plot, show
from warnings import simplefilter
simplefilter('ignore', RankWarning)

# Model parameters to be included in config.ini
T = 25.0                                            # (°C) Electrolyzer operating temperature
Pe = 101000                                         # (pa)
Pe_out = 50000000                                   # (Pa) state of maximum charge in the tank
eta_c = 0.8                                         # compressor's isentropic efficiency
A = 0.25                                            # (m^2) area of electrode
Nc = 12.0                                           # Number of cells connected in series
F = 96485.34                                        # (C/mol) Faraday's constant
ne = 2.0
charge_lvl_min = 20                                 # (%) minimum state of charge in the hydrogen tank
charge_lvl_max = 95                                 # (%) maximum state of charge in the hydrogen tank
soc_lvl_init = 19                                   # (%) initial state of charge
DG_25 = 237000.0
DG_80 = 228480.0
DH = 286000.0
R = 8.31445                                         # (J/mol-K) universal constant of gases
Ne = 50                                             # Number of Electrolyzers
V_tank = 0.3                                         # (m^3) volume of the tank
r1 = 7.331e-5                                       # (ohm m^2) ri parameter for ohmic resistance of electrolyte
r2 = -1.107e-7                                      # (ohm m2 °C^-1)
r3 = 0
s1 = 1.586e-1                                       # (V) si and ti parameters for over-voltage on electrodes
s2 = 1.378e-3                                       # (V°C^-1)
s3 = -1.606e-5                                      # V °C^-2)
t1 = 1.599e-2
t2 = -1.302
t3 = 4.213e2
I_initial = 0
I_final = 870
I_step = 1
V_fin = 2.2
V_step = 1e-3
a1 = 0.995                                          # 99.5 %
a2 = -9.5788                                        # (m ^ 2 * A ^ -1)
a3 = -0.0555                                        # (m ^ 2 * A ^ -1 *°C)
a4 = 0
a5 = 1502.7083                                      # (m ^ 4 * A ^ -1)
a6 = -70.8005                                       # (m ^ 4 * A ^ -1 *°C-1)
a7 = 0
gamma = 1.41
cpH2 = 14.31                                        # kj / kg - K
power_data = 'pdata.csv'                            # Power curve time-series CSV data

# Compute starting parameters for model init
min_charge = charge_lvl_min*1e-2*Pe_out             # min. state of charge in the hydrogen tank
max_charge = charge_lvl_max*1e-2*Pe_out             # max. state of charge in the hydrogen tank
# soc_i VALUE NOT BEING USED!!
soc_i = soc_lvl_init*1e-2*Pe_out                    # SOC initial
n_i = soc_i*0.3/8.3145/(25+273.15)

DG = DG_25-(T-25)/55*(DG_25-DG_80)
V_rev = DG/ne/F
V_init = round(V_rev, 2)
Vtn = DH/ne/F                                       # thermo-neutral voltage

nn = (I_final-I_initial)/I_step
I = [i for i in range(0, I_final + 1, I_step)]

# Compute V and Id
V_graph = [V_rev + (r1+r2*T)*I[i]/A+(s1+s2*T+s3*T**2)*log10((t1+t2/T+t3/T**2)*I[i]/A+1) for i in range(int(nn) + 1)]
Id = [i/2500 for i in I]

# Read demand profile and check if timestamp interval is at least in seconds
# Execute only if freq does not match: milli, micro, or nano
df = read_csv(power_data, header=None, parse_dates=[0], index_col=0)
if any(i in df.index.inferred_freq for i in ('L', 'ms', 'U', 'us', 'N')) is False:
    print("Demand data time-interval is at least in seconds:\t\tOKAY")
else:
    raise Exception("\tTime-series data should be at least in seconds\n"
                    "\te.g.:\n"
                    "\t\t2019-01-21 00:00:00  646.969697\n"
                    "\t\t2019-01-21 00:05:00  642.818182\n"
                    "\t\t...................  ..........\n"
                    "\t\tYYYY-MM-DD HH:MM:SS  Value\n")

# Least-square curve-fitting
p_vec = df.values
t_vec = [i for i in range(len(p_vec))]
p = polyfit(t_vec, p_vec, 21)


Pl, Pr, P_tot, Ir, P, V, ne, Qh2_V, Qh2_m,\
    m_dotH2, P_tank, Tout, W_c, soc = [zeros((len(p_vec)-1, 1), dtype=float) for i in range(14)]
moles = zeros((len(p_vec), 1), dtype=float)
moles[0][0] = n_i

for i in range(len(p_vec)-1):
    Pl[i] = 1.1*(-1.66886501583441e-91*(i+1)**21+1.47641487070072e-85*(i+1)**20-6.04737306005779e-80*(i+1)**19 +
    1.5215691572903e-74*(i+1)**18-2.63102213044733e-69*(i+1)**17 +
    3.31408128540438e-64*(i+1)**16-3.14500220264774e-59*(i+1)**15 +
    2.29376348189984e-54*(i+1)**14-1.29999214364872e-49*(i+1)**13 +
    5.75117958605101e-45*(i+1)**12-1.98427144802997e-40*(i+1)**11 +
    5.30725470343592e-36*(i+1)**10-1.08802897081482e-31*(i+1)**9 +
    1.67983622356027e-27*(i+1)**8-1.90337588931417e-23*(i+1)**7 +
    1.52346864091771e-19*(i+1)**6-8.11379421971959e-16*(i+1)**5 +
    2.58376941897956e-12*(i+1)**4-3.77390895140414e-09*(i+1)**3 -
    1.85238743353635e-07*(i+1)**2-0.00331412861521689*(i+1)+645.405712039294)/10

    Pr[i] = 1e3*Pl[i]/Ne                            # (W) to power one stack of electrolyzer

    mm = round((V_fin - V_init) / V_step)

    co = 0
    while co != 1:
        for j in range(mm):
            Va = round(V_rev, 2) + V_step * (j+1 - 1)
            B = V_rev + (r1+r2*T)*Pr[i]/A/Nc/Va+(s1+s2*T+s3*T**2)*log10((t1+t2/T+t3/T**2)*Pr[i]/A/Nc/Va+1)

            if abs(B - Va) < 0.005:
                co = 1
                V[i] = B

    Ir[i] = Pr[i]/Nc/V[i]

    P[i] = Ne*Nc*V[i]*Ir[i]

    # Compute Faraday Efficiency
    nf = a1 * exp((a2 + a3 * T + a4 * T ** 2) / (Ir[i] / A) + (a5 + a6 * T + a7 * T ** 2) / (Ir[i] / A) ** 2)

    # Energy (or voltaje) efficiency of a cell
    ne[i] = Vtn / V[i]

    # Flow of H2 produced
    Qh2_V[i] = 80.69*Nc*Ir[i]*nf/2/F                                # (Nm^3/h)
    Qh2_m[i] = Ne*Nc*Ir[i]*nf/2/F                                   # (mol/s)
    m_dotH2[i] = Qh2_m[i]*0.001                                     # (kg/s)

    # Compressor model ERROR IN MOLES INDEX ERROR
    P_tank[i] = moles[i]*R*(T+273.15)/V_tank
    Tout[i] = (T+273.15)*(P_tank[i]/Pe)**((gamma-1)/gamma)
    W_c[i] = (m_dotH2[i]/eta_c)*cpH2*(Tout[i]-(T+273.15))           # (kW)
    P_tot[i] = W_c[i]*1000 + P[i]

    # Storage Tank
    # Number of moles in time i in the tank
    moles[i + 1] = moles[i] + Qh2_m[i] * 1
    soc[i] = P_tank[i]

    if soc[i] >= max_charge:
        print('Tank is fully charged!!\n'
              'Charge time:%d sec.' % i)

        soc_i = round(soc[i] / max_charge * 100, 1)
        break

plot(W_c[:i])
show()
plot(P_tank[:i])
show()
plot(Ir[:i])
show()
plot(V[:i])
show()
plot(moles[:i])
show()
plot(m_dotH2[:i]*1000)                                              # (g/s)
show()
plot(P_tot[:i])
show()
plot(P[:i], 'r')
show()
