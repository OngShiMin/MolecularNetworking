import requests
import json
import jsonpickle
import pandas as pd
import sys
import math
import numpy as np

from molnet.mnet import Spectrum, Cluster, mol_network
from molnet.scoring_functions import  fast_cosine_shift
from molnet.bokeh_nx import mn_display
from molnet.spec_lib import SpecLib

# =============================================================================
#  api to extract data from FrAnK (created by Dr Joe Wandy)
# =============================================================================
def get_authentication_token(host, username, password):
    url = 'http://{}/export/get_token'.format(host)
    r = requests.post(url, data={'username': username, 'password': password})
    token = json.loads(r.text)['token']
    return(token)
    
    
def get_data(token, url, as_dataframe=False):
    headers = {'Authorization': 'token {}'.format(token)}
    payload = None    
    
    with requests.Session() as s:
        s.headers.update(headers)
        r = s.get(url)
        print(url, r)

        # extract GET results
        if r.status_code == 200:
            payload = json.loads(r.text)    
            if as_dataframe:
                try:
                    df = pd.read_json(payload)
                except: # alternative way to load the response
                    df = pd.read_json(r.text)
                payload = df.sort_index()
                
    return payload

    
host = 'polyomics.mvls.gla.ac.uk'
token = 'e77570ee7f5665c604449ffb4ceba52b06c8603a'

#analysis_id = 1321 # example beer analysis

def get_ms2_peaks(token, host, analysis_id, as_dataframe=False):
    url = 'http://{}/export/get_ms2_peaks?analysis_id={}&as_dataframe={}'.format(host, analysis_id, as_dataframe)
    payload = get_data(token, url, as_dataframe)
    return payload




# =============================================================================
# load spectras >> load cluster >> dataframe
# =============================================================================
def load_spectra(analysis_id):
    
    ms2_peaks = get_ms2_peaks(token, host, analysis_id)
    
    spectrum_dict = ms2_peaks['spectra']
    spectrum_list = []
    
    for s in spectrum_dict:
        spectrum_id = s[0]
        precursor_mz = s[1]
        ms2 = s[2]
        
        spectrum_list.append(Spectrum(peaks=ms2, file_name=analysis_id, scan_number=spectrum_id, ms1='', precursor_mz=precursor_mz, parent_mz=precursor_mz))
    
    return spectrum_list


def load_clusters(spectrum_list, similarity_tolerance, min_match, score_threshold, k=10, mc=1, max_shift=100):
    
    cluster_list = []
    
    for i, s in enumerate(spectrum_list):
        cluster = Cluster(s, i)
        cluster_list.append(cluster)
        
    
    f, mol_fam = mol_network(cluster_list, fast_cosine_shift, similarity_tolerance, min_match, score_threshold, k=10, beta=100, mc=1, max_shift = 100)
    
    
    return cluster_list, mol_fam



def edges_dataframe(mol_fam):
    edges = []
    
    for f in mol_fam:
        for c1, c2, score in f.scores:
            edges.append({'cluster1': c1.cluster_id,
                              'cluster2': c2.cluster_id,
                              'similarity_score': score})
    
    
    edges_df = pd.DataFrame(edges)
    
    return edges_df


# =============================================================================
# spectra libraries
# =============================================================================
def load_spectra_lib():
#    sys.path.append("C:/Users/Shimin/Documents/UoG/MSc Dissertation/mnet/Workspace/molnet_project/molnet")
    sys.path.append("./molnet")
    with open("molnet/matched_mibig_gnps.p", 'r') as f:
        lib = jsonpickle.decode(f.read())

    return lib


def spec_hits(cluster_list, edges_df):
    spec_lib = load_spectra_lib()
    hit_list_id = []
    hit_list = []
    
    for c in cluster_list:
        hit_id = spec_lib.spectral_match(query=c.spectrum)
        if hit_id != []:
            hit_list_id.extend([i[0] for i in hit_id])
            
    for i in hit_list_id:
        matched_spec = spec_lib.spectra[i]
        matched_cl = Cluster(matched_spec, i)
        hit_list.append(matched_cl)
        
           
           
    
    print("{} library matches".format(len(hit_list)))
    
    return hit_list



# =============================================================================
# link to view
# =============================================================================
def view(analysis_id, similarity_tolerance, min_match, score_threshold, k, mc, max_shift):
    spectrum_list = load_spectra(analysis_id)
    
    cluster_list, mol_fam = load_clusters(spectrum_list, similarity_tolerance, min_match, score_threshold, k, mc, max_shift)
    
    
    
    edges_df = edges_dataframe(mol_fam)
    hit_list = spec_hits(cluster_list, edges_df)
    
    m_networks = mn_display(edges_df, analysis_id)
    
    
    return m_networks, cluster_list, hit_list


