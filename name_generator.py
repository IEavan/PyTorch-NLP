# TODO: 
# Define model
# Write training loop
# Write evaluation and testing scripts


import glob
import unicodedata
import string
import random

import torch
from torch.autograd import Variable

# Constants
allowed_chars = string.ascii_letters + " .,;'"
n_chars = len(allowed_chars)
n_hidden = 128
training_iterations = 10000
print_every = 500

# Converts unicode strings into strings containing only ascii
# Characters. Accented letters will have their accents
# removed and other unicode characters will be removed
def unicode_to_ascii(s):
    return "".join(
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != "Mn"
            and c in allowed_chars
        )

# Returns a list of paths matching a given pattern
def find_files(path):
    return glob.glob(path)

# Opens a file of the given name and
# returns a list of the lines in ascii format
def read_lines(filename):
    with open(filename, encoding="UTF-8") as lines:
        names = lines.read().strip().split('\n')
        return [unicode_to_ascii(name) for name in names]

# Declare data containers
category_lines = {}
categories = []

# Load data into containers
for filename in find_files("name_data/names/*.txt"):
    category = filename.split('/')[-1].split('.')[0]
    categories.append(category)
    lines = read_lines(filename)
    category_lines[category] = lines

n_categories = len(categories)

# Helper methods for converting strings to onehot tensors
def letter_to_variable(letter):
    one_hot_tensor = torch.zeros(1, n_chars)
    index = allowed_chars.find(letter)
    one_hot_tensor[0][index] = 1
    return Variable(one_hot_tensor)

def name_to_variable(name):
    one_hot_tensor = torch.zeros(len(name), 1, n_chars)
    # Loop over and add ones at a corresponding index
    for i in range(len(name)):
        index = allowed_chars.find(name[i])
        one_hot_tensor[i][0][index] = 1
    return Variable(one_hot_tensor)

# Define Generative Model
class Generator(torch.nn.Module):
    def __init__(self, input_size, hidden_size, output_size, drop_probability=0.1):
        super(Generator, self).__init__()
        self.hidden_size = hidden_size

        # parameters
        self.c2i = torch.nn.Linear(input_size + hidden_size + n_catagories, output_size)
        self.c2h = torch.nn.Linear(input_size + hidden_size + n_categories, hidden_size)
        self.i2o = torch.nn.Linear(output_size + hidden_size, output_size)
        # Read c2i as combined value to intermediate value;
        #      c2h as combined value to hidden value
        #      i2o as intermediate value to output value

        # Define internal functions
        self.softmax = torch.nn.LogSoftmax()
        self.dropout = torch.nn.Dropout(drop_probability)

    def forward(self, category, prev_out, prev_hidden):
        # Function to combute a single iteration of the recurrent generator
        # Outputting negative log probabilities for a letter and the next hidden state
        combined = torch.cat((category, prev_out, prev_hidden), 1)
        intermediate = self.c2i(combined)
        hidden = self.c2h(combined)
        
        combined_intermediate = torch.cat((intermediate, hidden), 1)
        output = self.i2o(combined_intermediate)
        output = self.dropout(output)
        output = self.softmax(output)

        return output, hidden

    def init_hidden(self):
        # Function to generate a hidden value with the correct dimensions
        return Variable(torch.zeros(1, self.hidden_size))
