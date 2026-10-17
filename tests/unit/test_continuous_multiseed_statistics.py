import math

import numpy as np
import pytest

from heterodiff.evaluation.continuous_multiseed_statistics import (
    _width, paired_contrast, paired_error_summary, route_report, seed_summary,
)


def vector(empty=.2, other=.3):
    mass=1.-empty-other
    return [empty,other,mass]+np.linspace(0.,mass,21).tolist()


def test_predeclared_widths_and_maximum_discrepancies():
    p,q=vector(.25,.25),vector()
    r=route_report(p,q,512)
    assert r['maximum_indicator_error']==pytest.approx(.05)
    assert r['maximum_category_error']==pytest.approx(.05)
    assert r['maximum_joint_cdf_grid_error']==0.
    assert r['sampling_half_width']==pytest.approx(.1094221364,abs=1e-10)
    assert route_report(p,q,2048)['sampling_half_width']==pytest.approx(.0547110682,abs=1e-10)
    assert r['finite_indicator_error_interval'][0]==0.


def test_mixture_error_is_not_average_seed_error():
    q=vector()
    rows=[vector(.3,.2),vector(.1,.4),q]
    s=seed_summary(rows,q,512)
    assert s['mixture_maximum_indicator_error']==pytest.approx(0.,abs=1e-16)
    assert s['mixture_maximum_category_error']==pytest.approx(0.,abs=1e-16)
    assert s['mixture_maximum_joint_cdf_grid_error']==pytest.approx(0.,abs=1e-16)
    assert s['seed_error_mean_descriptive']==pytest.approx(1/15)
    assert s['seed_error_sd_descriptive']>0
    assert not s['training_seed_population_confidence_claimed']
    assert s['mixture_sampling_half_width']==pytest.approx(.0605125673,abs=1e-10)


def test_signed_contrast_uses_range_two():
    left,right=[vector(.3,.2)]*3,[vector()]*3
    c=paired_contrast(left,right,512)
    assert c['signed_indicator_difference_left_minus_right'][:3]==pytest.approx([.1,-.1,0])
    assert c['sampling_half_width']==pytest.approx(.1172371436,abs=1e-10)
    assert c['sampling_half_width']==2*_width(1536,2,.0025)
    assert not c['common_random_numbers_claimed']


def test_paired_error_contrast_keeps_per_seed_and_mean_estimands():
    q=vector()
    p=paired_error_summary([vector(.3,.2),vector(.1,.4),q],[q]*3,q,512)
    assert p['per_seed_error_difference_left_minus_right']==pytest.approx([.1,.1,0])
    assert p['mean_error_difference_left_minus_right']==pytest.approx(1/15)
    assert p['sampling_half_width']==2*route_report(q,q,512)['sampling_half_width']
    assert p['mean_error_difference_interval'][0]<0<p['mean_error_difference_interval'][1]


@pytest.mark.parametrize('bad',[[],[.5]*24,[float('nan')]*24,[float('inf')]*24,[-1.]*24,[2.]*24])
def test_invalid_indicator_vectors_rejected(bad):
    with pytest.raises(ValueError):
        route_report(bad,vector(),512)


def test_nonmonotone_or_nonjoint_cdf_rejected():
    for i,value in ((4,-.1),(3,.8),(23,.8)):
        p=vector();p[i]=value
        with pytest.raises(ValueError):
            route_report(p,vector(),512)


@pytest.mark.parametrize('n',[0,-1,1.,True])
def test_invalid_draw_counts_rejected(n):
    with pytest.raises(ValueError):
        route_report(vector(),vector(),n)


@pytest.mark.parametrize('function',[paired_contrast,paired_error_summary])
def test_incomplete_seed_rosters_rejected(function):
    args=([vector()],[],512) if function is paired_contrast else ([vector()],[],vector(),512)
    with pytest.raises(ValueError):
        function(*args)
    with pytest.raises(ValueError):
        seed_summary([],vector(),512)


def test_one_seed_reports_no_sample_sd_and_intervals_are_clamped():
    r=seed_summary([vector()],vector(.7,.3),1)
    assert r['seed_error_sd_descriptive'] is None
    assert r['mixture_error_interval']==[0.,1.]
    p=paired_contrast([vector()],[vector(.7,.3)],1)
    assert all(a==-1. and b==1. for a,b in p['signed_indicator_intervals'])
    assert math.isfinite(p['sampling_half_width'])
