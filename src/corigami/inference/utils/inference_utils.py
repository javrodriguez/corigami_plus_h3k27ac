import os
import numpy as np
import pandas as pd
import sys
import torch

from corigami.inference.utils.model_utils import load_default

def preprocess_default(seq, ctcf, atac, h3k27ac):
    # Process sequence
    seq = torch.tensor(seq).unsqueeze(0) 
    # Normailze ctcf and atac-seq
    ctcf = torch.tensor(np.nan_to_num(ctcf, 0)) # Important! replace nan with 0
    atac_log = torch.tensor(atac) # Important! replace nan with 0
    h3k27ac_log = torch.tensor(h3k27ac) # Important! replace nan with 0
    # Merge inputs
    features = [ctcf, atac_log, h3k27ac_log]
    features = torch.cat([feat.unsqueeze(0).unsqueeze(2) for feat in features], dim = 2)
    inputs = torch.cat([seq, features], dim = 2)
    # Move input to gpu if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    inputs = inputs.to(device)
    return inputs

## Load data ##
def load_region(chr_name, start, seq_path, ctcf_path, atac_path, h3k27ac_path, window = 2097152):
    ''' Single loading method for one region '''
    end = start + window
    seq, ctcf, atac, h3k27ac = load_data_default(chr_name, seq_path, ctcf_path, atac_path, h3k27ac_path)
    seq_region, ctcf_region, atac_region, h3k27ac_region = get_data_at_interval(chr_name, start, end, seq, ctcf, atac, h3k27ac)
    return seq_region, ctcf_region, atac_region, h3k27ac_region


def load_data_default(chr_name, seq_path, ctcf_path, atac_path, h3k27ac_path):
    from corigami.data.data_feature import SequenceFeature, GenomicFeature
    seq_chr_path = os.path.join(seq_path.strip('='), f'{chr_name}.fa.gz')
    seq = SequenceFeature(path = seq_chr_path)
    ctcf = GenomicFeature(path = ctcf_path.strip('='), norm = None)
    atac = GenomicFeature(path = atac_path.strip('='), norm = 'log')
    h3k27ac = GenomicFeature(path = h3k27ac_path.strip('='), norm = 'log')
    return seq, ctcf, atac, h3k27ac

def get_data_at_interval(chr_name, start, end, seq, ctcf, atac, h3k27ac):
    '''
    Slice data from arrays with transformations
    '''
    seq_region = seq.get(start, end)
    ctcf_region = ctcf.get(chr_name, start, end)
    atac_region = atac.get(chr_name, start, end)
    h3k27ac_region = h3k27ac.get(chr_name, start, end)
    return seq_region, ctcf_region, atac_region, h3k27ac_region

## Load Model ##
def prediction(seq_region, ctcf_region, atac_region, h3k27ac_region, model_path):
    model = load_default(model_path)
    inputs = preprocess_default(seq_region, ctcf_region, atac_region, h3k27ac_region)
    pred = model(inputs)[0].detach().cpu().numpy()
    return pred
