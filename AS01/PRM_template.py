PRM_template="""
traces = dict(
    raw_data_files=[experiment_name + '.dat'],
    voltage_gain=10.,
    sample_rate=20000,
    n_channels=Nch,
    dtype='int16',
)

spikedetekt = dict(
    filter_low=500.,  # Low pass frequency (Hz)
    filter_high_factor=0.95 * .5,
    filter_butter_order=3,  # Order of Butterworth filter.

    filter_lfp_low=0,  # LFP filter low-pass frequency
    filter_lfp_high=300,  # LFP filter high-pass frequency

    chunk_size_seconds=1,
    chunk_overlap_seconds=.015,

    n_excerpts=50,
    excerpt_size_seconds=1,
    threshold_strong_std_factor=4.5,
    threshold_weak_std_factor=2.,
    detect_spikes='negative',

    connected_component_join_size=1,

    extract_s_before=16,
    extract_s_after=16,

    n_features_per_channel=3,  # Number of features per channel.
    pca_n_waveforms_max=10000,
)

klustakwik2 = dict(
    num_starting_clusters=100,
)

"""