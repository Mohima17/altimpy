"""
Module with functions to form and process time series. 

"""
# Fernando Paolo <fpaolo@ucsd.edu>
# August 6, 2013 

import numpy as np
from altimpy.const import *
from altimpy.util import *

#----------------------------------------------------------------
# Backscatter corrections
#----------------------------------------------------------------

def backscatter_corr(H, G, diff=False, robust=False): 
    """Apply the backscatter correction to an elevation-change time series.

    It uses constant correlation and sensitivity (transfer function).

    Implements the correction using a time series of dAGC formed exactly as the
    dh time series, following: Zwally, et al. (2005); Yi, et al. (2011):
        
        H_cor(t) = H(t) - S * G(t) - H0

    where H(t) = dh(t0,t), G(t) = dAGC(t0,t) and S = dH/dG = const.

    Parameters
    ----------
    H : array-like
        Time series of elevation change (m).
    G : array-like
        Time series of backscatter change, AGC or sigma0 (dB).
    diff : boolean, default False
        If False, derive mix-term sensitivity as dH/dG; if True, derive
        short-term sensitivity using the derivatives (i.e., differenced series)
        dH'/dG'.
    robust : boolean, default False
        Performs linear fit by robust regression (M-estimate), otherwise uses
        Ordinary Least Squares (default).

    Returns
    -------
    H_cor : array-like
        Corrected elevation-change series.
    R : float
        Correlation coeficient.
    S : float
        Sensitivity factor (transfer function).

    Notes
    -----
    S is slope of linear fit to correlation(dG|dG', dH|dH')
    H0 is intercept of linear fit to correlation(dG|dG', dH|dH')

    See also
    --------
    backscatter_corr2, bacscatter_corr3

    """
    # NOTE: WHAT ABOUT ZEROS IN THE MIDDLE OF THE RECORD (W/DIFF)?
    # use only non-null and non-zero entries for correlation
    ind, = np.where((~np.isnan(H)) & (~np.isnan(G)) & (H!=0) & (G!=0))
    H2, G2 = H[ind], G[ind]
    if len(H2) < 2: 
        return [H, np.nan, np.nan]

    if diff:
        if isinstance(H2, pd.Series):
            # pandas diff -> N (w/NaN)
            H2, G2 = H2.diff(), G2.diff()
            H2, G2 = H2[H2.notnull()], G2[G2.notnull()]
        else:
            # numpy diff -> N-1
            H2, G2 = np.diff(H2), np.diff(G2)
    else:
        pass

    # correlation coef
    R = np.corrcoef(G2, H2)[0,1]

    # correlation grad and intercept
    if robust:
        S, H0 = linear_fit_robust(G2, H2, return_coef=True)
    else:
        S, H0 = linear_fit(G2, H2, return_coef=True)

    # a) no correction applied if |R| < 0.2
    # b) fix values outside the range [-0.2, 0.7]
    if np.abs(R) < 0.2:                          
        return [H, R, S]
    elif S < -0.2:
        S = -0.2
    elif S > 0.7:
        S = 0.7

    #G0 = -H0 * (1. / S)
    #H_cor = H - S * (G - G0)
    H_cor = H - S * G - H0 

    return [H_cor, R, S]


