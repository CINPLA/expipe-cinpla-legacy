import quantities as pq
import matplotlib.pyplot as plt
import exana.tracking as tr
import numpy as np
from exana.misc.plot import simpleaxis
import math

file_params = {
    'speed_filter': 5 * pq.m / pq.s,
    'pos_fs': 100 * pq.Hz,
    'f_cut': 6 * pq.Hz,
    'spat_binsize': 0.02 * pq.m,
    'spat_smoothing': 0.025,
    'grid_stepsize': 0.1 * pq.m,
    'box_xlen': 1 * pq.m,
    'box_ylen': 1 * pq.m,
    'ang_binsize': 4,
    'ang_n_avg_bin': 4,
    'imgformat': '.png',
    'corr_bin_width': 0.01 * pq.s,
    'corr_limit': 1. * pq.s,
    'isi_binsize': 1 * pq.ms,
    'isi_time_limit': 100 * pq.ms,
}


def make_spatiality_overview(x, y, t, angles, t_angles, sptr, acorr=None,
                             G=None, fig=None, mask_unvisited=False,
                             vmin=0, ang_binsize=2, projection='polar',
                             title=None, rate_map=None, params=None,
                             spike_size=10., origin='upper', cmap='jet'):
    """


    Parameters
    ----------
    x : quantities.Quantity array in m
        1d vector of x positions
    y : quantities.Quantity array in m
        1d vector of y positions
    t : quantities.Quantity array in s
        1d vector of time at x, y positions
    angles : np.ndarray
        head direction angles
    t_angles : np.ndarray
        times corresponding to angles
    acorr : 2d np.ndarray
        autocorrelation map
    G : gridness score
    fig : matplotlib figure
    mask_unvisited : bool
        mask bins which has not been visited

    Returns
    -------
    out : fig
    """
    par = params or file_params
    if acorr is None:
        rate_map = tr.spatial_rate_map(x, y, t, sptr, binsize=par['spat_binsize'],
                                       mask_unvisited=True)
        G, acorr = tr.gridness(rate_map, return_acorr=True,
                               box_xlen=par['box_xlen'],
                               box_ylen=par['box_ylen'])
    ncol, nrow = 2, 2

    if fig is None:
        fig = plt.figure()
    ax1 = fig.add_subplot(nrow, ncol, 1, xlim=[0, 1], ylim=[0, 1], aspect=1)
    ax1.grid(False)
    tr.plot_path(x, y, t, sptr=sptr, ax=ax1, box_xlen=par['box_xlen'],
                 box_ylen=par['box_ylen'], markersize=spike_size,
                 origin=origin)
    ax1.set_title('N spikes {}'.format(len(sptr)))
    ax2 = fig.add_subplot(nrow, ncol, 2, xlim=[0, 1], ylim=[0, 1], aspect=1,
                          yticks=[])
    if rate_map is None:
        tr.plot_ratemap(x, y, t, sptr, binsize=par['spat_binsize'], vmin=vmin,
                     mask_unvisited=mask_unvisited, ax=ax2)
    else:
        ax2.imshow(rate_map, interpolation='none', origin=origin,
                  extent=(0, 1, 0, 1), vmin=vmin, cmap=cmap)
        ax2.set_title('%.2f Hz' % np.nanmax(rate_map))
    ax2.grid(False)
    ax3 = fig.add_subplot(nrow, ncol, 3, xlim=[0, 1], ylim=[0, 1], aspect=1)
    ax3.imshow(acorr, interpolation='none',
               origin=origin, extent=(0, 1, 0, 1))
    ax3.set_title('Gridness %.2f\n' % G)
    simpleaxis(ax3, left=False, bottom=False)
    ax3.set_xticks([])
    ax3.set_yticks([])
    ax3.grid(False)
    ax4 = fig.add_subplot(nrow, ncol, 4, aspect=1, projection=projection)
    ang_bins, rate_in_ang = tr.head_direction_rate(sptr, angles, t_angles,
                                                     binsize=ang_binsize)
    tr.plot_head_direction_rate(sptr, ang_bins, rate_in_ang,
                             projection=projection, ax=ax4)
    mean_ang, mean_vec_len = tr.head_direction_stats(ang_bins, rate_in_ang)
    ax4.set_title(r'$\bar{\theta} = %.2f,\, \bar{r} = %.2f$' % (mean_ang,
             mean_vec_len))
    # ax4.set_yticks([])
    # plt.text(0.5, 1.08, r'$\bar{\theta} = %.2f,\, \bar{r} = %.2f$' % (mean_ang,
    #          mean_vec_len), horizontalalignment='center',
    #          transform=ax4.transAxes)
    ax4.plot(math.radians(mean_ang)*np.ones((10, 1)),
             np.linspace(0, np.nanmax(rate_in_ang), 10), 'r', lw=3)
    fig.tight_layout()
    if title is not None:
        fig.suptitle(title)
    return fig
