# =============================================================================
# This script is provided by Dr Simon Rogers
# =============================================================================

from __future__ import print_function

import sys
import os
#import getopt
import math
import bisect
import pymzml
import glob

from molnet.scoring_functions import fast_cosine, fast_cosine_shift


def sqrt_normalise(peaks):
    temp = []
    total = 0.0
    for mz,intensity in peaks:
        temp.append((mz,math.sqrt(intensity)))
        total += intensity
    norm_facc = math.sqrt(total)
    normalised_peaks = []
    for mz,intensity in temp:
        normalised_peaks.append((mz,intensity/norm_facc))
    return normalised_peaks

class Annotation(object):
    def __init__(self,data_dict):
        self.metadata = data_dict
    
    
    def get_score(self):
        if 'score' in self.metadata:
            return self.metadata['score']
        elif 'MQScore' in self.metadata:
            return self.metadata['MQScore']
        else:
            return None

    score = property(get_score)

    def __str__(self):
        return "{} {}".format(
            self.metadata.get('Compound_Name',None),
            self.metadata.get('SpectrumID',None))
        
# Class to hold a single spectrum and its metadata
class Spectrum(object):
    def __init__(self,peaks,file_name,scan_number,ms1,precursor_mz,parent_mz,rt = None,precursor_intensity = None,metadata = None):
        self.peaks = sorted(peaks,key = lambda x: x[0]) # ensure sorted by mz
        self.normalised_peaks = sqrt_normalise(self.peaks) # useful later
        self.n_peaks = len(self.peaks)
        self.max_ms2_intensity = max([intensity for mz,intensity in self.peaks])
        self.total_ms2_intensity = sum([intensity for mz,intensity in self.peaks])
        self.file_name = file_name
        self.scan_number = scan_number
        self.ms1 = ms1
        self.rt = rt
        self.precursor_mz = precursor_mz
        self.parent_mz = parent_mz
        self.precursor_intensity = precursor_intensity
        self.metadata = metadata

    def get_annotation(self):
        if not 'annotation' in self.metadata:
            return None
        else:
            anns = self.metadata['annotation']
            anns.sort(key = lambda x: x.score,reverse = True)
            return anns[0]



    annotation = property(get_annotation)


    def normalise_max_intensity(self,max_intensity = 1000.0):
        new_peaks = []
        for mz,intensity in self.peaks:
            new_peaks.append((mz,max_intensity*(intensity/self.max_ms2_intensity)))
        self.peaks = new_peaks
        self.n_peaks = len(self.peaks)
        if self.n_peaks > 0:
            self.normalised_peaks = sqrt_normalise(self.peaks)
            self.max_ms2_intensity = max([intensity for mz,intensity in self.peaks])
            self.total_ms2_intensity = sum([intensity for mz,intensity in self.peaks])
        else:
            self.normalised_peaks = []
            self.max_ms2_intensity = 0.0
            self.total_ms2_intensity = 0.0


    def randomise_intensities(self):
        from numpy.random import permutation
        intensities = [p[1] for p in self.peaks]
        permuted_intensities = permutation(intensities)
        new_peaks = []
        for i,(mz,intensity) in enumerate(self.peaks):
            new_peaks.append((mz,permuted_intensities[i]))
        self.peaks = new_peaks
        self.peaks.sort(key = lambda x: x[0])
        if self.n_peaks > 0:
            self.normalised_peaks = sqrt_normalise(self.peaks)
            self.max_ms2_intensity = max([intensity for mz,intensity in self.peaks])
            self.total_ms2_intensity = sum([intensity for mz,intensity in self.peaks])
        else:
            self.normalised_peaks = []
            self.max_ms2_intensity = 0.0
            self.total_ms2_intensity = 0.0        

    def flatten_peaks(self):
        max_intensity = max([p[1] for p in self.peaks])
        new_peaks = []
        for mz,intensity in self.peaks:
            new_peaks.append((mz,max_intensity))
        self.peaks = new_peaks
        if self.n_peaks > 0:
            self.normalised_peaks = sqrt_normalise(self.peaks)
            self.max_ms2_intensity = max([intensity for mz,intensity in self.peaks])
            self.total_ms2_intensity = sum([intensity for mz,intensity in self.peaks])
        else:
            self.normalised_peaks = []
            self.max_ms2_intensity = 0.0
            self.total_ms2_intensity = 0.0

    def remove_top_perc(self,perc):
        # remove the peaks corresponding to the top perc of intensity
        total_intensity = sum([p[1] for p in self.peaks])
        self.peaks.sort(key = lambda x: x[1])
        new_peaks = []
        total_found = 0.0
        for mz,intensity in self.peaks:
            total_found += intensity
            if total_found > (1-perc)*total_intensity:
                break
            else:
                new_peaks.append((mz,intensity))

        self.peaks = new_peaks
        self.peaks.sort(key = lambda x: x[0])

        if self.n_peaks > 0:
            self.normalised_peaks = sqrt_normalise(self.peaks)
            self.max_ms2_intensity = max([intensity for mz,intensity in self.peaks])
            self.total_ms2_intensity = sum([intensity for mz,intensity in self.peaks])
        else:
            self.normalised_peaks = []
            self.max_ms2_intensity = 0.0
            self.total_ms2_intensity = 0.0

    def remove_small_peaks(self,min_ms2_intensity = 10000):
        new_peaks = []
        for mz,intensity in self.peaks:
            if intensity >= min_ms2_intensity:
                new_peaks.append((mz,intensity))
        self.peaks = new_peaks
        self.n_peaks = len(self.peaks)
        if self.n_peaks > 0:
            self.normalised_peaks = sqrt_normalise(self.peaks)
            self.max_ms2_intensity = max([intensity for mz,intensity in self.peaks])
            self.total_ms2_intensity = sum([intensity for mz,intensity in self.peaks])
        else:
            self.normalised_peaks = []
            self.max_ms2_intensity = 0.0
            self.total_ms2_intensity = 0.0


    def remove_precursor_peak(self,tolerance = 17):
        new_peaks = []
        for mz,intensity in self.peaks:
            if abs(mz - self.precursor_mz) > tolerance:
                new_peaks.append((mz,intensity))
        self.peaks = new_peaks
        self.n_peaks = len(self.peaks)
        if self.n_peaks > 0:
            self.normalised_peaks = sqrt_normalise(self.peaks)
            self.max_ms2_intensity = max([intensity for mz,intensity in self.peaks])
            self.total_ms2_intensity = sum([intensity for mz,intensity in self.peaks])
        else:
            self.normalised_peaks = []
            self.max_ms2_intensity = 0.0
            self.total_ms2_intensity = 0.0
        

    def keep_top_k(self,k=6,mz_range=50):
        # only keep peaks that are in the top k in += mz_range
        start_pos = 0
        new_peaks = []
        for mz,intensity in self.peaks:
            while self.peaks[start_pos][0]< mz-mz_range:
                start_pos += 1
            end_pos = start_pos
            n_bigger = 0
            while end_pos < len(self.peaks) and self.peaks[end_pos][0] <= mz+mz_range:
                if self.peaks[end_pos][1] > intensity:
                    n_bigger += 1
                end_pos += 1
            if n_bigger < k:
                new_peaks.append((mz,intensity))

        self.peaks = new_peaks
        self.n_peaks = len(self.peaks)
        if self.n_peaks > 0:
            self.normalised_peaks = sqrt_normalise(self.peaks)
            self.max_ms2_intensity = max([intensity for mz,intensity in self.peaks])
            self.total_ms2_intensity = sum([intensity for mz,intensity in self.peaks])
        else:
            self.normalised_peaks = []
            self.max_ms2_intensity = 0.0
            self.total_ms2_intensity = 0.0
        

    def print_spectrum(self):
        print()
        print(self.file_name,self.scan_number)
        for i,(mz,intensity) in enumerate(self.peaks):
            print(i,mz,intensity,self.normalised_peaks[i][1])

    def plot(self,xlim = None,**kwargs):
        plot_spectrum(self.peaks,xlim=xlim,title = "{} {} (m/z= {})".format(self.file_name,self.scan_number,self.parent_mz),**kwargs)

    def __str__(self):
        return "Spectrum from scan {} in {} with {} peaks, max_ms2_intensity {}".format(self.scan_number,self.file_name,self.n_peaks,self.max_ms2_intensity)

    def __cmp__(self,other):
        if self.parent_mz >= other.parent_mz:
            return 1
        else:
            return -1

    def __lt__(self,other):
        if self.parent_mz <= other.parent_mz:
            return 1
        else:
            return 0