def backscatter_corr2(H, G, diff=False, robust=False, npts=9):
    """Apply the backscatter correction to an elevation-change time series.

    It uses time-variable correlation and sensitivity (transfer function).

    Implements the correction using a time series of dAGC formed exactly as the
    dh time series. Calculates correlations and sensitivities on time windows 
    for each point, following khvorostovsky (2011):
        
        H_cor(t) = H(t) - S(t) * G(t) - H0(t)

    where H(t) = dh(t0,t), G(t) = dAGC(t0,t) and S(t) = dH/dG(t).
 
    Parameters
    ----------
    H : array-like
        Time series of elevation change (m).
    G : array-like
        Time series of backscatter change, AGC or sigma0 (dB).
    diff : boolean, default False
        If False, derive mix-term sensitivity as dH/dG; if True, derive
        short-term sensitivity using the derivatives (i.e., differenced series)
        dH'/dG'.
    robust : boolean, default False
        Performs linear fit by robust regression (M-estimate), otherwise uses
        Ordinary Least Squares (default).
    npts : int, optional
        Number of points used for correlation at each time (window size).

    Returns
    -------
    H_cor : array-like
        Corrected elevation-change series.
    RR : array-like
        Correlation coeficient for each point.
    SS : array-like
        Sensitivity factor for each point (transfer function).

    Notes
    -----
    S is slope of linear fit to correlation(dG|dG', dH|dH')
    H0 is intercept of linear fit to correlation(dG|dG', dH|dH')
    RR, SS, HH are time series of the respective parameters.

    See also
    --------
    backscatter_corr, bacscatter_corr3

    """
    if np.alltrue(np.isnan(H)):
        return [H, np.nan, np.nan]

    H = referenced(H, to='first')
    G = referenced(G, to='first')

    N = len(H)
    RR = np.empty(N, 'f8') * np.nan
    SS = np.empty(N, 'f8') * np.nan
    HH = np.empty(N, 'f8') * np.nan
    l = int(npts/2.)

    for k in range(N):
        if k < l or k >= N-l: 
            continue
        # take chunks (time window) every iteration
        H2, G2 = H[k-l:k+l+1], G[k-l:k+l+1]    
        ind, = np.where((~np.isnan(H2)) & (~np.isnan(G2)))
        H2, G2 = H2[ind], G2[ind]
        if diff:
            if isinstance(H2, pd.Series):
                # pandas diff -> N (w/NaN)
                H2, G2 = H2.diff(), G2.diff()
                H2, G2 = H2[H2.notnull()], G2[G2.notnull()]
            else:
                # numpy diff -> N-1
                H2, G2 = np.diff(H2), np.diff(G2)
        else:
            pass

        # correlation coef
        R = np.corrcoef(G2, H2)[0,1]

        # correlation grad and intercept
        if robust:
            S, H0 = linear_fit_robust(G2, H2, return_coef=True)
        else:
            S, H0 = linear_fit(G2, H2, return_coef=True)

        RR[k] = R
        SS[k] = S
        HH[k] = H0 

    # fill both ends
    RR[:l] = RR[l]
    SS[:l] = SS[l]
    HH[:l] = HH[l]
    RR[N-l:] = RR[N-l-1]
    SS[N-l:] = SS[N-l-1]
    HH[N-l:] = HH[N-l-1]

    # a) no correction applied if |R| < 0.2
    # b) fix values outside the range [-0.2, 0.7]
    ii, = np.where(np.abs(RR) < 0.2)
    SS[ii] = 0.0
    HH[ii] = 0.0
    SS[SS<-0.2] = -0.2
    SS[SS>0.7] = 0.7

    # fill with NaN when no data in dh TS
    jj, = np.where(np.isnan(H))
    RR[jj] = np.nan
    SS[jj] = np.nan
    HH[jj] = np.nan

    H_cor = H - SS * G - HH
    H_cor = referenced(H_cor, to='first')

    return [H_cor, RR, SS]


def backscatter_corr3(H, G, t, intervals, diff=False, robust=False):
    """Apply the backscatter correction to an elevation-change time series.

    It uses interval-variable correlation and sensitivity (transfer function).

    Implements the correction using a time series of dAGC formed exactly as the
    dh time series. Calculates correlations and sensitivities on given time
    intervals:

        dh_cor(t) = dh(t) - s(intv) * dg(t) - h0(intv)

    where dh(t) = dh(t0,t), dg(t) = dAGC(t0,t) and s(intv) = dh/dg[intv].
 
    Parameters
    ----------
    H : array-like
        Time series of elevation change (m).
    G : array-like
        Time series of backscatter change, AGC or sigma0 (dB).
    t : datetime
        Times in datetime objects.
    intervals : list 
        List with datetime tuples defining the time intervals: [(dt1,dt2), 
        (dt2,dt3), ...].
    diff : boolean, default False
        If False, derive mix-term sensitivity as dH/dG; if True, derive
        short-term sensitivity using the derivatives (i.e., differenced series)
        dH'/dG'.
    robust : boolean, default False
        Performs linear fit by robust regression (M-estimate), otherwise uses
        Ordinary Least Squares (default).

    Returns
    -------
    H_cor : array-like
        Corrected elevation-change series.
    RR : array-like
        Correlation coeficient for each point.
    SS : array-like
        Sensitivity factor for each point (transfer function).

    Notes
    -----
    S is slope of linear fit to correlation(dG|dG', dH|dH')
    H0 is intercept of linear fit to correlation(dG|dG', dH|dH')
    RR, SS, HH are time series of the respective parameters.

    See also
    --------
    backscatter_corr, backscatter_corr2

    """
    if np.alltrue(np.isnan(H)):
        return [H, np.nan, np.nan]

    H = referenced(H, to='first')
    G = referenced(G, to='first')

    N = len(H)
    RR = np.empty(N, 'f8') * np.nan
    SS = np.empty(N, 'f8') * np.nan
    HH = np.empty(N, 'f8') * np.nan

    # take chunks (time intervals) at every iteration
    for tt in intervals:
        kk, = np.where((t >= tt[0]) & (t < tt[1]))
        H2, G2 = H[kk], G[kk]
        ind, = np.where((~np.isnan(H2)) & (~np.isnan(G2)))
        H2, G2 = H2[ind], G2[ind]
        if diff:
            if isinstance(H2, pd.Series):
                # pandas diff -> N (w/NaN)
                H2, G2 = H2.diff(), G2.diff()
                H2, G2 = H2[H2.notnull()], G2[G2.notnull()]
            else:
                # numpy diff -> N-1
                H2, G2 = np.diff(H2), np.diff(G2)
        else:
            pass

        # correlation coef
        R = np.corrcoef(G2, H2)[0,1]

        # correlation grad and intercept
        if robust:
            S, H0 = linear_fit_robust(G2, H2, return_coef=True)
        else:
            S, H0 = linear_fit(G2, H2, return_coef=True)

        RR[kk] = R
        SS[kk] = S
        HH[kk] = H0 

    # a) no correction applied if |R| < 0.2
    # b) fix values outside the range [-0.2, 0.7]
    ii, = np.where(np.abs(RR) < 0.2)
    SS[ii] = 0.0
    HH[ii] = 0.0
    SS[SS<-0.2] = -0.2
    SS[SS>0.7] = 0.7

    # fill with NaN when no data in dh TS
    jj, = np.where(np.isnan(H))
    RR[jj] = np.nan
    SS[jj] = np.nan
    HH[jj] = np.nan

    # apply correction only if increase is not greater than p%
    H_cor = H - SS * G - HH
    #H_cor = limit_correction(H, H_cor, max_increase=2.)
    H_cor = referenced(H_cor, to='first')

    return [H_cor, RR, SS]

