# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov
"""
from _load import *
simplefilter('ignore', RankWarning)
colorama.init()


def ne_calc(filename, e_size, ne=None):
    """
    :param filename: Time-stamped power curve input data as CSV
    :param e_size: Size of a single Electrolyzer in kW
    :param ne: User input for number of Electrolyzers
    :return: Optimum number of Electrolyzers
    """
    df = read_csv(filename, header=None, parse_dates=[0], names=['datetime', 'Pval'])
    opt_ne = int(round(trapz(df['Pval'])/len(df)/e_size))
    if int(ne) != opt_ne:
        cprint("Number of Electrolyzers does not fit the power curve:\t\t[%d]" % int(ne), 'red')
        cprint("Optimum Electrolyzers used for this simulation run:\t\t[%d]" % opt_ne, 'cyan')
        return opt_ne
    return ne


def fit_pdat(filename, time_interval=None):
    """
    Read demand profile and check if timestamp interval is at least in seconds.
    Execute only if freq does not match: milli, micro, or nano
    :param filename: Time-stamped power curve input data as CSV
    :param time_interval: Specify the data time interval in seconds
    :return p: Curve-fit results using Least square curve-fitting method
    """
    if time_interval is None:
        try:
            df = read_csv(filename, header=None, parse_dates=[0], index_col=0, nrows=10)
            interval = df.index.inferred_freq
        except (AttributeError, TypeError):
            raise Exception("\tUnable to infer time interval from input data\n"
                            "\tPlease specify the time_interval parameter in seconds!!\n")
        if any(i in interval for i in ('L', 'ms', 'U', 'us', 'N')) is False:
            cprint("Power data time-interval is at least in seconds:\t\t[OKAY]", 'green')
            df = read_csv(filename, header=None, parse_dates=[0], names=['datetime', 'Pval'])
            df['sec'] = df['datetime'].sub(df['datetime'].iloc[0]).dt.total_seconds()
        else:
            raise Exception("\tTime-series data should be at least in seconds\n"
                            "\te.g.:\n"
                            "\t\t2019-01-21 00:00:00  646.969697\n"
                            "\t\t2019-01-21 00:05:00  642.818182\n"
                            "\t\t...................  ..........\n"
                            "\t\tYYYY-MM-DD HH:MM:SS  Value\n")
    else:
        df = read_csv(filename, header=None, names=['Pval'])
        df['sec'] = [i for i in range(0, len(df)*time_interval, time_interval)]

    # Least-square curve-fitting
    return polyfit(df['sec'].values, df['Pval'].values, 21), int(df['sec'].iloc[-1])


def vi_calc(x, Pri, Nc, V_rev, T, r1, r2, s1, s2, s3, t1, t2, t3, A):
    fa = list([x[0] - V_rev - (r1+r2*T)*x[1]/A - (s1+s2*T+s3*T**2)*log10((t1+t2/T+t3/T**2)*x[1]/A+1)])
    fa.append((Nc*x[0])*x[1]-Pri)
    return fa


def static_plots(**kwargs):
    plots = int(len(kwargs))
    nplots = int(2*plots)
    fig1 = figure(figsize=(20, 8))
    fig1.subplots_adjust(wspace=0.4)
    fig1.subplots_adjust(hspace=4.5)
    res_plt = {}
    for i, (k, v) in enumerate(kwargs.items()):
        if i % 2 == 0:
            res_plt[str(i)] = subplot2grid((nplots, plots), (i, 0), rowspan=2, colspan=3)
        else:
            res_plt[str(i)] = subplot2grid((nplots, plots), (i-1, 3), rowspan=2, colspan=3)

        res_plt[str(i)].set_title(k)
        res_plt[str(i)].plot(v[0], '-.r')
        res_plt[str(i)].set_ylabel(v[1])
        res_plt[str(i)].grid()
    show()
    fig1.savefig("ey_result2.png", bbox_inches='tight')