# Class to hold a cluster of spectra
class Cluster(object):
    def __init__(self,spectrum,cluster_id):
        self.spectra = [spectrum]
        self.n_spectra = 1
        self.set_prototype()
        self.cluster_id = cluster_id

    def get_annotation(self):
        return self.spectrum.annotation 
    
    annotation = property(get_annotation)

    def get_mgf_string(self):
        out_string = ""
        out_string += "BEGIN IONS\n"
        out_string += "FEATURE_ID={}\n".format(self.cluster_id)
        out_string += "PEPMASS={}\n".format(self.spectrum.precursor_mz)
        out_string += "SCANS={}\n".format(self.cluster_id)
        out_string += "RTINSECONDS={}\n".format(self.spectrum.rt)
        out_string += "CHARGE={}\n".format(self.spectrum.ms1.charge)
        out_string += "MSLEVEL=2\n"
        out_string += "FILENAME={}\n".format(self.spectrum.file_name)
        for p in self.spectrum.peaks:
            out_string += "{} {}\n".format(p[0],p[1])
        out_string += "END IONS\n\n"
        return out_string


    def get_file_intensity_dict(self):
        file_intensity = {}
        for spectrum in self.spectra:
            if spectrum.precursor_intensity:
                this_file = spectrum.file_name
                this_intensity = spectrum.precursor_intensity
                if not this_file in file_intensity:
                    file_intensity[this_file] = this_intensity
                else:
                    ma = max(this_intensity,file_intensity[this_file])
                    file_intensity[this_file] = ma
        return file_intensity
    def member_string(self):
        ms = ":".join(["{}_{}".format(s.file_name,s.scan_number) for s in self.spectra])
        return ms

    def get_members(self):
        members = []
        for spec in self.spectra:
            members.append((spec.file_name,spec.scan_number))
        return members

    def list_members(self):
        for spec in self.spectra:
            print("{}: {}".format(spec.file_name,spec.scan_number))

    def plot_spectrum(self,xlim = None,**kwargs):
        self.spectrum.plot(xlim = xlim,**kwargs)

    def get_frag_range(self,buff = 0):
        mz_min = 1e100
        mz_max = 0

        for spec in self.spectra:
            this_mz_min = min([m[0] for m in spec.peaks])
            this_mz_max = max([m[0] for m in spec.peaks])
            if this_mz_min < mz_min:
                mz_min = this_mz_min
            if this_mz_max > mz_max:
                mz_max = this_mz_max

        return [mz_min - buff,mz_max + buff]


    def plot(self,**kwargs):
        xlim = self.get_frag_range(buff = 50)
        for spec in self.spectra:
            spec.plot(xlim = xlim,**kwargs)

    def set_prototype(self):
        # This allows us to treat the Cluster as a spectrum and compute
        # similarities etc
        self.spectra.sort(key = lambda x: x.total_ms2_intensity,reverse = True)
        self.peaks = self.spectra[0].peaks # always keep the prototype at the start
        self.normalised_peaks = self.spectra[0].normalised_peaks
        self.n_peaks = self.spectra[0].n_peaks
        self.spectrum = self.spectra[0]
        self.precursor_mz = self.spectra[0].precursor_mz
        self.parent_mz = self.spectra[0].parent_mz


    def add_spectrum(self,spectrum):
        self.spectra.append(spectrum)
        self.n_spectra += 1
        self.set_prototype()

    def n_unique_files(self):
        files = [s.file_name for s in self.spectra]
        return len(set(files))

    def contains_file(self,list_of_files):
        my_files = set([s.file_name for s in self.spectra])
        if len(my_files.intersection(set(list_of_files))) > 0:
            return True
        return False

    def n_members_in_file(self,list_of_files):
        # returns a list of length(list_of_files) with the 
        # number of spectra it has from each of the files
        file_pos = {}
        for pos,file_name in enumerate(list_of_files):
            file_pos[file_name] = pos
        counts = [0 for file_name in list_of_files]
        for spec in self.spectra:
            counts[file_pos[spec.file_name]] += 1
        return counts

    
    def n_metadata_in_cluster(self,list_of_metadata_items,filename_to_metadata):
        metadata_pos = {}
        for pos,metadata_item in enumerate(list_of_metadata_items):
            metadata_pos[metadata_item] = pos
        counts = [0 for i in list_of_metadata_items]
        for spec in self.spectra:
            if spec.file_name in filename_to_metadata:
                this_metadata = filename_to_metadata[spec.file_name]
                counts[metadata_pos[this_metadata]] += 1
        n_non_zero = 0
        for c in counts:
            if c > 0:
                n_non_zero += 1
        return counts,n_non_zero


    def __str__(self):
        return "Cluster ({}), mz: {}, ({})".format(
            self.n_spectra,
            str(self.spectrum.parent_mz),
            self.spectrum.annotation)

    def __cmp__(self,other):
        if self.parent_mz > other.parent_mz:
            return 1
        else:
            return -1