#----------------------------------------------------------------
# Other functionalities
#----------------------------------------------------------------

def limit_correction(ts, ts_cor, max_increase=2.):
    """Limit the magnitude of the correction."""
    i = (ts_cor / ts) > max_increase
    ts_cor[i] = ts[i]
    return ts_cor


def get_area_cells(grid, x, y):
    """Calculates the area of each grid-cell.

    Parameters
    ----------
    grid : 2d-array
        A rectangular grid.
    x, y : 1d-arrays
        The coordinates of the cells or nodes (edges). If x and y are
        of the same lengh as grid dimensions, then cell-centered 
        coordinates are assumed, otherwise edges are assumed.

    Returns
    -------
    out : 2d-array
        Same shape as 'grid' with the values of the area on each cell.

    """
    ny, nx = grid.shape
    # cells -> nodes
    if len(x) == nx and len(y) == ny:  
        dx, dy = x[1] - x[0], y[1] - y[0]
        x -= dx/2.
        y -= dy/2.
        x = np.append(x, x[-1]+dx)
        y = np.append(y, y[-1]+dy)
    C = EARTH_RADIUS**2 * D2R  # deg -> rad
    A = np.empty_like(grid)
    for i in xrange(ny):
        for j in xrange(nx):
            lat1, lat2 = y[i] * D2R, y[i+1] * D2R
            lon1, lon2 = x[j] * D2R, x[j+1] * D2R
            A[i,j] = C * np.abs(np.sin(lat1)-np.sin(lat2)) * np.abs(lon1-lon2)
    return A


def area_weighted_mean(X, A):
    """Compute the area-weighted-average time series from a 3d array.
    
    For each value in the average time series also returns the fraction
    of area covered by each average.

    Parameters
    ----------
    X : 3d-array 
        Array containing one time series per grid-cell, where the
        first dimension (i) is the time, and the second and thrid 
        dimensions (j and k) are the spatial coordinates (x,y).
    A : 2d-array
        A grid containing the area of each grid-cell on X, i.e.,
        the spatial coordinates.

    Returns
    -------
    ts : 1d-array
        The average time series weighted by each grid-cell area.
    ar : 1d-array
        The fraction of area covered by each average.

    Notes
    -----
    This function uses numpy 'masked arrays'.

    See also
    --------
    get_area_cells

    """
    nt, _, _ = X.shape
    X = np.ma.masked_invalid(X)
    total_area = float(X.sum(axis=0).count())
    ts = np.zeros(nt, 'f8')  # container for output avrg time series
    ar = np.zeros(nt, 'f8')  # container for fraction of area covered
    for k in range(nt):      # weight-average each 2d time step
        G = X[k,...]
        W = A.copy()
        W[np.isnan(G)] = 0
        s = W.sum()
        if s != 0:
            W /= s           # normalize such that sum(W) == 1
        else:
            W[:] = 0 
        ts[k] = np.sum(W*G)  # area-weighted average per time step
        ar[k] =  G.count() / total_area
    return [ts, ar]