class MolecularFamily(object):
    # A class to hold a molecular family object
    def __init__(self,graph_object,family_id):
        self.clusters = list(graph_object.edge_dict.keys())
        self.n_clusters = len(self.clusters)
        self.scores = self.convert_graph_to_scores(graph_object)
        self.family_id = family_id

    def report(self,similarity_function,similarity_tolerance,**kwargs):
        print
        print("Molecular family object containing {} clusters".format(len(self.clusters)))
        for n1,n2,weight in self.scores:
            print("{} <- {} -> {}".format(n1,weight,n2))
            if len(self.clusters) < 10:
                plot_spectral_alignment(n1,n2,similarity_function,similarity_tolerance,**kwargs)
            else:
                print("Not plotting as too many clusters, use plot_spectral_alignment to plot individual pairs")

    def convert_graph_to_scores(self,graph_object):
        done = set()
        scores = []
        for node,edges in graph_object.edge_dict.items():
            for node2,weight in edges:
                if not (node,node2) in done:
                    scores.append((node,node2,weight))
                    done.add((node2,node))
        return scores
    def n_members_in_file(self,list_of_files):
        counts = [0 for i in list_of_files]
        for cluster in self.clusters:
            temp = cluster.n_members_in_file(list_of_files)
            counts = [c+temp[i] for i,c in enumerate(counts)]
        return counts

    def plot(self,xlim=None,**kwargs):
        # Plots the prototype spectrum from each cluster
        if not xlim:
            mz_min = 1e100
            mz_max = 0
            for cluster in self.clusters:
                temp = cluster.get_frag_range(buff = 50)
                mz_min = min([mz_min,temp[0]])
                mz_max = max([mz_max,temp[1]])

            xlim = [mz_min,mz_max]

        for cluster in self.clusters:
            cluster.plot_spectrum(xlim = xlim,**kwargs)

def write_mnet_files(molecular_families,file_name,parameters,metadata = None,pickle = True,write_mgf = True,extra_node_data = None):
    import csv,jsonpickle
    # write a csv file from a list of molecular molecular_families
    csv_name = file_name + '_nodes.csv'
    edge_file = file_name + '_edges.csv'
    mgf_file = file_name + '.mgf'
    # First need to find all the unique files
    unique_files = []
    for family in molecular_families:
        for cluster in family.clusters:
            for spectrum in cluster.spectra:
                unique_files.append(spectrum.file_name)
    unique_files = sorted(list(set(unique_files)))
    heads = ['cid','familyid','precursor_mz','parent_mz','short_precursor_mz','short_parent_mz','charge','members','n_unique_files'] + unique_files
    if metadata:
        for mlist,mdict,mtitle in metadata:
            heads += mlist + [mtitle]
    if extra_node_data:
        for extra in extra_node_data:
            heads += extra[0]
    print("Writing csv")
    with open(csv_name,'w') as f:
        writer = csv.writer(f)
        writer.writerow(heads)
        for family in molecular_families:
            for cluster in family.clusters:
                newrow = [cluster.cluster_id,family.family_id,cluster.precursor_mz,cluster.parent_mz]
                newrow += ["{:.2f}".format(cluster.precursor_mz),"{:.2f}".format(cluster.parent_mz)]
                newrow += [cluster.spectrum.ms1.charge]
                newrow += [cluster.member_string()]
                newrow += [cluster.n_unique_files()]
                newrow += cluster.n_members_in_file(unique_files)
                if metadata:
                    for mlist,mdict,mtitle in metadata:
                        counts,nnz = cluster.n_metadata_in_cluster(mlist,mdict)
                        newrow += counts + [nnz]
                if extra_node_data:
                    for extra in extra_node_data:
                        newrow += extra[1][cluster.cluster_id]
                writer.writerow(newrow)
    print("Writing edges")
    with open(edge_file,'w') as f:
        writer = csv.writer(f)
        writer.writerow(["source","target","weight"])
        for family in molecular_families:
            scores = family.scores
            if len(scores) > 0:
                for node1,node2,weight in scores:
                    writer.writerow([node1.cluster_id,node2.cluster_id,weight])
            else:
                # Singleteon family -- write the self loop
                assert len(family.clusters) == 1
                cluster = family.clusters[0]
                writer.writerow([cluster.cluster_id,cluster.cluster_id,'self'])

    # finally, write the mgf-style file
    if write_mgf:
        print("Writing mgf")
        with open(mgf_file,'w') as f:
            for family in molecular_families:
                for cluster in family.clusters:
                    f.write("BEGIN IONS\n")
                    f.write("FILENAME={}\n".format(cluster.spectrum.file_name))
                    f.write("SCANNO={}\n".format(cluster.spectrum.scan_number))
                    f.write("CID={}\n".format(cluster.cluster_id))
                    f.write("FAMILYID={}\n".format(family.family_id))
                    f.write("PEPMASS={}\n".format(cluster.spectrum.precursor_mz))
                    f.write("RTINSECONDS={}\n".format(cluster.spectrum.rt))
                    f.write("CHARGE={}\n".format(cluster.spectrum.ms1.charge))
                    f.write("NAME={}\n".format(cluster.cluster_id))
                    for mz,intensity in cluster.spectrum.peaks:
                        f.write("{} {}\n".format(mz,intensity))
                    f.write("END IONS\n\n")

    if pickle:
        print("Writing pickle")
        # write the pickle of everything
        pickle_file = file_name + '.pickle'
        with open(pickle_file,'w') as f:
            f.write(jsonpickle.dumps(molecular_families))

    pickle_parameter_file = file_name + '_parameters.pickle'
    with open(pickle_parameter_file,'w') as f:
        f.write(jsonpickle.dumps(parameters))
    parameter_file = file_name + '_parameters.csv'
    with open(parameter_file,'w') as f:
        writer = csv.writer(f)
        for key,value in parameters.items():
            writer.writerow([key,value])



def merge(cluster_list,spectrum,similarity_function,similarity_tolerance,min_match,score_threshold = 0.95,rt_tolerance = 1000000,ms1_tolerance=0.02,initial_cluster_id = 0):
    # Compute the siilarity between the spectrum and all clusters in the list
    # if a cluster is found with score >= threshold
    # add the spectrum to the cluster and return
    # If none is found, create a new singleton cluster and append to the list

    next_id = initial_cluster_id


    # Slow version
    possible_idx = []
    for i,cluster in enumerate(cluster_list):
        if abs(spectrum.parent_mz - cluster.spectrum.parent_mz) <= ms1_tolerance:
            possible_idx.append(i)

    # fast version
    # spectrum.precursor_mz -= ms1_tolerance
    # min_pos = bisect.bisect_left(cluster_list,spectrum)
    # spectrum.precursor_mz += ms1_tolerance
    # spectrum.precursor_mz += ms1_tolerance
    # max_pos = bisect.bisect_right(cluster_list,spectrum)
    # spectrum.precursor_mz -= ms1_tolerance
    # possible_idx = range(min_pos,max_pos)
    
    for idx in possible_idx:
        cluster = cluster_list[idx]
        if abs(cluster.spectrum.rt - spectrum.rt) < rt_tolerance: 
            score,match_list = similarity_function(cluster,spectrum,similarity_tolerance,min_match)
            if score >= score_threshold:
                cluster.add_spectrum(spectrum)
                # re-sort
                # cluster_list.sort()
                cluster_list[possible_idx[0]:possible_idx[-1]+1] = sorted(cluster_list[possible_idx[0]:possible_idx[-1]+1])
                # for i,c in enumerate(cluster_list[:-1]):
                #     if not cluster_list[i+1] >= cluster_list[i]:
                #         print possible_idx,i
                return next_id
    # if we get to here, nothing was found
    # insertion_point = bisect.bisect_left(cluster_mz_list,spectrum.precursor_mz)
    bisect.insort(cluster_list,Cluster(spectrum,next_id))
    # cluster_list.append(Cluster(spectrum,next_id))
    # cluster_list.sort(key = lambda x: x.spectrum.precursor_mz)
    next_id += 1
    return next_id

   
def make_initial_network(cluster_list,similarity_function,similarity_tolerance,min_match,score_threshold,k=10,mc=1,max_shift = 100):

    # Do the MC filtering
    filtered_cluster_list = list(filter(lambda x: len(x.spectra)>=mc,cluster_list))


    edges = []
    edge_dict = {}
    G = Graph()
    for cluster in filtered_cluster_list:
        G.add_node(cluster)
    for i,cluster in enumerate(filtered_cluster_list[:-1]):
        if i%200 == 0 and i > 0:
            print("Done {} of {}".format(i,len(filtered_cluster_list)))
        for cluster2 in filtered_cluster_list[i+1:]:
            if abs(cluster.parent_mz - cluster2.parent_mz) < max_shift:
                score,_ = similarity_function(cluster,cluster2,similarity_tolerance,min_match)
                if score >= score_threshold:
                    G.add_edge(cluster,cluster2,score)

    filtered_graph = G.topk_filter(k = k)

    return filtered_graph

class Graph(object):
    def __init__(self,edge_dict = {}):
        if not edge_dict:
            self.edge_dict = {}
        else:
            self.edge_dict = edge_dict

    def add_node(self,node):
        if not node in self.edge_dict:
            self.edge_dict[node] = set()

    def add_edge(self,node1,node2,weight):
        if not node1 in self.edge_dict:
            self.edge_dict[node1] = set()
        if not node2 in self.edge_dict:
            self.edge_dict[node2] = set()
        self.edge_dict[node1].add((node2,weight))
        self.edge_dict[node2].add((node1,weight))
        
    def topk_filter(self,k=10):
        sorted_edge_dict = {}
        for node,edges in self.edge_dict.items():
            sorted_edge_dict[node] = sorted(edges,key = lambda x: x[1], reverse = True)
        done = set()
        filtered_edges = {}
        for node,edges in sorted_edge_dict.items():
            filtered_edges[node] = []
            j = 0
            for node2,weight in edges:
                other_pos = sorted_edge_dict[node2].index((node,weight))
                if other_pos < k:
                    if not node in filtered_edges:
                        filtered_edges[node] = []
                    filtered_edges[node].append((node2,weight))
                j += 1
                if j == k:
                    break
        # check for symmetry
        for node,edges in filtered_edges.items():
            for node2,weight in edges:
                if not (node,weight) in filtered_edges[node2]:
                    print("GAH!")
        return Graph(edge_dict = filtered_edges)

    def connected_components(self):
        visited = []
        to_visit = set(self.edge_dict.keys())
        while len(to_visit) > 0:
            current = to_visit.pop()
            component = self.find_reachable(current)
            to_visit -= component
            visited.append(component)

        # make the new graph components
        new_graphs = []
        for v in visited:
            new_edges = {}
            for node in v:
                new_edges[node] = self.edge_dict[node]
            new_graphs.append(Graph(edge_dict = new_edges))
        return new_graphs

    def n_connected_components(self):
        return len(self.connected_components())


    def find_reachable(self,node):
        visited = set()
        visited.add(node)
        to_visit = set([n for n,w in self.edge_dict[node]]) - visited
        while len(to_visit) > 0:
            current = to_visit.pop()
            visited.add(current)
            new_nodes = set([n for n,w in self.edge_dict[current]])
            new_nodes -= visited
            to_visit = to_visit.union(new_nodes)
        return visited

    def remove_weakest_edge(self):
        min_edges = 100.0
        min_n1 = None
        min_edge = None
        for node,edges in self.edge_dict.items():
            for pos,(node2,w) in enumerate(edges): 
                if w < min_edges:
                    min_n1 = node
                    min_pos = pos

        min_n2, min_w = self.edge_dict[min_n1][min_pos]
        del self.edge_dict[min_n1][min_pos]
        pos2 = self.edge_dict[min_n2].index((min_n1,min_w))
        del self.edge_dict[min_n2][pos2]
        



def mol_network(cluster_list,similarity_function,similarity_tolerance,min_match,score_threshold,k=10,beta=100,mc=1,max_shift = 100):
    print()
    print("Computing pairwise similarities (might take some time)")
    G = make_initial_network(cluster_list,similarity_function,similarity_tolerance,min_match,score_threshold,k=k,mc=mc,max_shift = max_shift)


    # print "Created initial network, {} nodes and {} edges".format(len(G),len(G.edges()))
    print("Originally {} components".format(G.n_connected_components()))
    
    molecular_families = G.connected_components()

    finished = False

    final_families = []
    too_big = []
    for family in molecular_families:
        if len(family.edge_dict) <= beta:
            final_families.append(family)
        else:
            too_big.append(family)

    print("{} components are too big".format(len(too_big)))
    while not finished:
        new_too_big = []
        for m in too_big:
            # print "Found component of size = {}".format(len(m))
            while m.n_connected_components() == 1:
                m.remove_weakest_edge()
            # return the two components
            for c in m.connected_components():
                if len(c.edge_dict) <= beta:
                    final_families.append(c)
                else:
                    new_too_big.append(c)

        too_big = new_too_big
        if len(too_big)>0:
            print("{} components are too big, biggest = {}".format(len(too_big),max([len(m.edge_dict) for m in too_big])))

        if len(too_big) == 0:
            finished = True


    print("After pruning, {} components are left".format(len(final_families)))
    return final_families,[MolecularFamily(m,family_id) for family_id,m in enumerate(final_families)]

def remove_clusters(cluster_list,files):
    # removes from the cluster_list any clusters that include spectra from the files
    # listed in files (e.g. blanks)
    filtered_cluster_list = []
    print("Removing clusters that appear in: {}".format(", ".join(files)))
    for cluster in cluster_list:
        if not cluster.contains_file(files):
            filtered_cluster_list.append(cluster)
    print("Prefiltering = {}, postfiltering = {}".format(len(cluster_list),len(filtered_cluster_list)))
    return filtered_cluster_list

def get_spectrum_from_file(input_file,scan_number):
    run = pymzml.run.Reader(input_file,obo_version='4.0.1')
    spec_no = 0
    peaks = []
    for spectrum in run:
        if spec_no == scan_number:
            if not spectrum['ms level'] == 2:
                print("Warning: the chosen scan is not MS2!")
            for mz,intensity in spectrum.centroidedPeaks:
                peaks.append((mz,intensity))
        spec_no += 1
    return peaks

def plot_spectrum(peaks,xlim = None,title = None,**kwargs):
    import pylab as plt
    plt.figure(**kwargs)
    for mz,intensity in peaks:
        plt.plot([mz,mz],[0,intensity],'k')
    if xlim:
        plt.xlim(xlim)
    if title:
        plt.title(title)


def plot_spectrum_pair(peaks1,peaks2,**kwargs):
    import pylab as plt
    plt.figure(**kwargs)
    for mz,intensity in peaks1:
        plt.plot([mz,mz],[0,intensity],'r')
    for mz,intensity in peaks2:
        plt.plot([mz,mz],[0,-intensity],'b')

def plot_cluster_by_id(cluster_list,cluster_id,**kwargs):
    cluster = get_cluster_by_id(cluster_list,cluster_id)
    if cluster:
        cluster.plot(**kwargs)

def get_cluster_by_id(cluster_list,cluster_id):
    for cluster in cluster_list:
        if cluster.cluster_id == cluster_id:
            return cluster
    return None    

def plot_family_by_id(family_list,family_id,xlim = None,**kwargs):
    family = get_family_by_id(family_list,family_id)
    if family:
        family.plot(xlim = xlim,**kwargs)            

def get_family_by_id(family_list,family_id):
    for family in family_list:
        if family.family_id == family_id:
            return family

    return None    

def plot_spectral_alignment(spectrum1,spectrum2,similarity_function,similarity_tolerance,scale = True,**kwargs):
    import pylab as plt
    score,matches = similarity_function(spectrum1,spectrum2,similarity_tolerance,0) # set min_match to zero
    cols = ['r','b','g','k','m','c']
    plt.figure(**kwargs)
    if scale:
        maxi1 = max([intensity for mz,intensity in spectrum1.peaks])
        maxi2 = max([intensity for mz,intensity in spectrum2.peaks])
    else:
        maxi1 = 1.0
        maxi2 = 1.0
        
    for mz,intensity in spectrum1.peaks:
        plt.plot([mz,mz],[0,intensity/maxi1],'k',color=[0.3, 0.3, 0.3])
    for mz,intensity in spectrum2.peaks:
        plt.plot([mz,mz],[0,-intensity/maxi2],'k',color=[0.3, 0.3, 0.3])
    plt.plot(plt.xlim(),[0,0],'k--',color =[0.6,0.6,0.6])
    colpos = 0
    for pos1,pos2,_ in matches:
        plt.plot([spectrum1.peaks[pos1][0],spectrum1.peaks[pos1][0]],[0,spectrum1.peaks[pos1][1]/maxi1],cols[colpos])
        plt.plot([spectrum2.peaks[pos2][0],spectrum2.peaks[pos2][0]],[0,-spectrum2.peaks[pos2][1]/maxi2],cols[colpos])
        if abs(spectrum1.peaks[pos1][0] - spectrum2.peaks[pos2][0]) >= similarity_tolerance:
            plt.plot([spectrum1.peaks[pos1][0],spectrum2.peaks[pos2][0]],[spectrum1.peaks[pos1][1]/maxi1,-spectrum2.peaks[pos2][1]/maxi2],'k--',color = [0.6,0.6,0.6])
        colpos += 1
        if colpos == len(cols):
            colpos = 0
    plt.title("{:.2f} <-> {:.2f}, Score = {}".format(spectrum1.parent_mz,spectrum2.parent_mz,score))

def get_family_from_cluster(family_graph_list,cluster):
    for family in family_graph_list:
        if cluster in family.nodes():
            return family
    return None

def test_family(family,similarity_function,similarity_tolerance,score_threshold):
    # for debugging: check to make sure there are no edges below the threshold
    for cluster in family.clusters:
        max_score = 0.0
        j = 0
        max_pos = -1
        for cluster2 in family.clusters:
            if not (cluster == cluster2):
                s,_ = similarity_function(cluster,cluster2,similarity_tolerance,3)
                if s >= max_score:
                    max_score = s
                    max_pos = j
            j+=1
        if max_score < score_threshold:
            print("PROBLEM: {} < {}".format(max_score,score_threshold))
            print(family.clusters.index(cluster),max_pos)
            return False
    return True









class SpectralLibrary(object):
    def __init__(self,filename,loader,loading_parameters):
        self.filename = filename
        self.loader = loader
        self.loading_parameters = loading_parameters
        self.load_spectra()
        print("Loaded {} spectra".format(len(self.spectra)))
        print("Filtering...")
        self.normalise_max_intensity()
        self.filter()
        print("Finished filtering -- now have {} spectra".format(len(self.spectra)))

    def remove_small_peaks(self,min_ms2_intensity = 5.0):
        for s in self.spectra:
            s.remove_small_peaks(min_ms2_intensity = min_ms2_intensity)

    def normalise_max_intensity(self,max_intensity = 1000.0):
        for s in self.spectra:
            s.normalise_max_intensity(max_intensity = max_intensity)

    def load_spectra(self):
        ms1,ms2,metadata = self.loader.load_spectra(self.filename)
        temp_spectra = {}
        for m in ms2:
            tempms1 = m[3]
            ms1_name = tempms1.name
            spec_name = ms1_name

            if not spec_name in temp_spectra:
                temp_spectra[spec_name] = {}
                temp_spectra[spec_name]['peaks'] = []
                temp_spectra[spec_name]['scan_number'] = m[-1]
                temp_spectra[spec_name]['file_name'] = self.filename
                temp_spectra[spec_name]['ms1'] = m[3]
                temp_spectra[spec_name]['rt'] = m[1]
                temp_spectra[spec_name]['precursor_mz'] = m[3].mz
            temp_spectra[spec_name]['peaks'].append((m[0],m[2]))

        self.spectra = []
        for s in temp_spectra:
            sp = temp_spectra[s]
            if len(sp['peaks']) > 0:
                self.spectra.append(Spectrum(sp['peaks'],sp['file_name'],sp['scan_number'],
                                sp['ms1'],sp['precursor_mz'],sp['rt']))
                self.spectra[-1].spectrumid = metadata[s]['spectrumid']
                self.spectra[-1].name = metadata[s]['name']

    def filter(self):
        for s in self.spectra:
            s.remove_small_peaks(min_ms2_intensity = self.loading_parameters['min_ms2_intensity'])
            s.remove_precursor_peak(tolerance = self.loading_parameters['precursor_tolerance'])
            s.keep_top_k(k = self.loading_parameters['k'],mz_range = self.loading_parameters['mz_range'])

        self.spectra = filter(lambda x: x.n_peaks >= self.loading_parameters['N'],self.spectra)

    def score_spectrum(self,spectrum,similarity_function,similarity_tolerance,min_match_peaks,score_threshold):
        import bisect
        self.spectra.sort()
        matches = []
        # find candidates
        spectrum.precursor_mz -= similarity_tolerance
        left_pos = bisect.bisect_left(self.spectra,spectrum)
        spectrum.precursor_mz += 2*similarity_tolerance
        right_pos = bisect.bisect_right(self.spectra,spectrum)
        spectrum.precursor_mz -= similarity_tolerance
        
        potential_candidates = range(left_pos,right_pos)
        for p in potential_candidates:
            s = self.spectra[p]
            if abs(s.precursor_mz - spectrum.precursor_mz) < similarity_tolerance:
                sc,m = similarity_function(s,spectrum,similarity_tolerance,min_match_peaks)
                if sc >= score_threshold:
                    matches.append((s,sc))
        return matches


